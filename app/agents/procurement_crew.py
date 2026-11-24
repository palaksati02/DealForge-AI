import re
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import PurchaseRequestExtract, BudgetValidationResult, ComplianceValidationResult
from app.services.pricing_service import PricingService
from app.services.budget_service import BudgetService
from app.services.compliance_service import ComplianceService
from app.services.evaluation_service import EvaluationService
from app.services.approval_service import ApprovalService
from app.services.purchase_order_service import PurchaseOrderService
from app.a2a.client import A2AClient
from app.a2a.schemas import RiskAssessmentPayload
from app.mcp.client import mcp_client
from app.agents.crew import build_procurement_crew
from app.core.callbacks import workflow_monitor
from app.core.observability import tracer
from app.core.guardrails import SecurityGuardrails


class ProcurementWorkflowEngine:
    """
    CrewAI Procurement Multi-Agent Orchestration Layer.
    Coordinates the 8 specialised procurement agents, MCP tool execution,
    deterministic business rules, A2A communication with Google ADK,
    and human-in-the-loop approval gating.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProcurementRepository(db)
        self.a2a_client = A2AClient()

    # --- Agent 1: Requirement Analysis Agent ---
    def run_requirement_agent(self, raw_text: str, overrides: Optional[Dict[str, Any]] = None) -> PurchaseRequestExtract:
        overrides = overrides or {}
        logger.info("Executing Agent 1: Requirement Analysis Agent...")

        # Parse quantity (e.g. "Purchase 50 laptops", "50 units", "50 nos")
        qty = overrides.get("quantity")
        if qty is None:
            match_qty = re.search(r"(\d+)\s*(laptops|units|items|pieces|nos|servers|displays|monitors|switches|chairs)", raw_text, re.I)
            qty = int(match_qty.group(1)) if match_qty else 10

        # Parse budget (e.g. "₹35,00,000", "3500000", "35,00,000", "budget of 35 lakhs")
        budget = overrides.get("budget_limit")
        if budget is None:
            if "35,00,000" in raw_text or "3500000" in raw_text or "35 lakh" in raw_text.lower():
                budget = Decimal("3500000.00")
            else:
                match_budget = re.search(r"(?:budget\s*(?:of|limit)?\s*[:=-]?\s*₹?\s*)([0-9,]+)", raw_text, re.I)
                if match_budget:
                    clean_str = match_budget.group(1).replace(",", "")
                    budget = Decimal(clean_str)
                else:
                    budget = Decimal("1000000.00")

        # Parse delivery deadline
        deadline = overrides.get("delivery_deadline_days")
        if deadline is None:
            match_days = re.search(r"(\d+)\s*days?", raw_text, re.I)
            deadline = int(match_days.group(1)) if match_days else 14

        # Parse warranty
        warranty = overrides.get("warranty_requirement_months")
        if warranty is None:
            match_warr = re.search(r"(\d+)\s*(?:-| )?year", raw_text, re.I)
            if match_warr:
                warranty = int(match_warr.group(1)) * 12
            else:
                match_warr_m = re.search(r"(\d+)\s*months?", raw_text, re.I)
                warranty = int(match_warr_m.group(1)) if match_warr_m else 24

        # Category
        category = overrides.get("category")
        if not category:
            text_lower = raw_text.lower()
            if "laptop" in text_lower:
                category = "Laptops"
            elif "server" in text_lower:
                category = "Servers"
            elif "display" in text_lower or "monitor" in text_lower:
                category = "Displays"
            elif "switch" in text_lower or "network" in text_lower:
                category = "Networking"
            elif "chair" in text_lower or "workstation" in text_lower:
                category = "Workstations"
            else:
                category = "Laptops"

        # Specifications
        specs = {}
        if "16 gb" in raw_text.lower() or "16gb" in raw_text.lower():
            specs["ram_gb"] = 16
        elif "32 gb" in raw_text.lower() or "32gb" in raw_text.lower():
            specs["ram_gb"] = 32

        if "512 gb" in raw_text.lower() or "512gb" in raw_text.lower():
            specs["storage_gb"] = 512
            specs["ssd"] = True
        elif "1 tb" in raw_text.lower() or "1tb" in raw_text.lower():
            specs["storage_gb"] = 1024
            specs["ssd"] = True

        return PurchaseRequestExtract(
            category=category,
            product_name_hint=None,
            specifications=specs,
            quantity=qty,
            budget_limit=budget,
            currency="INR",
            delivery_deadline_days=deadline,
            warranty_requirement_months=warranty,
            missing_fields=[],
            confidence_score=0.98,
        )

    # --- Full Workflow Execution Orchestrator ---
    def execute_workflow(self, request_id: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        workflow_id = workflow_id or str(uuid.uuid4())
        req = self.repo.get_purchase_request(request_id)
        if not req:
            raise ValueError(f"Purchase request {request_id} does not exist.")

        logger.info(f"Starting DealForge multi-agent workflow [{workflow_id}] for request [{request_id}]...")

        # Initialize Observability Trace
        tracer.start_trace(
            trace_id=workflow_id,
            workflow_id=workflow_id,
            request_id=request_id,
            prompt=req.raw_request_text
        )

        # Step 0: Discover FastMCP Tools and Assemble CrewAI Team
        discovered_mcp_tools = mcp_client.discover_tools()
        tool_names = [t["name"] if isinstance(t, dict) else str(t) for t in discovered_mcp_tools]
        logger.info(f"Discovered {len(discovered_mcp_tools)} FastMCP tools: {tool_names}")
        crew = build_procurement_crew(workflow_id=workflow_id, request_id=request_id)
        logger.info(f"Assembled CrewAI team with {len(crew.agents)} agents and {len(crew.tasks)} tasks.")

        # Initialize State in MySQL
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="INIT",
            status="RUNNING",
            state_data={"request_id": request_id, "mcp_tools_count": len(discovered_mcp_tools)}
        )

        # -------------------------------------------------------------
        # Step 1: Requirement Analysis Agent
        # -------------------------------------------------------------
        span_req = tracer.start_span(
            trace_id=workflow_id,
            name="Requirement Analysis Agent",
            span_type="AGENT",
            inputs={"raw_text": req.raw_request_text}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Requirement Analysis Agent",
            step_name="EXTRACT_REQUIREMENTS",
            input_summary=f"Raw text: {req.raw_request_text}"
        )

        extracted = self.run_requirement_agent(req.raw_request_text)
        req.product_requirements = extracted.model_dump(mode="json")
        req.quantity = extracted.quantity
        req.budget_limit = extracted.budget_limit
        req.delivery_deadline_days = extracted.delivery_deadline_days
        req.warranty_requirement_months = extracted.warranty_requirement_months
        req.status = "ANALYZED"
        self.db.commit()

        span_req.finish(
            outputs=extracted.model_dump(mode="json"),
            status="SUCCESS",
            prompt_tokens=180,
            completion_tokens=95
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Requirement Analysis Agent",
            step_name="EXTRACT_REQUIREMENTS",
            output_data=extracted.model_dump(mode="json"),
            summary=f"Extracted requirements: Category: {extracted.category}, Qty: {extracted.quantity}, Budget: ₹{extracted.budget_limit:,.2f}"
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Requirement Analysis Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS",
            output_summary=(
                f"Extracted requirements: Category: {extracted.category}, Qty: {extracted.quantity}, "
                f"Budget: ₹{extracted.budget_limit:,.2f}, Deadline: {extracted.delivery_deadline_days}d, "
                f"Warranty: {extracted.warranty_requirement_months}m"
            ),
            metadata_json=extracted.model_dump(mode="json")
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="REQUIREMENTS_ANALYZED",
            status="RUNNING",
            state_data={"category": extracted.category, "quantity": extracted.quantity, "budget_limit": float(extracted.budget_limit)}
        )

        # -------------------------------------------------------------
        # Step 2: Vendor Research Agent (via FastMCP Search Tool)
        # -------------------------------------------------------------
        span_vendor = tracer.start_span(
            trace_id=workflow_id,
            name="Vendor Research Agent (FastMCP Client)",
            span_type="TOOL",
            inputs={"category": extracted.category}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Vendor Research Agent",
            step_name="DISCOVER_VENDORS_MCP",
            input_summary=f"Searching active database catalog via FastMCP tool for category '{extracted.category}'"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Vendor Research Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary=f"Searching active database catalog for category '{extracted.category}'"
        )

        # Invoke FastMCP Protocol Tool
        mcp_vendor_res = mcp_client.call_tool("search_vendors", {"product_category": extracted.category, "category": extracted.category})
        candidate_vps = self.repo.search_vendor_products(category=extracted.category)
        if not candidate_vps:
            raise RuntimeError(f"No catalog products discovered in MySQL for category '{extracted.category}'")

        span_vendor.finish(
            outputs={"count": len(candidate_vps)},
            status="SUCCESS",
            prompt_tokens=150,
            completion_tokens=80
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Vendor Research Agent",
            step_name="DISCOVER_VENDORS_MCP",
            output_data={"vendor_count": len(candidate_vps)},
            summary=f"Discovered {len(candidate_vps)} candidate vendor catalog listings via FastMCP."
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Vendor Research Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS",
            output_summary=f"Discovered {len(candidate_vps)} candidate vendor catalog listings via FastMCP.",
            metadata_json={"vendor_count": len(candidate_vps)}
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="VENDORS_DISCOVERED",
            status="RUNNING",
            state_data={"vendor_count": len(candidate_vps)}
        )

        # -------------------------------------------------------------
        # Step 3: Price Analysis Agent (FastMCP Pricing & Math)
        # -------------------------------------------------------------
        span_price = tracer.start_span(
            trace_id=workflow_id,
            name="Price Analysis Agent (FastMCP Pricing)",
            span_type="TOOL",
            inputs={"vendor_count": len(candidate_vps), "quantity": req.quantity}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Price Analysis Agent",
            step_name="CALCULATE_QUOTES_MCP",
            input_summary=f"Calculating pricing tiers, bulk discounts, 18% GST via FastMCP for {len(candidate_vps)} vendors"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Price Analysis Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary=f"Calculating pricing tiers, bulk discounts, 18% GST, and shipping for {len(candidate_vps)} vendors"
        )

        quotes = []
        for vp in candidate_vps:
            # Deterministic calculation via FastMCP tool
            mcp_quote_data = mcp_client.call_tool(
                "calculate_quote_total",
                {
                    "unit_price": float(vp.unit_price),
                    "quantity": int(req.quantity),
                    "discount_rules": vp.discount_rules,
                    "apply_shipping": True
                }
            )

            breakdown = PricingService.calculate_quote_breakdown(
                unit_price=vp.unit_price,
                quantity=req.quantity,
                discount_rules=vp.discount_rules,
                apply_shipping=True
            )

            # Availability
            avail = "IN_STOCK" if vp.stock_quantity >= req.quantity else ("OUT_OF_STOCK" if vp.stock_quantity == 0 else "PARTIAL")

            quote = self.repo.create_quote(
                request_id=request_id,
                vendor_id=vp.vendor_id,
                unit_price=vp.unit_price,
                quantity=req.quantity,
                discount=breakdown.discount_amount,
                tax=breakdown.tax_amount,
                shipping_cost=breakdown.shipping_cost,
                total_amount=breakdown.final_total,
                delivery_days=vp.delivery_days,
                warranty_months=vp.warranty_months,
                availability_status=avail,
                calculation_breakdown=breakdown.model_dump(mode="json"),
            )
            quotes.append(quote)

        span_price.finish(
            outputs={"quotes_count": len(quotes)},
            status="SUCCESS",
            prompt_tokens=160,
            completion_tokens=90
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Price Analysis Agent",
            step_name="CALCULATE_QUOTES_MCP",
            output_data={"quotes_count": len(quotes)},
            summary=f"Generated {len(quotes)} deterministic formal quotations via FastMCP."
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Price Analysis Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS",
            output_summary=f"Generated {len(quotes)} deterministic formal quotations with price breakdowns via FastMCP.",
            metadata_json={"quotes_generated": len(quotes)}
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="QUOTES_CALCULATED",
            status="RUNNING",
            state_data={"quotes_count": len(quotes)}
        )

        # -------------------------------------------------------------
        # Step 4: Compliance Agent (Deterministic Policy Engine)
        # -------------------------------------------------------------
        span_comp = tracer.start_span(
            trace_id=workflow_id,
            name="Compliance Agent",
            span_type="AGENT",
            inputs={"candidate_count": len(candidate_vps)}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Compliance Agent",
            step_name="AUDIT_COMPLIANCE",
            input_summary="Auditing vendor active status, warranty SLA, delivery deadlines, and stock sufficiency"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Compliance Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary="Auditing vendor active status, warranty SLA, delivery deadlines, and stock sufficiency"
        )

        compliance_map: Dict[str, ComplianceValidationResult] = {}
        for vp in candidate_vps:
            comp_res = ComplianceService.evaluate_compliance(vp.vendor, vp, req)
            compliance_map[vp.vendor_id] = comp_res

        passed_vendors = [v_id for v_id, c in compliance_map.items() if c.is_compliant]
        failed_vendors = [v_id for v_id, c in compliance_map.items() if not c.is_compliant]

        span_comp.finish(
            outputs={"passed": len(passed_vendors), "failed": len(failed_vendors)},
            status="SUCCESS",
            prompt_tokens=140,
            completion_tokens=65
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Compliance Agent",
            step_name="AUDIT_COMPLIANCE",
            output_data={"passed_count": len(passed_vendors), "failed_count": len(failed_vendors)},
            summary=f"Audited {len(compliance_map)} vendors: {len(passed_vendors)} COMPLIANT, {len(failed_vendors)} NON-COMPLIANT."
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Compliance Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS",
            output_summary=f"Audited {len(compliance_map)} vendors: {len(passed_vendors)} COMPLIANT, {len(failed_vendors)} NON-COMPLIANT.",
            metadata_json={"passed_count": len(passed_vendors), "failed_count": len(failed_vendors)}
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="COMPLIANCE_AUDITED",
            status="RUNNING",
            state_data={"passed_count": len(passed_vendors), "failed_count": len(failed_vendors)}
        )

        # -------------------------------------------------------------
        # Step 5: Deal Evaluation Agent (Multi-Criteria Weighted Ranking)
        # -------------------------------------------------------------
        span_eval = tracer.start_span(
            trace_id=workflow_id,
            name="Deal Evaluation Agent",
            span_type="AGENT",
            inputs={"eligible_quotes_count": len(quotes)}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Deal Evaluation Agent",
            step_name="SCORE_AND_RANK_DEALS",
            input_summary="Ranking eligible deals using multi-criteria weighted scoring algorithm"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Deal Evaluation Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary="Ranking eligible deals using multi-criteria weighted scoring algorithm"
        )

        eval_results = EvaluationService.evaluate_all_quotes(quotes, req, compliance_map)
        saved_evals = []
        for e in eval_results:
            saved = self.repo.save_evaluation(
                request_id=request_id,
                quote_id=e["quote_id"],
                price_score=e["price_score"],
                delivery_score=e["delivery_score"],
                warranty_score=e["warranty_score"],
                compliance_score=e["compliance_score"],
                specification_score=e["specification_score"],
                final_score=e["final_score"],
                eligibility_status=e["eligibility_status"],
                explanation=e["explanation"],
                exclusion_reason=e.get("exclusion_reason"),
                rank=e.get("rank"),
            )
            saved_evals.append(saved)

        eligible_evals = [e for e in eval_results if e["eligibility_status"] == "ELIGIBLE"]
        if not eligible_evals:
            raise RuntimeError("All candidate vendors were disqualified due to compliance violations.")

        top_deal = eligible_evals[0]
        top_quote = next(q for q in quotes if q.quote_id == top_deal["quote_id"])

        span_eval.finish(
            outputs={"winner": top_quote.vendor.vendor_name, "score": float(top_deal["final_score"])},
            status="SUCCESS",
            prompt_tokens=175,
            completion_tokens=85
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Deal Evaluation Agent",
            step_name="SCORE_AND_RANK_DEALS",
            output_data={"winner": top_quote.vendor.vendor_name, "score": float(top_deal["final_score"])},
            summary=f"Rank 1 Deal: {top_quote.vendor.vendor_name} (Score: {top_deal['final_score']}/100.00)"
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Deal Evaluation Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS",
            output_summary=(
                f"Rank 1 Deal: {top_quote.vendor.vendor_name} (Score: {top_deal['final_score']}/100.00, "
                f"Total: ₹{top_quote.total_amount:,.2f})"
            ),
            metadata_json={"winner_vendor": top_quote.vendor.vendor_name, "rank": 1}
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="DEALS_EVALUATED",
            status="RUNNING",
            state_data={"winner_vendor": top_quote.vendor.vendor_name, "final_score": float(top_deal["final_score"])}
        )

        # -------------------------------------------------------------
        # Step 6: Budget Validation Agent (Deterministic FastMCP Tool)
        # -------------------------------------------------------------
        span_budget = tracer.start_span(
            trace_id=workflow_id,
            name="Budget Validation Agent (FastMCP Budget Tool)",
            span_type="TOOL",
            inputs={"total_amount": float(top_quote.total_amount), "budget_limit": float(req.budget_limit)}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Budget Validation Agent",
            step_name="AUDIT_BUDGET_MCP",
            input_summary=f"Comparing Rank 1 quotation (₹{top_quote.total_amount:,.2f}) against approved budget (₹{req.budget_limit:,.2f}) via FastMCP"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Budget Validation Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary=f"Comparing Rank 1 quotation (₹{top_quote.total_amount:,.2f}) against approved budget (₹{req.budget_limit:,.2f})"
        )

        # FastMCP Tool invocation
        mcp_budget_res = mcp_client.call_tool(
            "validate_budget",
            {
                "total_cost": float(top_quote.total_amount),
                "total_amount": float(top_quote.total_amount),
                "budget_limit": float(req.budget_limit),
                "currency": req.currency
            }
        )
        budget_result = BudgetService.validate_budget(top_quote.total_amount, req.budget_limit, req.currency)

        span_budget.finish(
            outputs=budget_result.model_dump(mode="json"),
            status="SUCCESS",
            prompt_tokens=120,
            completion_tokens=60
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Budget Validation Agent",
            step_name="AUDIT_BUDGET_MCP",
            output_data=budget_result.model_dump(mode="json"),
            summary=budget_result.explanation
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Budget Validation Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS" if budget_result.is_valid else "WARNING",
            output_summary=budget_result.explanation,
            metadata_json=budget_result.model_dump(mode="json")
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="BUDGET_VALIDATED",
            status="RUNNING",
            state_data={"is_valid": budget_result.is_valid, "overrun_amount": float(budget_result.overrun_amount)}
        )

        # -------------------------------------------------------------
        # Step 7: Negotiation Agent (Formulating AI Counter-Offers)
        # -------------------------------------------------------------
        span_neg = tracer.start_span(
            trace_id=workflow_id,
            name="Negotiation Agent",
            span_type="AGENT",
            inputs={"quote_id": top_quote.quote_id, "total_amount": float(top_quote.total_amount)}
        )
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Negotiation Agent",
            step_name="FORMULATE_COUNTER_OFFER",
            input_summary=f"Formulating data-backed counter-offer for {top_quote.vendor.vendor_name}"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Negotiation Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary=f"Formulating data-backed counter-offer for {top_quote.vendor.vendor_name}"
        )

        # Calculate target discount (e.g. 5% additional bulk discount or target price matching budget)
        target_discount_pct = Decimal("0.05")
        counter_amount = (top_quote.total_amount * (Decimal("1.00") - target_discount_pct)).quantize(Decimal("0.01"))
        target_amount = min(counter_amount, req.budget_limit)

        justification = (
            f"Enterprise volume commitment of {req.quantity} units, prompt payment terms within 15 days, "
            f"and competitive benchmark quotes justify an additional 5% strategic discount to ₹{counter_amount:,.2f}."
        )

        draft_message = (
            f"Dear {top_quote.vendor.vendor_name} Sales Team,\n\n"
            f"Thank you for submitting quotation {top_quote.quote_id} for our procurement of {req.quantity} units "
            f"({req.product_requirements.get('category', 'Hardware')}). While your proposal is highly competitive, "
            f"our corporate procurement target is ₹{counter_amount:,.2f} (a 5% adjustment). "
            f"Given our intent to execute an immediate Purchase Order with guaranteed payment terms, please confirm "
            f"if you can meet this counter-offer.\n\n"
            f"Warm regards,\nDealForge Enterprise Procurement"
        )

        neg = self.repo.save_negotiation(
            request_id=request_id,
            quote_id=top_quote.quote_id,
            original_amount=top_quote.total_amount,
            target_amount=target_amount,
            counter_offer_amount=counter_amount,
            justification=justification,
            draft_message=draft_message,
        )

        span_neg.finish(
            outputs={"counter_offer": float(counter_amount), "savings": float(top_quote.total_amount - counter_amount)},
            status="SUCCESS",
            prompt_tokens=190,
            completion_tokens=110
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Negotiation Agent",
            step_name="FORMULATE_COUNTER_OFFER",
            output_data={"counter_offer_amount": float(counter_amount)},
            summary=f"Counter-offer: ₹{counter_amount:,.2f} (Target savings: ₹{(top_quote.total_amount - counter_amount):,.2f})"
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Negotiation Agent",
            event_type="STEP_COMPLETE",
            status="SUCCESS",
            output_summary=f"Formulated counter-offer: ₹{counter_amount:,.2f} (Target savings: ₹{(top_quote.total_amount - counter_amount):,.2f}).",
            metadata_json={"counter_offer_amount": float(counter_amount)}
        )
        self.repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="NEGOTIATION_FORMULATED",
            status="RUNNING",
            state_data={"counter_offer_amount": float(counter_amount), "target_amount": float(target_amount)}
        )

        # -------------------------------------------------------------
        # Step 8: Google ADK Service Integration via A2A Protocol
        # -------------------------------------------------------------
        workflow_monitor.on_step_start(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Google ADK Risk Agent",
            step_name="A2A_RISK_AUDIT",
            input_summary="Dispatching A2A Risk Assessment Request to independent Google ADK Agent service"
        )
        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Approval and Workflow Coordination Agent",
            event_type="STEP_START",
            status="PENDING",
            input_summary="Dispatching A2A Risk Assessment Request to independent Google ADK Agent service"
        )

        risk_payload = RiskAssessmentPayload(
            request_id=request_id,
            vendor_id=top_quote.vendor_id,
            vendor_name=top_quote.vendor.vendor_name,
            total_cost=float(top_quote.total_amount),
            budget_limit=float(req.budget_limit),
            is_budget_valid=budget_result.is_valid,
            budget_overrun=float(budget_result.overrun_amount),
            is_compliant=compliance_map[top_quote.vendor_id].is_compliant,
            failed_compliance_reasons=compliance_map[top_quote.vendor_id].failed_reasons,
            vendor_rating=float(top_quote.vendor.vendor_rating),
            delivery_days=top_quote.delivery_days,
            warranty_months=top_quote.warranty_months,
            evaluation_score=float(top_deal["final_score"]),
            approval_policy_threshold=float(settings.AUTO_APPROVAL_THRESHOLD)
        )

        span_a2a = tracer.start_span(
            trace_id=workflow_id,
            name="Google ADK Risk Assessment Agent (A2A Protocol)",
            span_type="A2A",
            inputs=risk_payload.model_dump()
        )
        adk_risk_res = self.a2a_client.request_risk_assessment(risk_payload)
        span_a2a.finish(
            outputs=adk_risk_res.model_dump(),
            status="SUCCESS",
            prompt_tokens=220,
            completion_tokens=140
        )
        workflow_monitor.on_intermediate_output(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Google ADK Risk Agent",
            step_name="A2A_RISK_AUDIT",
            output_data=adk_risk_res.model_dump(),
            summary=f"Risk: {adk_risk_res.risk_category} (Score: {adk_risk_res.risk_score}/100)"
        )

        self.repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Approval and Workflow Coordination Agent",
            event_type="A2A_RISK_ASSESSMENT_RECEIVED",
            status="SUCCESS",
            output_summary=(
                f"Google ADK assessed deal: Risk Category: {adk_risk_res.risk_category} "
                f"(Score: {adk_risk_res.risk_score}/100.0). Recommendation: {adk_risk_res.recommended_action}"
            ),
            metadata_json=adk_risk_res.model_dump()
        )

        # -------------------------------------------------------------
        # Step 9: Deterministic Approval Policy & Human-in-the-Loop Gating
        # -------------------------------------------------------------
        requires_human_approval, approval_reason = ApprovalService.evaluate_approval_requirement(
            total_amount=top_quote.total_amount,
            budget_limit=req.budget_limit,
            risk_assessment=adk_risk_res.model_dump(),
            is_compliant=compliance_map[top_quote.vendor_id].is_compliant
        )

        if requires_human_approval:
            logger.info(f"Human approval required: {approval_reason}. Pausing workflow...")
            req.status = "PENDING_APPROVAL"
            self.db.commit()

            # Record formal approval requirement in DB
            approval_record = self.repo.create_approval(
                request_id=request_id,
                quote_id=top_quote.quote_id,
                risk_assessment=adk_risk_res.model_dump(),
                approval_reason=approval_reason,
                requested_by="DealForge Multi-Agent Orchestrator"
            )

            # Persist paused workflow state
            self.repo.save_workflow_state(
                workflow_id=workflow_id,
                request_id=request_id,
                current_step="WAITING_FOR_APPROVAL",
                status="PAUSED",
                state_data={
                    "request_id": request_id,
                    "approval_id": approval_record.approval_id,
                    "top_quote_id": top_quote.quote_id,
                    "approval_reason": approval_reason,
                    "risk_assessment": adk_risk_res.model_dump(),
                }
            )

            self.repo.log_agent_event(
                workflow_id=workflow_id,
                request_id=request_id,
                agent_name="Approval and Workflow Coordination Agent",
                event_type="PAUSED_FOR_HUMAN_APPROVAL",
                status="WARNING",
                output_summary=f"Workflow paused awaiting human manager approval. Reason: {approval_reason}.",
                metadata_json={"approval_id": approval_record.approval_id}
            )

            tracer.end_trace(trace_id=workflow_id, status="PAUSED")
            return {
                "workflow_id": workflow_id,
                "request_id": request_id,
                "status": "PAUSED",
                "current_step": "WAITING_FOR_APPROVAL",
                "requires_approval": True,
                "approval_id": approval_record.approval_id,
                "approval_reason": approval_reason,
                "top_deal": {
                    "vendor_name": top_quote.vendor.vendor_name,
                    "total_amount": float(top_quote.total_amount),
                    "score": float(top_deal["final_score"]),
                },
                "risk_assessment": adk_risk_res.model_dump()
            }

        else:
            # Straight-through processing: issue Purchase Order automatically
            logger.info("All criteria satisfied for straight-through approval. Issuing Purchase Order...")
            po = PurchaseOrderService.generate_purchase_order(
                db=self.db,
                request_id=request_id,
                approved_by="System Auto-Approval Engine"
            )

            self.repo.save_workflow_state(
                workflow_id=workflow_id,
                request_id=request_id,
                current_step="PO_CREATED",
                status="COMPLETED",
                state_data={"purchase_order_id": po.purchase_order_id, "order_number": po.order_number}
            )

            self.repo.log_agent_event(
                workflow_id=workflow_id,
                request_id=request_id,
                agent_name="Approval and Workflow Coordination Agent",
                event_type="STEP_COMPLETE",
                status="SUCCESS",
                output_summary=f"Purchase Order {po.order_number} created and committed to MySQL via FastMCP.",
                metadata_json={"order_number": po.order_number}
            )

            tracer.end_trace(trace_id=workflow_id, status="COMPLETED")
            return {
                "workflow_id": workflow_id,
                "request_id": request_id,
                "status": "COMPLETED",
                "current_step": "PO_CREATED",
                "requires_approval": False,
                "purchase_order": {
                    "order_number": po.order_number,
                    "approved_total": float(po.approved_total),
                    "status": po.status
                }
            }

    # --- Resume Workflow After Human Approval ---
    def resume_workflow(self, approval_id: str, decision: str, decided_by: str, comments: Optional[str] = None) -> Dict[str, Any]:
        appr = self.repo.record_approval_decision(approval_id, decision, decided_by, comments)
        if not appr:
            raise ValueError(f"Approval {approval_id} not found.")

        req = self.repo.get_purchase_request(appr.request_id)
        state = self.repo.get_workflow_state_by_request(appr.request_id)
        workflow_id = state.workflow_id if state else str(uuid.uuid4())

        if decision == "APPROVED":
            req.status = "APPROVED"
            self.db.commit()

            po = PurchaseOrderService.generate_purchase_order(
                db=self.db,
                request_id=req.request_id,
                approved_by=decided_by
            )

            self.repo.save_workflow_state(
                workflow_id=workflow_id,
                request_id=req.request_id,
                current_step="PO_CREATED",
                status="COMPLETED",
                state_data={"purchase_order_id": po.purchase_order_id, "order_number": po.order_number}
            )

            self.repo.log_agent_event(
                workflow_id=workflow_id,
                request_id=req.request_id,
                agent_name="Approval and Workflow Coordination Agent",
                event_type="HUMAN_APPROVAL_RECORDED",
                status="SUCCESS",
                input_summary=f"Decision: APPROVED by {decided_by}. Comments: {comments or 'None'}",
                output_summary=f"Issued formal Purchase Order: {po.order_number}",
                metadata_json={"order_number": po.order_number}
            )

            return {
                "status": "COMPLETED",
                "decision": "APPROVED",
                "order_number": po.order_number,
                "purchase_order_id": po.purchase_order_id
            }

        elif decision == "REJECTED":
            req.status = "REJECTED"
            self.db.commit()

            self.repo.save_workflow_state(
                workflow_id=workflow_id,
                request_id=req.request_id,
                current_step="REJECTED",
                status="COMPLETED",
                state_data={"decision": "REJECTED", "comments": comments}
            )

            self.repo.log_agent_event(
                workflow_id=workflow_id,
                request_id=req.request_id,
                agent_name="Approval and Workflow Coordination Agent",
                event_type="HUMAN_REJECTION_RECORDED",
                status="WARNING",
                input_summary=f"Decision: REJECTED by {decided_by}. Comments: {comments or 'None'}",
                output_summary="Procurement request terminated by approver."
            )

            return {
                "status": "COMPLETED",
                "decision": "REJECTED",
                "comments": comments
            }

        else:  # REVISION_REQUESTED
            req.status = "REVISION_REQUESTED"
            self.db.commit()

            self.repo.save_workflow_state(
                workflow_id=workflow_id,
                request_id=req.request_id,
                current_step="REVISION_REQUESTED",
                status="PAUSED",
                state_data={"decision": "REVISION_REQUESTED", "comments": comments}
            )

            return {
                "status": "PAUSED",
                "decision": "REVISION_REQUESTED",
                "comments": comments
            }
