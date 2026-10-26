import pytest
from decimal import Decimal
from typing import Dict, Any

from app.db.repositories.procurement_repo import ProcurementRepository
from app.agents.procurement_crew import ProcurementWorkflowEngine
from app.services.replanning_service import ReplanningService
from app.services.report_service import ReportService
from app.services.negotiation_service import NegotiationService
from app.services.pricing_service import PricingService
from app.services.compliance_service import ComplianceService
from app.services.evaluation_service import EvaluationService


def test_scenario_1_compliant_vendor_selected(db_session, repo):
    """Scenario 1: Standard compliant vendor selected successfully."""
    req = repo.create_purchase_request(
        requester="Scenario 1 Lead",
        raw_request_text="Procure 50 enterprise laptops within ₹38,00,000 budget, delivery within 14 days, min 2-year warranty.",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24,
    )
    engine = ProcurementWorkflowEngine(db_session)
    result = engine.execute_workflow(request_id=req.request_id)

    assert result["status"] in ["PAUSED", "COMPLETED"]
    assert "top_deal" in result
    assert result["top_deal"]["vendor_name"] is not None
    assert result["top_deal"]["score"] > 70.0


def test_scenario_2_cheapest_vendor_rejected_for_non_compliance(db_session, repo):
    """Scenario 2: Lowest price supplier disqualified if SLA or compliance criteria fail."""
    all_vendors = repo.get_all_vendors()
    v_cheap = all_vendors[1]
    v_quality = all_vendors[0]

    v_cheap.active_status = False  # Inactive vendor directory status
    db_session.flush()

    v_quality.active_status = True

    all_vps = repo.search_vendor_products()
    vp_cheap = next((vp for vp in all_vps if vp.vendor_id == v_cheap.vendor_id), all_vps[0])
    vp_quality = next((vp for vp in all_vps if vp.vendor_id == v_quality.vendor_id), all_vps[1])

    req = repo.create_purchase_request(
        requester="Audit Test",
        raw_request_text="50 laptops max 38L",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24
    )

    comp_cheap = ComplianceService.evaluate_compliance(v_cheap, vp_cheap, req)
    comp_quality = ComplianceService.evaluate_compliance(v_quality, vp_quality, req)

    assert comp_cheap.is_compliant is False
    assert comp_quality.is_compliant is True

    # Multi-attribute ranking gating: non-compliant is disqualified
    q_cheap = repo.create_quote(
        request_id=req.request_id,
        vendor_id=v_cheap.vendor_id,
        unit_price=Decimal("30000.00"),
        quantity=50,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        shipping_cost=Decimal("0.00"),
        total_amount=Decimal("1500000.00"),
        delivery_days=10,
        warranty_months=24,
        availability_status="IN_STOCK",
        calculation_breakdown={}
    )
    q_quality = repo.create_quote(
        request_id=req.request_id,
        vendor_id=v_quality.vendor_id,
        unit_price=Decimal("60000.00"),
        quantity=50,
        discount=Decimal("100000.00"),
        tax=Decimal("50000.00"),
        shipping_cost=Decimal("5000.00"),
        total_amount=Decimal("3427000.00"),
        delivery_days=10,
        warranty_months=24,
        availability_status="IN_STOCK",
        calculation_breakdown={}
    )

    comp_map = {
        v_cheap.vendor_id: comp_cheap,
        v_quality.vendor_id: comp_quality
    }

    evals = EvaluationService.evaluate_all_quotes(
        quotes=[q_cheap, q_quality],
        compliance_results=comp_map,
        request=req
    )

    cheap_eval = next(e for e in evals if e["quote_id"] == q_cheap.quote_id)
    quality_eval = next(e for e in evals if e["quote_id"] == q_quality.quote_id)

    assert cheap_eval["eligibility_status"] == "INELIGIBLE"
    assert cheap_eval["rank"] is None
    assert quality_eval["eligibility_status"] == "ELIGIBLE"
    assert quality_eval["rank"] == 1


def test_scenario_3_all_options_exceed_budget(db_session, repo):
    """Scenario 3: Budget too low for any supplier triggers strict budget rejection."""
    req = repo.create_purchase_request(
        requester="Underfunded Dept",
        raw_request_text="Need 50 enterprise laptops with budget ₹10,000",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("10000.00"),  # Impossibly low
        delivery_deadline_days=14,
        warranty_requirement_months=24
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)

    assert res["status"] == "FAILED"
    assert res["current_step"] in ["FAILED_ALL_DISQUALIFIED", "FAILED_BUDGET_OVERRUN"]


