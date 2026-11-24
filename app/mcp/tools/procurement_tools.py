from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.db.session import SessionLocal
from app.db.repositories.procurement_repo import ProcurementRepository
from app.services.pricing_service import PricingService
from app.services.budget_service import BudgetService
from app.services.compliance_service import ComplianceService
from app.services.evaluation_service import EvaluationService
from app.services.purchase_order_service import PurchaseOrderService


def search_vendors(product_category: Optional[str] = None, category: Optional[str] = None, specifications: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Search database for active vendors and matching products in a given category.
    """
    target_category = product_category or category or "Laptops"
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        vendor_products = repo.search_vendor_products(category=target_category)
        results = []
        for vp in vendor_products:
            results.append({
                "vendor_id": vp.vendor_id,
                "vendor_name": vp.vendor.vendor_name,
                "vendor_rating": float(vp.vendor.vendor_rating),
                "active_status": vp.vendor.active_status,
                "product_id": vp.product_id,
                "product_name": vp.product.product_name,
                "category": vp.product.category,
                "specifications": vp.product.specifications,
                "unit_price": float(vp.unit_price),
                "stock_quantity": vp.stock_quantity,
                "delivery_days": vp.delivery_days,
                "warranty_months": vp.warranty_months,
                "minimum_order_quantity": vp.minimum_order_quantity,
                "discount_rules": vp.discount_rules,
            })
        return results
    finally:
        db.close()


def get_vendor_details(vendor_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full contact, rating, and address details for a specific vendor from MySQL.
    """
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        v = repo.get_vendor_by_id(vendor_id)
        if not v:
            return None
        return {
            "vendor_id": v.vendor_id,
            "vendor_name": v.vendor_name,
            "contact_email": v.contact_email,
            "phone": v.phone,
            "address": v.address,
            "active_status": v.active_status,
            "vendor_rating": float(v.vendor_rating),
        }
    finally:
        db.close()


def get_vendor_quotes(request_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all generated quotations associated with a purchase request.
    """
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        quotes = repo.get_quotes_by_request(request_id)
        return [
            {
                "quote_id": q.quote_id,
                "vendor_id": q.vendor_id,
                "vendor_name": q.vendor.vendor_name,
                "unit_price": float(q.unit_price),
                "quantity": q.quantity,
                "discount": float(q.discount),
                "tax": float(q.tax),
                "shipping_cost": float(q.shipping_cost),
                "total_amount": float(q.total_amount),
                "delivery_days": q.delivery_days,
                "warranty_months": q.warranty_months,
                "availability_status": q.availability_status,
                "calculation_breakdown": q.calculation_breakdown,
            }
            for q in quotes
        ]
    finally:
        db.close()


def get_product_inventory(product_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve live stock levels and pricing across all vendors for a given product ID.
    """
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        vps = repo.search_vendor_products()
        matches = [vp for vp in vps if vp.product_id == product_id]
        return [
            {
                "vendor_id": vp.vendor_id,
                "vendor_name": vp.vendor.vendor_name,
                "stock_quantity": vp.stock_quantity,
                "unit_price": float(vp.unit_price),
                "delivery_days": vp.delivery_days,
            }
            for vp in matches
        ]
    finally:
        db.close()


def get_compliance_status(vendor_id: str, request_id: str) -> Dict[str, Any]:
    """
    Evaluate deterministic compliance rules for a vendor against a specific purchase request.
    """
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        vendor = repo.get_vendor_by_id(vendor_id)
        request = repo.get_purchase_request(request_id)
        if not vendor or not request:
            return {"error": "Vendor or request not found"}

        # Find matching product
        product_id = request.product_requirements.get("product_id", "prod-laptop-01")
        vp = repo.get_vendor_product(vendor_id, product_id)
        if not vp:
            # fallback to any product by this vendor in this category
            all_vps = repo.search_vendor_products(category=request.product_requirements.get("category", "Laptops"))
            vp = next((p for p in all_vps if p.vendor_id == vendor_id), None)

        if not vp:
            return {"error": f"Vendor has no catalog product for request"}

        res = ComplianceService.evaluate_compliance(vendor, vp, request)
        return {
            "vendor_id": res.vendor_id,
            "is_compliant": res.is_compliant,
            "checks": [c.model_dump() for c in res.checks],
            "failed_reasons": res.failed_reasons,
        }
    finally:
        db.close()


def calculate_quote_total(unit_price: float, quantity: int, discount_rules: Optional[Dict[str, Any]] = None, apply_shipping: bool = True) -> Dict[str, Any]:
    """
    Deterministically calculate base subtotal, bulk discounts, 18% GST, shipping, and grand total.
    """
    breakdown = PricingService.calculate_quote_breakdown(
        unit_price=Decimal(str(unit_price)),
        quantity=quantity,
        discount_rules=discount_rules,
        apply_shipping=apply_shipping
    )
    return {
        "base_subtotal": float(breakdown.base_subtotal),
        "discount_percentage": float(breakdown.discount_percentage),
        "discount_amount": float(breakdown.discount_amount),
        "taxable_amount": float(breakdown.taxable_amount),
        "tax_rate_percentage": float(breakdown.tax_rate_percentage),
        "tax_amount": float(breakdown.tax_amount),
        "shipping_cost": float(breakdown.shipping_cost),
        "final_total": float(breakdown.final_total),
    }


def validate_budget(total_cost: Optional[float] = None, total_amount: Optional[float] = None, budget_limit: float = 0.0, currency: str = "INR") -> Dict[str, Any]:
    """
    Deterministically compare total quote cost against approved budget ceiling.
    """
    effective_total = total_cost if total_cost is not None else (total_amount if total_amount is not None else 0.0)
    res = BudgetService.validate_budget(Decimal(str(effective_total)), Decimal(str(budget_limit)), currency=currency)
    return {
        "is_valid": res.is_valid,
        "budget_limit": float(res.budget_limit),
        "total_cost": float(res.total_cost),
        "difference": float(res.difference),
        "overrun_amount": float(res.overrun_amount),
        "explanation": res.explanation,
    }


def save_negotiation_proposal(
    request_id: str,
    quote_id: str,
    original_amount: float,
    target_amount: float,
    counter_offer_amount: float,
    justification: str,
    draft_message: str,
) -> Dict[str, Any]:
    """
    Save a vendor counter-offer proposal and justification to MySQL.
    """
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        neg = repo.save_negotiation(
            request_id=request_id,
            quote_id=quote_id,
            original_amount=Decimal(str(original_amount)),
            target_amount=Decimal(str(target_amount)),
            counter_offer_amount=Decimal(str(counter_offer_amount)),
            justification=justification,
            draft_message=draft_message,
        )
        return {
            "negotiation_id": neg.negotiation_id,
            "status": neg.negotiation_status,
            "counter_offer_amount": float(neg.counter_offer_amount),
        }
    finally:
        db.close()


def create_approval_request(
    request_id: str,
    quote_id: str,
    risk_assessment: Dict[str, Any],
    approval_reason: str,
    requested_by: str = "DealForge AI Orchestrator",
) -> Dict[str, Any]:
    """
    Record a formal approval requirement in MySQL and pause workflow for human manager decision.
    """
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        appr = repo.create_approval(
            request_id=request_id,
            quote_id=quote_id,
            risk_assessment=risk_assessment,
            approval_reason=approval_reason,
            requested_by=requested_by,
        )
        return {
            "approval_id": appr.approval_id,
            "decision": appr.decision,
            "created_at": str(appr.created_at),
        }
    finally:
        db.close()


def create_purchase_order(
    request_id: str,
    vendor_id: Optional[str] = None,
    quote_id: Optional[str] = None,
    approved_total: Optional[float] = None,
    approved_by: str = "Authorized Approver",
) -> Dict[str, Any]:
    """
    Deterministically issue a formal Purchase Order after validations and approvals pass.
    """
    db = SessionLocal()
    try:
        po = PurchaseOrderService.generate_purchase_order(
            db=db,
            request_id=request_id,
            approved_by=approved_by,
            override_total=Decimal(str(approved_total)) if approved_total else None
        )
        return {
            "purchase_order_id": po.purchase_order_id,
            "order_number": po.order_number,
            "status": po.status,
            "approved_total": float(po.approved_total),
        }
    finally:
        db.close()
