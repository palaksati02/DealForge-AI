import pytest
from decimal import Decimal
from app.services.pricing_service import PricingService
from app.services.budget_service import BudgetService
from app.services.compliance_service import ComplianceService
from app.services.evaluation_service import EvaluationService
from app.services.approval_service import ApprovalService
from app.services.purchase_order_service import PurchaseOrderService
from app.services.replanning_service import ReplanningService
from app.services.negotiation_service import NegotiationService
from app.db.models.entities import Vendor, VendorProduct, PurchaseRequest, VendorQuote, VendorCertification
from app.schemas.schemas import PurchaseRequestExtract


def test_pricing_calculation_exact_decimal():
    # 50 units @ ₹68,000 with 8% discount
    discount_rules = {"tiers": [{"min_qty": 20, "discount_pct": 5.0}, {"min_qty": 50, "discount_pct": 8.0}]}
    breakdown = PricingService.calculate_quote_breakdown(
        unit_price=Decimal("68000.00"),
        quantity=50,
        discount_rules=discount_rules,
        apply_shipping=True,
        budget_limit=Decimal("4000000.00")
    )

    # Base subtotal: 50 * 68,000 = 3,400,000
    assert breakdown.base_subtotal == Decimal("3400000.00")
    # Discount: 8% of 3,400,000 = 272,000
    assert breakdown.discount_amount == Decimal("272000.00")
    # Taxable: 3,400,000 - 272,000 = 3,128,000
    assert breakdown.taxable_amount == Decimal("3128000.00")
    # 18% GST: 3,128,000 * 0.18 = 563,040
    assert breakdown.tax_amount == Decimal("563040.00")
    # Shipping: 5000 + (100 * 50) = 10,000
    assert breakdown.shipping_cost == Decimal("10000.00")
    # Total: 3,128,000 + 563,040 + 10,000 = 3,701,040.00
    assert breakdown.final_total == Decimal("3701040.00")
    # Effective unit price = 3,701,040 / 50 = 74,020.80
    assert breakdown.effective_unit_price == Decimal("74020.80")
    # Budget utilization: (3,701,040 / 4,000,000) * 100 = 92.53%
    assert breakdown.budget_utilization_percentage == Decimal("92.53")
    assert breakdown.remaining_budget == Decimal("298960.00")


def test_pricing_zero_quantity_and_negative_price():
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        PricingService.calculate_quote_breakdown(unit_price=Decimal("1000.00"), quantity=0)

    with pytest.raises(ValueError, match="Unit price must be positive"):
        PricingService.calculate_quote_breakdown(unit_price=Decimal("-50.00"), quantity=10)


def test_budget_validation_pass_and_overrun():
    # Pass scenario
    res_pass = BudgetService.validate_budget(Decimal("3200000.00"), Decimal("3500000.00"))
    assert res_pass.is_valid is True
    assert res_pass.budget_status == "COMPLIANT_WITHIN_BUDGET"
    assert res_pass.difference == Decimal("300000.00")
    assert res_pass.overrun_amount == Decimal("0.00")
    assert res_pass.required_approval_level in ["PROCUREMENT_MANAGER", "FINANCE_REVIEWER"]

    # Boundary scenario (exact match)
    res_exact = BudgetService.validate_budget(Decimal("3500000.00"), Decimal("3500000.00"))
    assert res_exact.is_valid is True
    assert res_exact.difference == Decimal("0.00")
    assert res_exact.overrun_amount == Decimal("0.00")

    # Overrun scenario
    res_fail = BudgetService.validate_budget(Decimal("3620000.00"), Decimal("3500000.00"))
    assert res_fail.is_valid is False
    assert res_fail.budget_status == "BUDGET_OVERRUN"
    assert res_fail.difference == Decimal("-120000.00")
    assert res_fail.overrun_amount == Decimal("120000.00")
    assert res_fail.required_approval_level == "EXECUTIVE_ESCALATION"
    assert "BUDGET OVERRUN DETECTED" in res_fail.explanation


