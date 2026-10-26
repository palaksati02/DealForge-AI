import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.db.repositories.procurement_repo import ProcurementRepository
from app.agents.procurement_crew import ProcurementWorkflowEngine


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_login_and_me(client):
    # Test valid login with seeded manager credentials
    res = client.post("/api/auth/login", json={
        "email": "manager@dealforge.ai",
        "password": "Manager@123"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "manager@dealforge.ai"
    assert data["user"]["role_name"] == "Procurement Manager"

    token = data["access_token"]

    # Test /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "manager@dealforge.ai"
    assert me_data["role_name"] == "Procurement Manager"


def test_auth_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "manager@dealforge.ai",
        "password": "WrongPassword!999"
    })
    assert res.status_code == 401


def test_procurement_request_lifecycle_and_report(client, db_session, repo):
    # Submit request via canonical endpoint
    payload = {
        "requester": "Engineering Lead",
        "raw_request_text": "Procure 30 enterprise laptops with 32GB RAM, 1TB SSD, delivery under 15 days, 3-year warranty, max budget ₹25,00,000",
        "quantity_override": 30,
        "budget_override": 2500000.0,
        "deadline_override_days": 15,
        "warranty_override_months": 36,
        "category_override": "Laptops"
    }
    # Create via API without background task so we can control execution
    create_res = client.post("/api/procurement/requests?auto_start=false", json=payload)
    assert create_res.status_code == 201
    req_data = create_res.json()
    request_id = req_data["request_id"]
    assert req_data["quantity"] == 30
    assert Decimal(str(req_data["budget_limit"])) == Decimal("2500000.00")

    # Run workflow via engine
    engine = ProcurementWorkflowEngine(db_session)
    wf_res = engine.execute_workflow(request_id=request_id)
    assert wf_res["status"] in ["PAUSED", "COMPLETED"]

    # Check status endpoint
    status_res = client.get(f"/api/procurement/requests/{request_id}/status")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["request_id"] == request_id
    assert len(st_data["logs"]) > 0

    # Check report generation endpoint
    report_res = client.get(f"/api/procurement/requests/{request_id}/report")
    assert report_res.status_code == 200
    rep_data = report_res.json()
    assert rep_data["request_id"] == request_id
    assert "vendor_matrix" in rep_data
    assert len(rep_data["vendor_matrix"]) > 0
    assert "markdown_report" in rep_data
    assert "DEALFORGE AI" in rep_data["markdown_report"]


def test_approval_submission_and_idempotency(client, db_session, repo):
    # Setup request requiring approval
    req = repo.create_purchase_request(
        requester="Lab Admin",
        raw_request_text="50 laptops max 40L budget",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("4000000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24
    )
    engine = ProcurementWorkflowEngine(db_session)
    wf_res = engine.execute_workflow(request_id=req.request_id)
    assert wf_res["status"] == "PAUSED"
    approval_id = wf_res["approval_id"]

    # Approve via canonical endpoint
    appr_payload = {
        "decision": "APPROVED",
        "decided_by": "Priya Venkatesh",
        "comments": "Approved after technical compliance audit."
    }
    appr_res = client.post(f"/api/procurement/requests/{req.request_id}/approval", json=appr_payload)
    assert appr_res.status_code == 200
    data = appr_res.json()
    assert data["status"] == "COMPLETED"
    assert data["decision"] == "APPROVED"
    assert "order_number" in data

    # Test idempotency / duplicate submission protection
    dup_res = client.post(f"/api/procurement/requests/{req.request_id}/approval", json=appr_payload)
    # Since approval is no longer PENDING, it returns 404 No pending approval
    assert dup_res.status_code in [400, 404]


def test_replanning_via_api(client, db_session, repo):
    req = repo.create_purchase_request(
        requester="Operations Mgr",
        raw_request_text="50 laptops max 38L",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00")
    )
    engine = ProcurementWorkflowEngine(db_session)
    wf_res = engine.execute_workflow(request_id=req.request_id)

    # Trigger budget cut replan
    replan_res = client.post(f"/api/procurement/requests/{req.request_id}/replan", json={
        "trigger_type": "BUDGET_CUT",
        "new_budget": 3200000.0
    })
    assert replan_res.status_code == 200
    rp_data = replan_res.json()
    assert rp_data["event"] == "BUDGET_REDUCED"
    assert rp_data["new_budget"] == 3200000.0
