import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from app.db.session import SessionLocal
from app.db.repositories.procurement_repo import ProcurementRepository
from app.services.pricing_service import PricingService
from app.services.budget_service import BudgetService
from app.services.compliance_service import ComplianceService
from app.services.evaluation_service import EvaluationService
from app.services.purchase_order_service import PurchaseOrderService
from app.core.logging import logger


def search_vendors(product_category: str, specifications: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search database for active vendors and matching products in a given category."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        vendor_products = repo.search_vendor_products(category=product_category)
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
    """Retrieve full contact, rating, certifications, and address details for a specific vendor from MySQL."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        v = repo.get_vendor_by_id(vendor_id)
        if not v:
            return None
        certs = repo.get_vendor_certifications(vendor_id)
        return {
            "vendor_id": v.vendor_id,
            "vendor_name": v.vendor_name,
            "contact_email": v.contact_email,
            "phone": v.phone,
            "address": v.address,
            "active_status": v.active_status,
            "vendor_rating": float(v.vendor_rating),
            "certifications": [
                {
                    "certification_name": c.certification_name,
                    "issued_by": c.issued_by,
                    "verification_status": c.verification_status,
                    "valid_until": c.valid_until.isoformat() if c.valid_until else None,
                }
                for c in certs
            ]
        }
    finally:
        db.close()


def get_vendor_quotes(request_id: str) -> List[Dict[str, Any]]:
    """Retrieve all generated quotations associated with a purchase request."""
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


def check_stock_delivery(vendor_id: str, product_id: str, required_quantity: int) -> Dict[str, Any]:
    """Check live stock sufficiency and promised delivery SLA for a vendor product."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        vp = repo.get_vendor_product(vendor_id, product_id)
        if not vp:
            return {"error": f"Vendor {vendor_id} does not offer product {product_id}"}
        is_sufficient = vp.stock_quantity >= required_quantity
        availability = "IN_STOCK" if is_sufficient else ("OUT_OF_STOCK" if vp.stock_quantity == 0 else "PARTIAL")
        return {
            "vendor_id": vendor_id,
            "product_id": product_id,
            "stock_quantity": vp.stock_quantity,
            "required_quantity": required_quantity,
            "is_sufficient": is_sufficient,
            "availability_status": availability,
            "delivery_days": vp.delivery_days
        }
    finally:
        db.close()


def get_compliance_status(vendor_id: str, request_id: str) -> Dict[str, Any]:
    """Evaluate deterministic compliance rules for a vendor against a specific purchase request."""
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
            all_vps = repo.search_vendor_products(category=request.product_requirements.get("category", "Laptops"))
            vp = next((p for p in all_vps if p.vendor_id == vendor_id), None)

        if not vp:
            return {"error": "Vendor has no catalog product for request category"}

        res = ComplianceService.evaluate_compliance(vendor, vp, request)
        return {
            "vendor_id": res.vendor_id,
            "is_compliant": res.is_compliant,
            "overall_status": res.overall_status,
            "checks": [c.model_dump() for c in res.checks],
            "failed_reasons": res.failed_reasons,
        }
    finally:
        db.close()


def calculate_quote_total(
    unit_price: float,
    quantity: int,
    discount_rules: Optional[Dict[str, Any]] = None,
    budget_limit: Optional[float] = None
) -> Dict[str, Any]:
    """Deterministically calculate base subtotal, bulk discounts, 18% GST, shipping, effective unit price, and grand total."""
    b_limit = Decimal(str(budget_limit)) if budget_limit else None
    breakdown = PricingService.calculate_quote_breakdown(
        unit_price=Decimal(str(unit_price)),
        quantity=quantity,
        discount_rules=discount_rules,
        budget_limit=b_limit
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
        "effective_unit_price": float(breakdown.effective_unit_price),
        "budget_utilization_percentage": float(breakdown.budget_utilization_percentage) if breakdown.budget_utilization_percentage else None,
        "remaining_budget": float(breakdown.remaining_budget) if breakdown.remaining_budget else None
    }


def validate_budget(total_cost: float, budget_limit: float) -> Dict[str, Any]:
    """Deterministically compare total quote cost against approved budget ceiling and assign required approval level."""
    res = BudgetService.validate_budget(Decimal(str(total_cost)), Decimal(str(budget_limit)))
    return {
        "is_valid": res.is_valid,
        "budget_status": res.budget_status,
        "budget_limit": float(res.budget_limit),
        "total_cost": float(res.total_cost),
        "difference": float(res.difference),
        "overrun_amount": float(res.overrun_amount),
        "required_approval_level": res.required_approval_level,
        "explanation": res.explanation,
    }


def get_procurement_policies() -> List[Dict[str, Any]]:
    """Retrieve active corporate procurement policies, threshold limits, and mandatory requirements."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        policies = repo.get_all_policies()
        return [
            {
                "policy_id": p.policy_id,
                "policy_code": p.policy_code,
                "policy_name": p.policy_name,
                "category": p.category,
                "threshold_amount": float(p.threshold_amount),
                "mandatory_certifications": p.mandatory_certifications,
                "min_warranty_months": p.min_warranty_months,
                "max_delivery_days": p.max_delivery_days,
                "requires_finance_review": p.requires_finance_review,
            }
            for p in policies
        ]
    finally:
        db.close()


def save_procurement_request(
    requester: str,
    raw_request_text: str,
    category: str,
    quantity: int,
    budget_limit: float,
    delivery_deadline_days: int = 14,
    warranty_requirement_months: int = 24
) -> Dict[str, Any]:
    """Save an incoming purchase request to the relational MySQL database."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        req = repo.create_purchase_request(
            requester=requester,
            raw_request_text=raw_request_text,
            product_requirements={"category": category},
            quantity=quantity,
            budget_limit=Decimal(str(budget_limit)),
            delivery_deadline_days=delivery_deadline_days,
            warranty_requirement_months=warranty_requirement_months
        )
        return {
            "request_id": req.request_id,
            "requester": req.requester,
            "status": req.status,
            "quantity": req.quantity,
            "budget_limit": float(req.budget_limit)
        }
    finally:
        db.close()


