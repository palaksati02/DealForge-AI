import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.repositories.procurement_repo import ProcurementRepository
from app.core.logging import logger
from app.services.budget_service import BudgetService
from app.services.compliance_service import ComplianceService
from app.services.evaluation_service import EvaluationService


class ReplanningService:
    """
    Dynamic workflow replanning service.
    Handles unexpected procurement events (budget cuts, vendor stockouts, negotiation rejections).
    Identifies affected stages and recalculates downstream decisions deterministically.
    """

    @classmethod
    def handle_budget_reduction(
        cls,
        db: Session,
        workflow_id: str,
        request_id: str,
        new_budget: Decimal
    ) -> Dict[str, Any]:
        repo = ProcurementRepository(db)
        request = repo.get_purchase_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found.")

        old_budget = request.budget_limit
        request.budget_limit = new_budget
        db.commit()

        # Log event
        repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Approval and Workflow Coordination Agent",
            event_type="REPLAN_BUDGET_CHANGE",
            status="WARNING",
            input_summary=f"Budget reduced from ₹{old_budget:,.2f} to ₹{new_budget:,.2f}",
            output_summary="Triggering downstream re-evaluation and budget validation."
        )

        # Rerun budget validation and evaluation
        quotes = repo.get_quotes_by_request(request_id)
        compliance_results = {}
        for q in quotes:
            vendor = repo.get_vendor_by_id(q.vendor_id)
            vp = repo.get_vendor_product(q.vendor_id, request.product_requirements.get("product_id", "prod-laptop-01"))
            if vendor and vp:
                compliance_results[q.vendor_id] = ComplianceService.evaluate_compliance(vendor, vp, request)

        new_evals = EvaluationService.evaluate_all_quotes(quotes, request, compliance_results)
        for e in new_evals:
            repo.save_evaluation(
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

        return {
            "event": "BUDGET_REDUCED",
            "old_budget": float(old_budget),
            "new_budget": float(new_budget),
            "affected_stage": "BUDGET_VALIDATION_AND_EVALUATION",
            "reranked_evaluations": len(new_evals)
        }

    @classmethod
    def handle_vendor_stockout(
        cls,
        db: Session,
        workflow_id: str,
        request_id: str,
        vendor_id: str
    ) -> Dict[str, Any]:
        repo = ProcurementRepository(db)
        request = repo.get_purchase_request(request_id)
        vendor = repo.get_vendor_by_id(vendor_id)
        vendor_name = vendor.vendor_name if vendor else vendor_id

        repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name="Vendor Research Agent",
            event_type="REPLAN_VENDOR_STOCKOUT",
            status="WARNING",
            input_summary=f"Vendor '{vendor_name}' reported unexpected inventory exhaustion.",
            output_summary="Excluding vendor from active selection and promoting next eligible candidate."
        )

        quotes = repo.get_quotes_by_request(request_id)
        for q in quotes:
            if q.vendor_id == vendor_id:
                q.availability_status = "OUT_OF_STOCK"
                q.quote_status = "REJECTED"
                db.commit()

        # Re-evaluate
        evals = repo.get_evaluations_by_request(request_id)
        for e in evals:
            if e.quote.vendor_id == vendor_id:
                e.eligibility_status = "INELIGIBLE"
                e.exclusion_reason = "Vendor reported unexpected inventory stockout during procurement."
                e.final_score = Decimal("0.00")
                e.rank = None
                db.commit()

        # Re-rank remaining eligible candidates
        eligible = [e for e in evals if e.eligibility_status == "ELIGIBLE"]
        eligible.sort(key=lambda x: x.final_score, reverse=True)
        for rank, e in enumerate(eligible, start=1):
            e.rank = rank
        db.commit()

        next_winner = eligible[0].quote.vendor.vendor_name if eligible else "None"

        return {
            "event": "VENDOR_STOCKOUT",
            "disqualified_vendor": vendor_name,
            "promoted_vendor": next_winner,
            "remaining_eligible_count": len(eligible)
        }

    @classmethod
    def handle_negotiation_rejection(
        cls,
        db: Session,
        workflow_id: str,
        negotiation_id: str
    ) -> Dict[str, Any]:
        repo = ProcurementRepository(db)
        neg = repo.get_negotiation_by_id(negotiation_id)
        if not neg:
            raise ValueError(f"Negotiation {negotiation_id} not found.")

        neg.negotiation_status = "REJECTED"
        neg.vendor_response = "Vendor declined the counter-offer price. Quotation remains at original amount."
        db.commit()

        repo.log_agent_event(
            workflow_id=workflow_id,
            request_id=neg.request_id,
            agent_name="Negotiation Agent",
            event_type="REPLAN_NEGOTIATION_REJECTED",
            status="WARNING",
            input_summary=f"Vendor rejected counter-offer of ₹{neg.counter_offer_amount:,.2f}.",
            output_summary="Evaluating fallback to original quoted price or considering secondary vendor."
        )

        return {
            "event": "NEGOTIATION_REJECTED",
            "negotiation_id": negotiation_id,
            "status": "FALLBACK_TO_ORIGINAL_OR_NEXT_VENDOR"
        }
