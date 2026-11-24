import sys
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from app.mcp.tools import procurement_tools

# Instantiate dedicated FastMCP Server
mcp = FastMCP("DealForge-Procurement-Server")

@mcp.tool()
def search_vendors(product_category: Optional[str] = None, category: Optional[str] = None, specifications: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search database for active vendors and matching products in a given category."""
    target_cat = product_category or category or "Laptops"
    return procurement_tools.search_vendors(product_category=target_cat, specifications=specifications)

@mcp.tool()
def get_vendor_details(vendor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full contact, rating, and address details for a specific vendor from MySQL."""
    return procurement_tools.get_vendor_details(vendor_id)

@mcp.tool()
def get_vendor_quotes(request_id: str) -> List[Dict[str, Any]]:
    """Retrieve all generated quotations associated with a purchase request."""
    return procurement_tools.get_vendor_quotes(request_id)

@mcp.tool()
def get_product_inventory(product_id: str) -> List[Dict[str, Any]]:
    """Retrieve live stock levels and pricing across all vendors for a given product ID."""
    return procurement_tools.get_product_inventory(product_id)

@mcp.tool()
def get_compliance_status(vendor_id: str, request_id: str) -> Dict[str, Any]:
    """Evaluate deterministic compliance rules for a vendor against a specific purchase request."""
    return procurement_tools.get_compliance_status(vendor_id, request_id)

@mcp.tool()
def calculate_quote_total(unit_price: float, quantity: int, discount_rules: Optional[Dict[str, Any]] = None, apply_shipping: bool = True) -> Dict[str, Any]:
    """Deterministically calculate base subtotal, bulk discounts, 18% GST, shipping, and grand total."""
    return procurement_tools.calculate_quote_total(unit_price, quantity, discount_rules, apply_shipping=apply_shipping)

@mcp.tool()
def validate_budget(total_cost: Optional[float] = None, total_amount: Optional[float] = None, budget_limit: float = 0.0, currency: str = "INR") -> Dict[str, Any]:
    """Deterministically compare total quote cost against approved budget ceiling."""
    return procurement_tools.validate_budget(total_cost=total_cost, total_amount=total_amount, budget_limit=budget_limit, currency=currency)

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
    """Record a formal approval requirement in MySQL and pause workflow for human manager decision."""
    return procurement_tools.create_approval_request(request_id, quote_id, risk_assessment, approval_reason, requested_by)

@mcp.tool()
def create_purchase_order(
    request_id: str,
    vendor_id: Optional[str] = None,
    quote_id: Optional[str] = None,
    approved_total: Optional[float] = None,
    approved_by: str = "Authorized Approver",
) -> Dict[str, Any]:
    """Deterministically issue a formal Purchase Order after validations and approvals pass."""
    return procurement_tools.create_purchase_order(
        request_id=request_id,
        vendor_id=vendor_id,
        quote_id=quote_id,
        approved_total=approved_total,
        approved_by=approved_by,
    )


if __name__ == "__main__":
    # Runs the standard FastMCP server over stdio
    mcp.run()
