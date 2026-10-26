import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.a2a.client import a2a_client
from app.a2a.models import A2ATaskStatus

client = TestClient(app)


def test_a2a_agent_cards_discovery():
    # 1. List all services
    res = client.get("/a2a")
    assert res.status_code == 200
    data = res.json()
    assert data["protocol"] == "A2A/1.0"
    assert len(data["services"]) == 4

    # 2. Get specific agent cards
    for service_id in ["vendor-research", "procurement-analysis", "negotiation", "approval-replanning"]:
        card_res = client.get(f"/a2a/{service_id}/.well-known/agent.json")
        assert card_res.status_code == 200
        card = card_res.json()
        assert card["service_id"] == service_id
        assert card["protocol"] == "A2A/1.0"
        assert len(card["capabilities"]) >= 1
        assert len(card["supported_actions"]) >= 1


def test_a2a_vendor_research_task():
    task_res = a2a_client.submit_and_await_task(
        target_service="vendor-research",
        action="DISCOVER_VENDORS",
        request_id="req-test-a2a-vr",
        input_data={"category": "Laptops"}
    )
    assert task_res.status == A2ATaskStatus.COMPLETED
    assert task_res.service_id == "vendor-research"
    assert "vendors" in task_res.output_data
    assert task_res.output_data["vendor_count"] >= 10


def test_a2a_procurement_analysis_task_invoking_crewai():
    mock_quotes = [
        {"quote_id": "q-01", "vendor_id": "vend-nexus-01", "vendor_name": "Nexus Tech", "total_amount": 3701040.0},
        {"quote_id": "q-02", "vendor_id": "vend-apex-02", "vendor_name": "Apex Systems", "total_amount": 3800000.0},
    ]
    mock_evals = [
        {"quote_id": "q-01", "vendor_id": "vend-nexus-01", "final_score": 95.0, "rank": 1, "eligibility_status": "ELIGIBLE"},
        {"quote_id": "q-02", "vendor_id": "vend-apex-02", "final_score": 90.0, "rank": 2, "eligibility_status": "ELIGIBLE"},
    ]
    mock_compliance = {
        "vend-nexus-01": {"overall_status": "PASS", "is_compliant": True, "failed_reasons": []},
        "vend-apex-02": {"overall_status": "PASS", "is_compliant": True, "failed_reasons": []},
    }

    task_res = a2a_client.submit_and_await_task(
        target_service="procurement-analysis",
        action="ANALYZE_PROPOSALS",
        request_id="req-test-a2a-crewai",
        input_data={
            "quotes": mock_quotes,
            "request_data": {"quantity": 50, "warranty_requirement_months": 24},
            "compliance_results": mock_compliance,
            "evaluations": mock_evals,
            "negotiation_bounds": {"target_price": 3500000.0, "estimated_savings": 201040.0}
        }
    )
    assert task_res.status == A2ATaskStatus.COMPLETED
    assert task_res.service_id == "procurement-analysis"
    out = task_res.output_data
    assert out["crew_status"] == "SUCCESS"
    assert "Price Analysis Specialist" in out["agents_executed"]
    assert "Compliance Specialist" in out["agents_executed"]
    assert "Deal Evaluation Specialist" in out["agents_executed"]
    assert "Negotiation Specialist" in out["agents_executed"]
    assert out["deal_evaluation"]["rank_1_vendor"] == "Nexus Tech"


def test_a2a_negotiation_task():
    task_res = a2a_client.submit_and_await_task(
        target_service="negotiation",
        action="FORMULATE_COUNTER_OFFER",
        request_id="req-test-a2a-neg",
        input_data={
            "quote_id": "q-nexus-01",
            "vendor_name": "Nexus Tech",
            "original_amount": 3701040.0,
            "budget_limit": 3500000.0,
            "quantity": 50,
            "category": "Laptops"
        }
    )
    assert task_res.status == A2ATaskStatus.COMPLETED
    assert task_res.service_id == "negotiation"
    out = task_res.output_data
    assert out["target_price"] == 3500000.0
    assert out["estimated_savings"] == 201040.0
    assert out["is_estimate"] is True
    assert "Nexus Tech Sales Team" in out["draft_message"]


def test_a2a_approval_replanning_risk_task():
    task_res = a2a_client.submit_and_await_task(
        target_service="approval-replanning",
        action="EVALUATE_GOVERNANCE_RISK",
        request_id="req-test-a2a-appr",
        input_data={
            "total_cost": 3701040.0,
            "budget_limit": 3500000.0,
            "is_compliant": True,
            "vendor_rating": 4.85,
            "delivery_days": 10,
            "warranty_months": 36
        }
    )
    assert task_res.status == A2ATaskStatus.COMPLETED
    out = task_res.output_data
    assert out["risk_category"] in ["MEDIUM", "HIGH"]
    assert out["requires_approval"] is True


def test_a2a_invalid_action_handling():
    task_res = a2a_client.submit_and_await_task(
        target_service="vendor-research",
        action="UNKNOWN_ACTION_XYZ",
        request_id="req-test-fail",
        input_data={}
    )
    assert task_res.status == A2ATaskStatus.FAILED
    assert "Unsupported action" in task_res.error_message
