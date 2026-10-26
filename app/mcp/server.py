import sys
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from app.mcp.tools import procurement_tools

# Instantiate dedicated FastMCP Server
mcp = FastMCP("DealForge-Procurement-Server")


@mcp.tool()
def search_vendors(product_category: str, specifications: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search database for active vendors and matching products in a given category."""
    return procurement_tools.search_vendors(product_category, specifications)


@mcp.tool()
def get_vendor_details(vendor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full contact, rating, certifications, and address details for a specific vendor from MySQL."""
    return procurement_tools.get_vendor_details(vendor_id)


@mcp.tool()
def get_vendor_quotes(request_id: str) -> List[Dict[str, Any]]:
    """Retrieve all generated quotations associated with a purchase request."""
    return procurement_tools.get_vendor_quotes(request_id)


@mcp.tool()
def check_stock_delivery(vendor_id: str, product_id: str, required_quantity: int) -> Dict[str, Any]:
    """Check live stock sufficiency and promised delivery SLA for a vendor product."""
    return procurement_tools.check_stock_delivery(vendor_id, product_id, required_quantity)


@mcp.tool()
def get_compliance_status(vendor_id: str, request_id: str) -> Dict[str, Any]:
    """Evaluate deterministic compliance rules for a vendor against a specific purchase request."""
    return procurement_tools.get_compliance_status(vendor_id, request_id)


@mcp.tool()
def calculate_quote_total(
    unit_price: float,
    quantity: int,
    discount_rules: Optional[Dict[str, Any]] = None,
    budget_limit: Optional[float] = None
) -> Dict[str, Any]:
    """Deterministically calculate base subtotal, bulk discounts, 18% GST, shipping, effective unit price, and grand total."""
    return procurement_tools.calculate_quote_total(unit_price, quantity, discount_rules, budget_limit)


@mcp.tool()
def validate_budget(total_cost: float, budget_limit: float) -> Dict[str, Any]:
    """Deterministically compare total quote cost against approved budget ceiling and assign required approval level."""
    return procurement_tools.validate_budget(total_cost, budget_limit)


@mcp.tool()
def get_procurement_policies() -> List[Dict[str, Any]]:
    """Retrieve active corporate procurement policies, threshold limits, and mandatory requirements."""
    return procurement_tools.get_procurement_policies()


@mcp.tool()
def save_procurement_request(
    requester: str,
    raw_request_text: str,
    category: str,
    quantity: int,
    budget_limit: float,
    delivery_deadline_days: int = 14,
    warranty_requirement_months: int = 24
) -> Dict[str, Any]:
    """Save an incoming purchase request to MySQL."""
    return procurement_tools.save_procurement_request(
        requester, raw_request_text, category, quantity, budget_limit, delivery_deadline_days, warranty_requirement_months
    )


@mcp.tool()
def get_procurement_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve purchase request details from MySQL by request ID."""
    return procurement_tools.get_procurement_request(request_id)


@mcp.tool()
def record_evaluation(
    request_id: str,
    quote_id: str,
    price_score: float,
    delivery_score: float,
    warranty_score: float,
    compliance_score: float,
    specification_score: float,
    final_score: float,
    eligibility_status: str,
    explanation: str,
    exclusion_reason: Optional[str] = None,
    rank: Optional[int] = None
) -> Dict[str, Any]:
    """Record a multi-criteria vendor evaluation in MySQL."""
    return procurement_tools.record_evaluation(
        request_id, quote_id, price_score, delivery_score, warranty_score, compliance_score,
        specification_score, final_score, eligibility_status, explanation, exclusion_reason, rank
    )


@mcp.tool()
def record_procurement_audit_event(
    action: str,
    actor: str,
    request_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Record an immutable audit log entry in MySQL."""
    return procurement_tools.record_procurement_audit_event(action, actor, request_id, actor_role, details)


@mcp.tool()
def save_negotiation_proposal(
    request_id: str,
    quote_id: str,
    original_amount: float,
    target_amount: float,
    counter_offer_amount: float,
    justification: str,
    draft_message: str,
) -> Dict[str, Any]:
    """Save a vendor counter-offer proposal and justification to MySQL."""
    return procurement_tools.save_negotiation_proposal(
        request_id, quote_id, original_amount, target_amount, counter_offer_amount, justification, draft_message
    )


@mcp.tool()
def create_approval_request(
    request_id: str,
    quote_id: str,
    risk_assessment: Dict[str, Any],
    approval_reason: str,
    requested_by: str = "DealForge AI Orchestrator",
) -> Dict[str, Any]:
    """Record a formal approval requirement in MySQL and pause workflow for human decision."""
    return procurement_tools.create_approval_request(request_id, quote_id, risk_assessment, approval_reason, requested_by)


@mcp.tool()
def record_approval_decision(
    approval_id: str,
    decision: str,
    decided_by: str,
    comments: Optional[str] = None
) -> Dict[str, Any]:
    """Record an authorized human approval or rejection decision."""
    return procurement_tools.record_approval_decision(approval_id, decision, decided_by, comments)


@mcp.tool()
def create_purchase_order(
    request_id: str,
    vendor_id: str,
    quote_id: str,
    approved_total: float,
    approved_by: str,
) -> Dict[str, Any]:
    """Deterministically issue a formal Purchase Order after validations and approvals pass."""
    return procurement_tools.create_purchase_order(request_id, vendor_id, quote_id, approved_total, approved_by)


if __name__ == "__main__":
    # Runs the standard FastMCP server over stdio
    mcp.run()