def get_procurement_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve purchase request details from MySQL by request ID."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        req = repo.get_purchase_request(request_id)
        if not req:
            return None
        return {
            "request_id": req.request_id,
            "requester": req.requester,
            "raw_request_text": req.raw_request_text,
            "product_requirements": req.product_requirements,
            "quantity": req.quantity,
            "budget_limit": float(req.budget_limit),
            "currency": req.currency,
            "delivery_deadline_days": req.delivery_deadline_days,
            "warranty_requirement_months": req.warranty_requirement_months,
            "status": req.status,
            "created_at": req.created_at.isoformat()
        }
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        ev = repo.save_evaluation(
            request_id=request_id,
            quote_id=quote_id,
            price_score=Decimal(str(price_score)),
            delivery_score=Decimal(str(delivery_score)),
            warranty_score=Decimal(str(warranty_score)),
            compliance_score=Decimal(str(compliance_score)),
            specification_score=Decimal(str(specification_score)),
            final_score=Decimal(str(final_score)),
            eligibility_status=eligibility_status,
            explanation=explanation,
            exclusion_reason=exclusion_reason,
            rank=rank
        )
        return {
            "evaluation_id": ev.evaluation_id,
            "final_score": float(ev.final_score),
            "eligibility_status": ev.eligibility_status,
            "rank": ev.rank
        }
    finally:
        db.close()


def record_procurement_audit_event(
    action: str,
    actor: str,
    request_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Record an immutable audit log entry in MySQL."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        log_entry = repo.log_procurement_audit(
            action=action,
            actor=actor,
            request_id=request_id,
            actor_role=actor_role,
            details=details
        )
        return {
            "audit_id": log_entry.audit_id,
            "action": log_entry.action,
            "timestamp": log_entry.timestamp.isoformat()
        }
    finally:
        db.close()


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
            "original_amount": float(neg.original_amount),
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
    """Record a formal approval requirement in MySQL and pause workflow for human decision."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        approval = repo.create_approval(
            request_id=request_id,
            quote_id=quote_id,
            risk_assessment=risk_assessment,
            approval_reason=approval_reason,
            requested_by=requested_by,
        )
        return {
            "approval_id": approval.approval_id,
            "status": approval.decision,
            "requested_by": approval.requested_by,
        }
    finally:
        db.close()


def record_approval_decision(
    approval_id: str,
    decision: str,
    decided_by: str,
    comments: Optional[str] = None
) -> Dict[str, Any]:
    """Record an authorized human approval or rejection decision."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        appr = repo.get_approval_by_id(approval_id)
        if not appr:
            return {"error": "Approval request not found"}
        if appr.decision != "PENDING":
            return {"error": f"Approval already finalized as {appr.decision}"}

        appr.decision = decision.upper()
        appr.decided_by = decided_by
        appr.comments = comments
        appr.decided_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        return {
            "approval_id": appr.approval_id,
            "decision": appr.decision,
            "decided_by": appr.decided_by,
            "decided_at": appr.decided_at.isoformat()
        }
    finally:
        db.close()


def create_purchase_order(
    request_id: str,
    vendor_id: str,
    quote_id: str,
    approved_total: float,
    approved_by: str,
) -> Dict[str, Any]:
    """Deterministically issue a formal Purchase Order after validations and approvals pass."""
    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        po = repo.create_purchase_order(
            request_id=request_id,
            vendor_id=vendor_id,
            quote_id=quote_id,
            approved_total=Decimal(str(approved_total)),
            approved_by=approved_by,
        )
        return {
            "purchase_order_id": po.purchase_order_id,
            "order_number": po.order_number,
            "approved_total": float(po.approved_total),
            "status": po.status,
        }
    finally:
        db.close()