def test_scenario_4_negotiation_draft_within_permitted_boundaries(db_session, repo):
    """Scenario 4: Negotiation target strictly bounded within acceptable corporate discount range."""
    quote_amt = Decimal("3727000.00")
    budget_limit = Decimal("3800000.00")
    bounds = NegotiationService.calculate_negotiation_bounds(
        original_amount=quote_amt,
        budget_limit=budget_limit,
        quantity=50,
        target_discount_pct=Decimal("0.05")
    )

    assert bounds.target_price < quote_amt
    assert bounds.maximum_acceptable_price <= budget_limit
    assert bounds.estimated_savings > Decimal("0.00")
    assert bounds.is_estimate is True


def test_scenario_5_approval_pause_and_resume(db_session, repo):
    """Scenario 5: High-value transaction pauses for sign-off and resumes successfully."""
    req = repo.create_purchase_request(
        requester="Executive Admin",
        raw_request_text="50 laptops max 40L budget",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("4000000.00")
    )
    engine = ProcurementWorkflowEngine(db_session)
    result = engine.execute_workflow(request_id=req.request_id)

    assert result["status"] == "PAUSED"
    approval_id = result["approval_id"]

    # Resume workflow
    resumed = engine.resume_workflow(
        approval_id=approval_id,
        decision="APPROVED",
        decided_by="Priya Venkatesh",
        comments="Approved per delegated authority."
    )

    assert resumed["status"] == "COMPLETED"
    assert resumed["decision"] == "APPROVED"
    assert "order_number" in resumed
    assert resumed["order_number"].startswith("PO-DF-")


def test_scenario_6_rejected_approval_replanning(db_session, repo):
    """Scenario 6: Approver rejects the proposed deal, updating state to APPROVAL_REJECTED."""
    req = repo.create_purchase_request(
        requester="Executive Admin",
        raw_request_text="50 laptops max 40L budget",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("4000000.00")
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)
    approval_id = res["approval_id"]

    rejected_res = engine.resume_workflow(
        approval_id=approval_id,
        decision="REJECTED",
        decided_by="Priya Venkatesh",
        comments="Price is above target; negotiate further or switch vendor."
    )

    assert rejected_res["status"] == "REJECTED"
    assert rejected_res["decision"] == "REJECTED"
    assert req.status == "REJECTED"


def test_scenario_7_vendor_unavailability_stockout(db_session, repo):
    """Scenario 7: Vendor stockout during procurement triggers automatic promotion of alternative."""
    req = repo.create_purchase_request(
        requester="Operations Mgr",
        raw_request_text="50 laptops max 38L",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00")
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)
    wf_id = res["workflow_id"]

    # Nexus stockout
    replan = ReplanningService.handle_vendor_stockout(
        db=db_session,
        workflow_id=wf_id,
        request_id=req.request_id,
        vendor_id="vend-nexus-01"
    )

    assert replan["event"] == "VENDOR_STOCKOUT"
    assert replan["promoted_vendor"] != "None"


def test_scenario_8_unavailable_llm_safe_fallback(db_session, repo):
    """Scenario 8: Deterministic business logic functions without external LLM keys."""
    # Pricing calculation
    calc = PricingService.calculate_quote_breakdown(
        unit_price=Decimal("50000.00"),
        quantity=20,
        discount_rules={"tiers": [{"min_qty": 10, "discount_pct": 5.0}]},
        apply_shipping=True
    )
    assert calc.base_subtotal == Decimal("1000000.00")
    assert calc.discount_amount == Decimal("50000.00")
    assert calc.taxable_amount == Decimal("950000.00")
    assert calc.tax_amount == Decimal("171000.00")
    assert calc.final_total == Decimal("1128000.00")


def test_scenario_9_agent_failure_without_silent_finalization(db_session, repo):
    """Scenario 9: Unrecoverable failure records FAILED status without issuing PO."""
    req = repo.create_purchase_request(
        requester="Tester",
        raw_request_text="50 non-existent items",
        product_requirements={"category": "NonExistentCategory999"},
        quantity=50,
        budget_limit=Decimal("1000000.00")
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)

    assert res["status"] == "FAILED"
    # Verify no purchase order was issued
    po = repo.get_purchase_order_by_request(req.request_id)
    assert po is None


def test_scenario_10_end_to_end_audit_report(db_session, repo):
    """Scenario 10: Complete auditable executive procurement report generation."""
    req = repo.create_purchase_request(
        requester="Audit Test Lead",
        raw_request_text="50 laptops max 38L",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)

    # Approve
    if res.get("approval_id"):
        engine.resume_workflow(
            approval_id=res["approval_id"],
            decision="APPROVED",
            decided_by="Priya Venkatesh",
            comments="Approved for executive report audit."
        )

    # Compile report
    report = ReportService.generate_procurement_report(db_session, req.request_id)
    assert report["request_id"] == req.request_id
    assert len(report["vendor_matrix"]) > 0
    assert report["purchase_order"] is not None
    assert len(report["agent_execution_logs"]) > 0
    assert "DEALFORGE AI" in report["markdown_report"]
    assert "# DEALFORGE AI — EXECUTIVE PROCUREMENT REPORT" in report["markdown_report"]
