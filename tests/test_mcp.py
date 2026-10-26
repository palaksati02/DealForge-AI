import pytest
from app.mcp.client import mcp_client
from app.mcp.tools import procurement_tools


def test_mcp_search_vendors():
    vendors = mcp_client.search_vendors("Laptops")
    assert isinstance(vendors, list)
    assert len(vendors) >= 10
    v_nexus = next((v for v in vendors if v["vendor_id"] == "vend-nexus-01"), None)
    assert v_nexus is not None
    assert v_nexus["unit_price"] == 68000.0


def test_mcp_vendor_details_with_certifications():
    details = mcp_client.get_vendor_details("vend-nexus-01")
    assert details is not None
    assert details["vendor_name"].startswith("Nexus Tech")
    assert "certifications" in details
    assert len(details["certifications"]) >= 2
    assert any(c["certification_name"] == "ISO 9001" and c["verification_status"] == "VERIFIED" for c in details["certifications"])


def test_mcp_calculate_quote_total():
    res = mcp_client.calculate_quote_total(
        unit_price=68000.0,
        quantity=50,
        discount_rules={"tiers": [{"min_qty": 50, "discount_pct": 8.0}]},
        budget_limit=4000000.0
    )
    assert res["final_total"] == 3701040.0
    assert res["discount_amount"] == 272000.0
    assert res["effective_unit_price"] == 74020.80
    assert res["budget_utilization_percentage"] == 92.53


def test_mcp_validate_budget():
    pass_res = mcp_client.validate_budget(3000000.0, 3500000.0)
    assert pass_res["is_valid"] is True
    assert pass_res["budget_status"] == "COMPLIANT_WITHIN_BUDGET"
    assert pass_res["overrun_amount"] == 0.0

    fail_res = mcp_client.validate_budget(3800000.0, 3500000.0)
    assert fail_res["is_valid"] is False
    assert fail_res["budget_status"] == "BUDGET_OVERRUN"
    assert fail_res["overrun_amount"] == 300000.0
    assert fail_res["required_approval_level"] == "EXECUTIVE_ESCALATION"


def test_mcp_procurement_policies():
    policies = mcp_client.get_procurement_policies()
    assert isinstance(policies, list)
    assert len(policies) >= 4
    auto_app = next((p for p in policies if p["policy_code"] == "POL-AUTO-APP"), None)
    assert auto_app is not None
    assert auto_app["threshold_amount"] == 1000000.0


def test_mcp_tool_invalid_arguments():
    with pytest.raises(Exception):
        mcp_client.calculate_quote_total(unit_price=-100.0, quantity=5)

    with pytest.raises(Exception):
        mcp_client.calculate_quote_total(unit_price=100.0, quantity=0)
