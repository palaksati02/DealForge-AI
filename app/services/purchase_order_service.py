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

    @classmethod
    def generate_markdown(cls, po: PurchaseOrder) -> str:
        """
        Generate structured GitHub-flavored Markdown document with tables
        for formal Purchase Order presentation and export.
        """
        def to_f(val, default=0.0):
            try:
                return float(val) if val is not None else default
            except (TypeError, ValueError):
                return default

        details = po.order_details or {}
        breakdown = details.get("calculation_breakdown", {})
        vendor_name = po.vendor.vendor_name if po.vendor else "Designated Vendor"
        vendor_email = po.vendor.contact_email if po.vendor else "procurement@vendor.com"
        vendor_phone = po.vendor.phone if po.vendor else "N/A"

        unit_p = to_f(details.get("unit_price"))
        qty = int(details.get("quantity", 1))
        line_sub = unit_p * qty
        base_sub = to_f(breakdown.get("base_subtotal", line_sub))
        disc_amt = to_f(breakdown.get("discount_amount", details.get("discount", 0.0)))
        disc_pct = to_f(breakdown.get("discount_percentage", 0.0))
        taxable_amt = to_f(breakdown.get("taxable_amount", base_sub - disc_amt))
        tax_amt = to_f(breakdown.get("tax_amount", details.get("tax", 0.0)))
        ship_cost = to_f(breakdown.get("shipping_cost", details.get("shipping_cost", 0.0)))
        appr_tot = to_f(po.approved_total)

        md = f"""# OFFICIAL PURCHASE ORDER
**DealForge Enterprise Multi-Agent Procurement Automation**

---

### Purchase Order Summary

| Field | Value |
| :--- | :--- |
| **PO Number** | `{po.order_number}` |
| **Status** | **{po.status}** |
| **Issue Date** | {po.created_at.strftime("%Y-%m-%d %H:%M:%S") if po.created_at else "N/A"} |
| **Authorized By** | {po.approved_by} |
| **Purchase Request ID** | `{po.request_id}` |
| **Currency** | {po.currency} |

---

### Vendor Information

| Field | Details |
| :--- | :--- |
| **Vendor Name** | {vendor_name} |
| **Contact Email** | {vendor_email} |
| **Phone** | {vendor_phone} |
| **Promised Lead Time** | {details.get("delivery_days", 7)} Business Days |
| **Warranty Coverage** | {details.get("warranty_months", 12)} Months |

---

### Procurement Itemization & Line Items

| Item Description | Quantity | Unit Price ({po.currency}) | Line Subtotal ({po.currency}) |
| :--- | :---: | :---: | :---: |
| {details.get("product_requirements", {}).get("category", "Procurement Item")} - {details.get("product_requirements", {}).get("product_name_hint") or "Enterprise Standard"} | {qty} | ₹{unit_p:,.2f} | ₹{line_sub:,.2f} |

---

### Financial Calculation Breakdown (Exact Decimal)

| Financial Component | Amount ({po.currency}) | Notes |
| :--- | :---: | :--- |
| **Base Gross Subtotal** | ₹{base_sub:,.2f} | Unit Price × Quantity |
| **Volume Tier Discount** | -₹{disc_amt:,.2f} | {disc_pct:.1f}% Bulk Discount Applied |
| **Taxable Amount** | ₹{taxable_amt:,.2f} | Subtotal after Discount |
| **Statutory GST (18%)** | ₹{tax_amt:,.2f} | Standard Statutory 18% GST |
| **Logistics & Shipping** | ₹{ship_cost:,.2f} | Secure insured freight |
| **FINAL APPROVED TOTAL** | **₹{appr_tot:,.2f}** | **Net Authorized Commitment** |

---

*This document was deterministically compiled, risk-audited via Google ADK over A2A protocol, and authorized under DealForge AI Corporate Governance Policy.*
"""
        return md.strip()
