import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.db.repositories.procurement_repo import ProcurementRepository
from app.agents.procurement_crew import ProcurementWorkflowEngine
from app.services.replanning_service import ReplanningService
from app.a2a.client import A2AClient
from app.a2a.schemas import RiskAssessmentPayload
from app.adk_service.agent import adk_risk_agent

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["app_name"] == "DealForge AI"
    assert data["protocol"] == "A2A/1.0"


def test_google_adk_risk_agent_evaluation():
    payload = RiskAssessmentPayload(
        request_id="req-test-adk",
        vendor_id="vend-nexus-01",
        vendor_name="Nexus Tech Enterprise Solutions",
        total_cost=3701040.0,
        budget_limit=3500000.0,
        is_budget_valid=False,
        budget_overrun=201040.0,
        is_compliant=True,
        failed_compliance_reasons=[],
        vendor_rating=4.85,
        delivery_days=10,
        warranty_months=36,
        evaluation_score=94.5,
        approval_policy_threshold=1000000.0,
    )

    assessment = adk_risk_agent.evaluate_risk(payload)
    assert assessment.risk_category in ["MEDIUM", "HIGH"]
    assert assessment.risk_score > 30.0
    assert assessment.human_review_required is True
    assert "Google ADK" in assessment.assessed_by


def test_end_to_end_workflow_execution(db_session, repo):
    # Step 1: Create request (Within budget)
    req = repo.create_purchase_request(
        requester="Academic Evaluator",
        raw_request_text="Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, a maximum budget of ₹35,00,000, delivery within 14 days, and a minimum two-year warranty.",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),  # budget allows passage
        delivery_deadline_days=14,
        warranty_requirement_months=24,
    )

    engine = ProcurementWorkflowEngine(db_session)
    result = engine.execute_workflow(request_id=req.request_id)

    # Workflow pauses for human approval because total amount > AUTO_APPROVAL_THRESHOLD (₹10,00,000)
    assert result["status"] == "PAUSED"
    assert result["current_step"] == "WAITING_FOR_APPROVAL"
    assert result["requires_approval"] is True
    assert "approval_id" in result

    # Step 2: Approver approves
    approval_id = result["approval_id"]
    resume_res = engine.resume_workflow(
        approval_id=approval_id,
        decision="APPROVED",
        decided_by="Finance Director",
        comments="Approved as all technical requirements and ADK risk thresholds are met."
    )

    assert resume_res["status"] == "COMPLETED"
    assert resume_res["decision"] == "APPROVED"
    assert "order_number" in resume_res
    assert resume_res["order_number"].startswith("PO-DF-")

    # Verify PO is now persisted in DB
    po = repo.get_purchase_order_by_request(req.request_id)
    assert po is not None
    assert po.approved_by == "Finance Director"


def test_dynamic_replanning_budget_reduction(db_session, repo):
    req = repo.create_purchase_request(
        requester="Department Head",
        raw_request_text="50 laptops",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)
    wf_id = res["workflow_id"]

    # Budget cut during procurement from 38L to 30L
    replan_res = ReplanningService.handle_budget_reduction(
        db=db_session,
        workflow_id=wf_id,
        request_id=req.request_id,
        new_budget=Decimal("3000000.00")
    )

    assert replan_res["event"] == "BUDGET_REDUCED"
    assert replan_res["new_budget"] == 3000000.0
    assert req.budget_limit == Decimal("3000000.00")


def test_dynamic_replanning_vendor_stockout(db_session, repo):
    req = repo.create_purchase_request(
        requester="Department Head",
        raw_request_text="50 laptops",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)
    wf_id = res["workflow_id"]

    # Nexus reports sudden stockout
    replan_res = ReplanningService.handle_vendor_stockout(
        db=db_session,
        workflow_id=wf_id,
        request_id=req.request_id,
        vendor_id="vend-nexus-01"
    )

    assert replan_res["event"] == "VENDOR_STOCKOUT"
    assert "Nexus" in replan_res["disqualified_vendor"]
    # Check that another eligible vendor is promoted
    assert replan_res["promoted_vendor"] != "None"


def test_purchase_order_markdown_export(client, db_session, repo):
    from app.services.purchase_order_service import PurchaseOrderService
    req = repo.create_purchase_request(
        requester="Audit Officer",
        raw_request_text="50 laptops",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
    )
    engine = ProcurementWorkflowEngine(db_session)
    result = engine.execute_workflow(request_id=req.request_id)
    engine.resume_workflow(approval_id=result["approval_id"], decision="APPROVED", decided_by="CFO")

    po = repo.get_purchase_order_by_request(req.request_id)
    assert po is not None

    md = PurchaseOrderService.generate_markdown(po)
    assert "# OFFICIAL PURCHASE ORDER" in md
    assert po.order_number in md
    assert "| **PO Number** |" in md
    assert "FINAL APPROVED TOTAL" in md

    # Test API endpoint
    resp = client.get(f"/api/purchase-orders/{po.purchase_order_id}/markdown")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers.get("content-type", "")
    assert po.order_number in resp.text


def test_workflow_timeline_and_langfuse_export(client, db_session, repo):
    req = repo.create_purchase_request(
        requester="Tech Lead",
        raw_request_text="10 laptops",
        product_requirements={"category": "Laptops"},
        quantity=10,
        budget_limit=Decimal("1000000.00"),
    )
    engine = ProcurementWorkflowEngine(db_session)
    res = engine.execute_workflow(request_id=req.request_id)
    wf_id = res["workflow_id"]

    # Test Timeline API
    resp_timeline = client.get(f"/api/workflows/{wf_id}/timeline")
    assert resp_timeline.status_code == 200
    timeline_data = resp_timeline.json()
    assert timeline_data["workflow_id"] == wf_id
    assert "timeline" in timeline_data
    assert len(timeline_data["timeline"]) > 0

    # Test Langfuse Export API
    resp_langfuse = client.get(f"/api/observability/traces/{wf_id}/langfuse")
    assert resp_langfuse.status_code == 200
    langfuse_data = resp_langfuse.json()
    assert langfuse_data["id"] == wf_id
    assert "observations" in langfuse_data
    assert len(langfuse_data["observations"]) > 0
    assert "metadata" in langfuse_data
