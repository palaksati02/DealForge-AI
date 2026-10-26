from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.repositories.procurement_repo import ProcurementRepository
from app.db.models.entities import PurchaseOrder, PurchaseRequest, VendorQuote


class PurchaseOrderService:
    """
    Deterministic Purchase Order service.
    Guarantees strict auditability, transactionality, and idempotency.
    A Purchase Order cannot be created without validation.
    """

    @classmethod
    def generate_purchase_order(
        cls,
        db: Session,
        request_id: str,
        approved_by: str,
        override_total: Optional[Decimal] = None
    ) -> PurchaseOrder:
        repo = ProcurementRepository(db)
        request = repo.get_purchase_request(request_id)
        if not request:
            raise ValueError(f"Purchase request {request_id} does not exist.")

        # Check existing PO (idempotency)
        existing_po = repo.get_purchase_order_by_request(request_id)
        if existing_po:
            return existing_po

        # Find top ranked evaluation / selected quote
        evals = repo.get_evaluations_by_request(request_id)
        if not evals:
            raise ValueError("Cannot issue Purchase Order: No evaluations exist for this request.")

        eligible_evals = [e for e in evals if e.eligibility_status == "ELIGIBLE"]
        if not eligible_evals:
            raise ValueError("Cannot issue Purchase Order: No eligible vendors found.")

        best_eval = eligible_evals[0]
        quote = repo.get_quote_by_id(best_eval.quote_id)
        if not quote:
            raise ValueError("Winning quote record not found.")

        # Determine approved total
        final_total = override_total if override_total is not None else quote.total_amount

        # Check approval status if request was pending approval
        approvals = [a for a in request.approvals if a.quote_id == quote.quote_id]
        if approvals:
            latest_approval = approvals[-1]
            if latest_approval.decision != "APPROVED" and request.status != "APPROVED":
                raise ValueError(f"Cannot issue Purchase Order: Approval is {latest_approval.decision}, not APPROVED.")

        # Build comprehensive order details
        order_details = {
            "request_id": request.request_id,
            "requester": request.requester,
            "product_requirements": request.product_requirements,
            "quantity": request.quantity,
            "unit_price": float(quote.unit_price),
            "discount": float(quote.discount),
            "tax": float(quote.tax),
            "shipping_cost": float(quote.shipping_cost),
            "total_amount": float(final_total),
            "currency": request.currency,
            "delivery_days": quote.delivery_days,
            "warranty_months": quote.warranty_months,
            "evaluation_rank": best_eval.rank,
            "evaluation_score": float(best_eval.final_score),
            "calculation_breakdown": quote.calculation_breakdown,
        }

        # Create PO
        po = repo.create_purchase_order(
            request_id=request.request_id,
            vendor_id=quote.vendor_id,
            quote_id=quote.quote_id,
            approved_total=final_total,
            approved_by=approved_by,
            currency=request.currency,
            order_details=order_details
        )

        # Update request status
        repo.update_purchase_request_status(request_id, "PO_CREATED")
        return po