def test_compliance_rules_pass_fail_unknown(db_session, repo):
    request = repo.create_purchase_request(
        requester="Audit Officer",
        raw_request_text="Need 50 laptops with 24 months warranty within 14 days and ISO 9001 certification",
        product_requirements={"category": "Laptops", "mandatory_certifications": ["ISO 9001"]},
        quantity=50,
        budget_limit=Decimal("3500000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24,
    )

    # 1. Compliant winner: Nexus (Active, 36m warranty, in-stock 120, 10d delivery, ISO 9001 verified)
    nexus = repo.get_vendor_by_id("vend-nexus-01")
    vp_nexus = repo.get_vendor_product(nexus.vendor_id, "prod-laptop-01")
    res_nexus = ComplianceService.evaluate_compliance(nexus, vp_nexus, request, mandatory_certifications=["ISO 9001"])
    assert res_nexus.is_compliant is True
    assert res_nexus.overall_status == "PASS"
    assert all(c.status == "PASS" for c in res_nexus.checks)

    # 2. Inactive vendor: Legacy Hardware (FAILS active check)
    legacy = repo.get_vendor_by_id("vend-legacy-07")
    vp_legacy = repo.get_vendor_product(legacy.vendor_id, "prod-laptop-01")
    res_legacy = ComplianceService.evaluate_compliance(legacy, vp_legacy, request)
    assert res_legacy.is_compliant is False
    assert res_legacy.overall_status == "FAIL"
    assert any(c.status == "FAIL" and c.rule_type == "VENDOR_ACTIVE" for c in res_legacy.checks)

    # 3. Non-compliant warranty: Zenith (12 months vs 24 required -> FAILS warranty check)
    zenith = repo.get_vendor_by_id("vend-zenith-03")
    vp_zenith = repo.get_vendor_product(zenith.vendor_id, "prod-laptop-01")
    res_zenith = ComplianceService.evaluate_compliance(zenith, vp_zenith, request)
    assert res_zenith.is_compliant is False
    assert res_zenith.overall_status == "FAIL"
    assert any(c.status == "FAIL" and c.rule_type == "MIN_WARRANTY" for c in res_zenith.checks)

    # 4. Unknown/Missing certification: Stellar (status is UNKNOWN, must NOT pass!)
    stellar = repo.get_vendor_by_id("vend-stellar-09")
    vp_stellar = repo.get_vendor_product(stellar.vendor_id, "prod-laptop-01")
    res_stellar = ComplianceService.evaluate_compliance(stellar, vp_stellar, request, mandatory_certifications=["ISO 9001"])
    assert res_stellar.is_compliant is False
    assert res_stellar.overall_status in ["UNKNOWN", "FAIL"]
    assert any(c.status == "UNKNOWN" for c in res_stellar.checks)


def test_deal_evaluation_and_ineligible_exclusion(db_session, repo):
    request = repo.create_purchase_request(
        requester="Audit Officer",
        raw_request_text="Need 50 laptops with 24 months warranty within 14 days",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24,
    )

    q1 = repo.create_quote(
        request_id=request.request_id,
        vendor_id="vend-nexus-01",
        unit_price=Decimal("68000.00"),
        quantity=50,
        discount=Decimal("272000.00"),
        tax=Decimal("563040.00"),
        shipping_cost=Decimal("10000.00"),
        total_amount=Decimal("3701040.00"),
        delivery_days=10,
        warranty_months=36,
        availability_status="IN_STOCK",
        calculation_breakdown={},
    )
    q_ineligible = repo.create_quote(
        request_id=request.request_id,
        vendor_id="vend-legacy-07",
        unit_price=Decimal("50000.00"),  # Cheap but inactive
        quantity=50,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        shipping_cost=Decimal("0.00"),
        total_amount=Decimal("2500000.00"),
        delivery_days=10,
        warranty_months=24,
        availability_status="IN_STOCK",
        calculation_breakdown={},
    )

    compliance_results = {
        "vend-nexus-01": ComplianceService.evaluate_compliance(
            repo.get_vendor_by_id("vend-nexus-01"),
            repo.get_vendor_product("vend-nexus-01", "prod-laptop-01"),
            request
        ),
        "vend-legacy-07": ComplianceService.evaluate_compliance(
            repo.get_vendor_by_id("vend-legacy-07"),
            repo.get_vendor_product("vend-legacy-07", "prod-laptop-01"),
            request
        ),
    }

    evals = EvaluationService.evaluate_all_quotes([q1, q_ineligible], request, compliance_results)

    eval_legacy = next(e for e in evals if e["vendor_id"] == "vend-legacy-07")
    eval_nexus = next(e for e in evals if e["vendor_id"] == "vend-nexus-01")

    assert eval_legacy["eligibility_status"] == "INELIGIBLE"
    assert eval_legacy["rank"] is None
    assert eval_nexus["eligibility_status"] == "ELIGIBLE"
    assert eval_nexus["rank"] == 1


def test_tie_breaking_logic(db_session, repo):
    request = repo.create_purchase_request(
        requester="Procurement VP",
        raw_request_text="50 laptops",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("5000000.00"),
        delivery_deadline_days=14,
        warranty_requirement_months=24,
    )

    # Two quotes with identical terms, but Vendor A has lower total price
    q_a = repo.create_quote(
        request_id=request.request_id,
        vendor_id="vend-nexus-01",
        unit_price=Decimal("68000.00"),
        quantity=50,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        shipping_cost=Decimal("0.00"),
        total_amount=Decimal("3400000.00"),  # Cheaper
        delivery_days=10,
        warranty_months=36,
        availability_status="IN_STOCK",
        calculation_breakdown={},
    )
    q_b = repo.create_quote(
        request_id=request.request_id,
        vendor_id="vend-apex-02",
        unit_price=Decimal("70000.00"),
        quantity=50,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        shipping_cost=Decimal("0.00"),
        total_amount=Decimal("3500000.00"),  # More expensive
        delivery_days=10,
        warranty_months=36,
        availability_status="IN_STOCK",
        calculation_breakdown={},
    )

    comp_map = {
        "vend-nexus-01": ComplianceService.evaluate_compliance(repo.get_vendor_by_id("vend-nexus-01"), repo.get_vendor_product("vend-nexus-01", "prod-laptop-01"), request),
        "vend-apex-02": ComplianceService.evaluate_compliance(repo.get_vendor_by_id("vend-apex-02"), repo.get_vendor_product("vend-apex-02", "prod-laptop-01"), request),
    }

    evals = EvaluationService.evaluate_all_quotes([q_a, q_b], request, comp_map)
    rank_1 = next(e for e in evals if e["rank"] == 1)
    assert rank_1["vendor_id"] == "vend-nexus-01"


def test_negotiation_bounds():
    # Original quotation: ₹37,01,040, budget: ₹35,00,000, qty: 50
    bounds = NegotiationService.calculate_negotiation_bounds(
        original_amount=Decimal("3701040.00"),
        budget_limit=Decimal("3500000.00"),
        quantity=50,
        target_discount_pct=Decimal("0.05")
    )

    # 5% discount on 3,701,040 is 185,052 -> 3,515,988. Capped at budget 3,500,000
    assert bounds.target_price == Decimal("3500000.00")
    assert bounds.maximum_acceptable_price == Decimal("3500000.00")
    assert bounds.estimated_savings == Decimal("201040.00")
    assert bounds.is_estimate is True
    assert "Estimated non-committed savings" in bounds.justification


def test_purchase_order_generation_and_idempotency(db_session, repo):
    request = repo.create_purchase_request(
        requester="Procurement VP",
        raw_request_text="50 laptops",
        product_requirements={"category": "Laptops"},
        quantity=50,
        budget_limit=Decimal("3800000.00"),
    )
    quote = repo.create_quote(
        request_id=request.request_id,
        vendor_id="vend-nexus-01",
        unit_price=Decimal("68000.00"),
        quantity=50,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        shipping_cost=Decimal("0.00"),
        total_amount=Decimal("3400000.00"),
        delivery_days=10,
        warranty_months=36,
        availability_status="IN_STOCK",
        calculation_breakdown={},
    )
    repo.save_evaluation(
        request_id=request.request_id,
        quote_id=quote.quote_id,
        price_score=Decimal("100.00"),
        delivery_score=Decimal("90.00"),
        warranty_score=Decimal("100.00"),
        compliance_score=Decimal("100.00"),
        specification_score=Decimal("100.00"),
        final_score=Decimal("98.00"),
        eligibility_status="ELIGIBLE",
        explanation="Best vendor",
        rank=1
    )

    # Issue PO
    po1 = PurchaseOrderService.generate_purchase_order(
        db=db_session,
        request_id=request.request_id,
        approved_by="Procurement VP"
    )
    assert po1 is not None
    assert po1.order_number.startswith("PO-DF-")

    # Idempotency check: calling again returns the same PO
    po2 = PurchaseOrderService.generate_purchase_order(
        db=db_session,
        request_id=request.request_id,
        approved_by="Procurement VP"
    )
    assert po1.purchase_order_id == po2.purchase_order_id
    assert po1.order_number == po2.order_number
