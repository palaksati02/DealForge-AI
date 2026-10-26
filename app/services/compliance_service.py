from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.schemas.schemas import ComplianceValidationResult, ComplianceCheckItem
from app.db.models.entities import Vendor, VendorProduct, PurchaseRequest


class ComplianceService:
    """
    Deterministic compliance enforcement engine.
    Applies non-negotiable procurement policies to vendors and quotations.
    Evaluates every criterion to explicit PASS, FAIL, or UNKNOWN statuses.
    Missing data must never become a pass.
    """

    @classmethod
    def evaluate_compliance(
        cls,
        vendor: Vendor,
        vendor_product: VendorProduct,
        request: PurchaseRequest,
        mandatory_certifications: Optional[List[str]] = None,
    ) -> ComplianceValidationResult:
        checks: List[ComplianceCheckItem] = []
        failed_reasons: List[str] = []
        has_unknown = False

        # 1. Vendor Active Status Check (Mandatory)
        if vendor.active_status is None:
            active_status = "UNKNOWN"
            has_unknown = True
            checks.append(
                ComplianceCheckItem(
                    rule_name="Active Vendor Directory Verification",
                    rule_type="VENDOR_ACTIVE",
                    status="UNKNOWN",
                    passed=False,
                    mandatory=True,
                    details="Vendor directory status is unknown or unverified in database.",
                )
            )
            failed_reasons.append(f"Vendor '{vendor.vendor_name}' active status is UNKNOWN.")
        elif vendor.active_status:
            checks.append(
                ComplianceCheckItem(
                    rule_name="Active Vendor Directory Verification",
                    rule_type="VENDOR_ACTIVE",
                    status="PASS",
                    passed=True,
                    mandatory=True,
                    details="Vendor status is confirmed ACTIVE in corporate ERP directory.",
                )
            )
        else:
            checks.append(
                ComplianceCheckItem(
                    rule_name="Active Vendor Directory Verification",
                    rule_type="VENDOR_ACTIVE",
                    status="FAIL",
                    passed=False,
                    mandatory=True,
                    details="Vendor status is confirmed INACTIVE in corporate ERP directory.",
                )
            )
            failed_reasons.append(f"Vendor '{vendor.vendor_name}' is currently flagged as INACTIVE in vendor registry.")

        # 2. Minimum Warranty Check (Mandatory)
        req_warranty = request.warranty_requirement_months or 24
        supplied_warranty = vendor_product.warranty_months
        if supplied_warranty is None:
            has_unknown = True
            checks.append(
                ComplianceCheckItem(
                    rule_name="Minimum Mandatory Warranty Duration",
                    rule_type="MIN_WARRANTY",
                    status="UNKNOWN",
                    passed=False,
                    mandatory=True,
                    details="Supplied warranty duration is missing or unverified.",
                )
            )
            failed_reasons.append("Warranty duration is UNKNOWN.")
        elif supplied_warranty >= req_warranty:
            checks.append(
                ComplianceCheckItem(
                    rule_name="Minimum Mandatory Warranty Duration",
                    rule_type="MIN_WARRANTY",
                    status="PASS",
                    passed=True,
                    mandatory=True,
                    details=f"Supplied warranty: {supplied_warranty} months exceeds required {req_warranty} months.",
                )
            )
        else:
            checks.append(
                ComplianceCheckItem(
                    rule_name="Minimum Mandatory Warranty Duration",
                    rule_type="MIN_WARRANTY",
                    status="FAIL",
                    passed=False,
                    mandatory=True,
                    details=f"Supplied warranty: {supplied_warranty} months is below required threshold of {req_warranty} months.",
                )
            )
            failed_reasons.append(
                f"Warranty duration of {supplied_warranty} months is below required threshold of {req_warranty} months."
            )

        # 3. Delivery Deadline Check (Mandatory)
        req_deadline = request.delivery_deadline_days or 14
        promised_delivery = vendor_product.delivery_days
        if promised_delivery is None:
            has_unknown = True
            checks.append(
                ComplianceCheckItem(
                    rule_name="Delivery SLA Adherence",
                    rule_type="MAX_DELIVERY",
                    status="UNKNOWN",
                    passed=False,
                    mandatory=True,
                    details="Promised delivery timeline is missing.",
                )
            )
            failed_reasons.append("Delivery timeline is UNKNOWN.")
        elif promised_delivery <= req_deadline:
            checks.append(
                ComplianceCheckItem(
                    rule_name="Delivery SLA Adherence",
                    rule_type="MAX_DELIVERY",
                    status="PASS",
                    passed=True,
                    mandatory=True,
                    details=f"Vendor lead time: {promised_delivery} days is within maximum allowed {req_deadline} days.",
                )
            )
        else:
            checks.append(
                ComplianceCheckItem(
                    rule_name="Delivery SLA Adherence",
                    rule_type="MAX_DELIVERY",
                    status="FAIL",
                    passed=False,
                    mandatory=True,
                    details=f"Vendor lead time: {promised_delivery} days exceeds mandatory deadline of {req_deadline} days.",
                )
            )
            failed_reasons.append(
                f"Delivery timeline of {promised_delivery} days exceeds mandatory deadline of {req_deadline} days."
            )

        # 4. Inventory Stock Sufficiency Check (Mandatory)
        req_qty = request.quantity
        available_stock = vendor_product.stock_quantity
        if available_stock is None:
            has_unknown = True
            checks.append(
                ComplianceCheckItem(
                    rule_name="On-Hand Inventory Availability",
                    rule_type="STOCK_AVAILABILITY",
                    status="UNKNOWN",
                    passed=False,
                    mandatory=True,
                    details="Inventory stock quantity is missing in catalog.",
                )
            )
            failed_reasons.append("Inventory stock quantity is UNKNOWN.")
        elif available_stock >= req_qty:
            checks.append(
                ComplianceCheckItem(
                    rule_name="On-Hand Inventory Availability",
                    rule_type="STOCK_AVAILABILITY",
                    status="PASS",
                    passed=True,
                    mandatory=True,
                    details=f"Available on-hand: {available_stock} units fulfills required order quantity of {req_qty} units.",
                )
            )
        else:
            checks.append(
                ComplianceCheckItem(
                    rule_name="On-Hand Inventory Availability",
                    rule_type="STOCK_AVAILABILITY",
                    status="FAIL",
                    passed=False,
                    mandatory=True,
                    details=f"Available on-hand: {available_stock} units is insufficient for required {req_qty} units.",
                )
            )
            failed_reasons.append(
                f"Insufficient stock ({available_stock} units available) to fulfill order quantity of {req_qty} units."
            )

        # 5. Mandatory Certifications Check
        req_certs = mandatory_certifications or (
            request.product_requirements.get("mandatory_certifications", [])
            if request.product_requirements
            else []
        )
        if req_certs:
            vendor_certs = {c.certification_name: c.verification_status for c in getattr(vendor, "certifications", [])}
            cert_pass = True
            cert_unknown = False
            missing_or_failed = []

            for rc in req_certs:
                v_status = vendor_certs.get(rc)
                if not v_status or v_status == "UNKNOWN":
                    cert_unknown = True
                    cert_pass = False
                    missing_or_failed.append(f"{rc} (UNKNOWN/MISSING)")
                elif v_status != "VERIFIED":
                    cert_pass = False
                    missing_or_failed.append(f"{rc} ({v_status})")

            if cert_pass:
                checks.append(
                    ComplianceCheckItem(
                        rule_name="Enterprise Certification Audit",
                        rule_type="CERTIFICATION_CHECK",
                        status="PASS",
                        passed=True,
                        mandatory=True,
                        details=f"All required certifications verified: {', '.join(req_certs)}.",
                    )
                )
            elif cert_unknown:
                has_unknown = True
                checks.append(
                    ComplianceCheckItem(
                        rule_name="Enterprise Certification Audit",
                        rule_type="CERTIFICATION_CHECK",
                        status="UNKNOWN",
                        passed=False,
                        mandatory=True,
                        details=f"Required certifications have unverified or unknown status: {', '.join(missing_or_failed)}.",
                    )
                )
                failed_reasons.append(f"Certification status is UNKNOWN for {', '.join(missing_or_failed)}.")
            else:
                checks.append(
                    ComplianceCheckItem(
                        rule_name="Enterprise Certification Audit",
                        rule_type="CERTIFICATION_CHECK",
                        status="FAIL",
                        passed=False,
                        mandatory=True,
                        details=f"Required certifications failed verification: {', '.join(missing_or_failed)}.",
                    )
                )
                failed_reasons.append(f"Vendor failed required certifications: {', '.join(missing_or_failed)}.")

        # Determine overall compliance status
        if failed_reasons:
            if any("UNKNOWN" in r for r in failed_reasons) and not any("INACTIVE" in r or "below required" in r or "exceeds" in r or "Insufficient" in r for r in failed_reasons):
                overall_status = "UNKNOWN"
            else:
                overall_status = "FAIL"
            is_compliant = False
        else:
            overall_status = "PASS"
            is_compliant = True

        return ComplianceValidationResult(
            vendor_id=vendor.vendor_id,
            is_compliant=is_compliant,
            overall_status=overall_status,
            checks=checks,
            failed_reasons=failed_reasons,
        )
