from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.schemas.schemas import ComplianceValidationResult, ComplianceCheckItem
from app.db.models.entities import Vendor, VendorProduct, PurchaseRequest


class ComplianceService:
    """
    Deterministic compliance enforcement engine.
    Applies non-negotiable procurement policies to vendors and quotations.
    """

    @classmethod
    def evaluate_compliance(
        cls,
        vendor: Vendor,
        vendor_product: VendorProduct,
        request: PurchaseRequest,
    ) -> ComplianceValidationResult:
        checks: List[ComplianceCheckItem] = []
        failed_reasons: List[str] = []

        # 1. Vendor Active Status Check (Mandatory)
        is_active = bool(vendor.active_status)
        checks.append(
            ComplianceCheckItem(
                rule_name="Active Vendor Directory Verification",
                rule_type="VENDOR_ACTIVE",
                passed=is_active,
                mandatory=True,
                details=f"Vendor status is {'ACTIVE' if is_active else 'INACTIVE'}.",
            )
        )
        if not is_active:
            failed_reasons.append(f"Vendor '{vendor.vendor_name}' is currently flagged as INACTIVE in vendor registry.")

        # 2. Minimum Warranty Check (Mandatory)
        req_warranty = request.warranty_requirement_months or 24
        supplied_warranty = vendor_product.warranty_months or 12
        warranty_passed = supplied_warranty >= req_warranty
        checks.append(
            ComplianceCheckItem(
                rule_name="Minimum Mandatory Warranty Duration",
                rule_type="MIN_WARRANTY",
                passed=warranty_passed,
                mandatory=True,
                details=f"Supplied warranty: {supplied_warranty} months, Required minimum: {req_warranty} months.",
            )
        )
        if not warranty_passed:
            failed_reasons.append(
                f"Warranty duration of {supplied_warranty} months is below required threshold of {req_warranty} months."
            )

        # 3. Delivery Deadline Check (Mandatory)
        req_deadline = request.delivery_deadline_days or 14
        promised_delivery = vendor_product.delivery_days or 7
        delivery_passed = promised_delivery <= req_deadline
        checks.append(
            ComplianceCheckItem(
                rule_name="Delivery SLA Adherence",
                rule_type="MAX_DELIVERY",
                passed=delivery_passed,
                mandatory=True,
                details=f"Vendor lead time: {promised_delivery} days, Maximum allowed deadline: {req_deadline} days.",
            )
        )
        if not delivery_passed:
            failed_reasons.append(
                f"Delivery timeline of {promised_delivery} days exceeds mandatory deadline of {req_deadline} days."
            )

        # 4. Inventory Stock Sufficiency Check (Mandatory)
        req_qty = request.quantity
        available_stock = vendor_product.stock_quantity or 0
        stock_passed = available_stock >= req_qty
        checks.append(
            ComplianceCheckItem(
                rule_name="On-Hand Inventory Availability",
                rule_type="STOCK_AVAILABILITY",
                passed=stock_passed,
                mandatory=True,
                details=f"Available on-hand: {available_stock} units, Required order quantity: {req_qty} units.",
            )
        )
        if not stock_passed:
            failed_reasons.append(
                f"Insufficient stock ({available_stock} units available) to fulfill order quantity of {req_qty} units."
            )

        # 5. Minimum Order Quantity (MOQ) Check
        moq = vendor_product.minimum_order_quantity or 1
        moq_passed = req_qty >= moq
        checks.append(
            ComplianceCheckItem(
                rule_name="Minimum Order Quantity (MOQ) Alignment",
                rule_type="MOQ_CHECK",
                passed=moq_passed,
                mandatory=True,
                details=f"Vendor MOQ: {moq} units, Requested quantity: {req_qty} units.",
            )
        )
        if not moq_passed:
            failed_reasons.append(f"Requested quantity {req_qty} is less than vendor MOQ of {moq} units.")

        # Overall compliance
        is_compliant = len(failed_reasons) == 0

        return ComplianceValidationResult(
            vendor_id=vendor.vendor_id,
            is_compliant=is_compliant,
            checks=checks,
            failed_reasons=failed_reasons,
        )
