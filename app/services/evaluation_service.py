from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.schemas import EvaluationResponse
from app.db.models.entities import VendorQuote, Vendor, VendorProduct, PurchaseRequest


class EvaluationService:
    """
    Deterministic Deal Evaluation and Multi-Criteria Ranking Engine.
    Combines weighted criteria: Price, Delivery SLA, Warranty, Compliance, Specifications.
    Enforces that weights sum to 1.0, applies mandatory eligibility gates,
    and breaks ties deterministically.
    """

    @classmethod
    def validate_scoring_weights(cls) -> None:
        total = (
            settings.WEIGHT_PRICE
            + settings.WEIGHT_DELIVERY
            + settings.WEIGHT_WARRANTY
            + settings.WEIGHT_COMPLIANCE
            + settings.WEIGHT_SPECIFICATION
        )
        if abs(total - Decimal("1.00")) > Decimal("0.001"):
            raise ValueError(f"Scoring weights must sum to exactly 1.00; current sum is {total}")

    @classmethod
    def calculate_price_score(cls, quote_total: Decimal, lowest_quote_total: Decimal) -> Decimal:
        if quote_total <= Decimal("0.00") or lowest_quote_total <= Decimal("0.00"):
            return Decimal("0.00")
        score = (lowest_quote_total / quote_total) * Decimal("100.00")
        return min(Decimal("100.00"), score).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_delivery_score(cls, delivery_days: int, deadline_days: int) -> Decimal:
        if delivery_days <= 0:
            return Decimal("100.00")
        if delivery_days > deadline_days:
            return Decimal("0.00")
        margin = max(1, deadline_days - 1)
        ratio = (deadline_days - delivery_days) / margin
        score = Decimal("60.00") + (Decimal(str(ratio)) * Decimal("40.00"))
        return min(Decimal("100.00"), max(Decimal("0.00"), score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_warranty_score(cls, warranty_months: int, required_months: int) -> Decimal:
        if warranty_months < required_months:
            return Decimal("0.00")
        base_score = (Decimal(warranty_months) / Decimal("36.00")) * Decimal("100.00")
        return min(Decimal("100.00"), max(Decimal("0.00"), base_score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def evaluate_all_quotes(
        cls,
        quotes: List[VendorQuote],
        request: PurchaseRequest,
        compliance_results: Dict[str, Any],  # vendor_id -> ComplianceValidationResult
    ) -> List[Dict[str, Any]]:
        if not quotes:
            return []

        cls.validate_scoring_weights()

        budget_limit = request.budget_limit or Decimal("10000000.00")

        # Find lowest price among COMPLIANT quotes within budget
        eligible_totals = []
        for q in quotes:
            comp = compliance_results.get(q.vendor_id)
            is_comp = getattr(comp, "is_compliant", True)
            is_within_budget = q.total_amount <= budget_limit
            if is_comp and is_within_budget:
                eligible_totals.append(q.total_amount)

        min_total = min(eligible_totals) if eligible_totals else min(q.total_amount for q in quotes)

        evaluations = []
        deadline_days = request.delivery_deadline_days or 14
        required_warranty = request.warranty_requirement_months or 24

        for q in quotes:
            comp = compliance_results.get(q.vendor_id)
            is_compliant = getattr(comp, "is_compliant", True)
            failed_reasons = getattr(comp, "failed_reasons", [])
            exclusion_reasons = list(failed_reasons)

            # Strict Budget Limit check: quote above budget cannot be eligible
            is_within_budget = q.total_amount <= budget_limit
            if not is_within_budget:
                overrun = q.total_amount - budget_limit
                exclusion_reasons.append(f"Quote total ₹{q.total_amount:,.2f} exceeds budget limit ₹{budget_limit:,.2f} by ₹{overrun:,.2f}")

            # 1. Price Score
            price_score = cls.calculate_price_score(q.total_amount, min_total)

            # 2. Delivery Score
            delivery_score = cls.calculate_delivery_score(q.delivery_days, deadline_days)

            # 3. Warranty Score
            warranty_score = cls.calculate_warranty_score(q.warranty_months, required_warranty)

            # 4. Compliance Score
            compliance_score = Decimal("100.00") if is_compliant else Decimal("0.00")

            # 5. Specification Score
            specification_score = Decimal("95.00")

            # Eligibility gating
            if not is_compliant or not is_within_budget:
                eligibility_status = "INELIGIBLE"
                final_score = Decimal("0.00")
                explanation = f"Disqualified: {'; '.join(exclusion_reasons)}."
            else:
                eligibility_status = "ELIGIBLE"
                final_score = (
                    (price_score * settings.WEIGHT_PRICE)
                    + (delivery_score * settings.WEIGHT_DELIVERY)
                    + (warranty_score * settings.WEIGHT_WARRANTY)
                    + (compliance_score * settings.WEIGHT_COMPLIANCE)
                    + (specification_score * settings.WEIGHT_SPECIFICATION)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                explanation = (
                    f"Eligible: Final Score {final_score}/100.00 (Price: {price_score}, Delivery: {delivery_score}, "
                    f"Warranty: {warranty_score}, Compliance: {compliance_score}, Specs: {specification_score})."
                )

            vendor_rating = Decimal(str(getattr(q.vendor, "vendor_rating", 4.0))) if getattr(q, "vendor", None) else Decimal("4.00")

            evaluations.append({
                "quote_id": q.quote_id,
                "vendor_id": q.vendor_id,
                "price_score": price_score,
                "delivery_score": delivery_score,
                "warranty_score": warranty_score,
                "compliance_score": compliance_score,
                "specification_score": specification_score,
                "final_score": final_score,
                "eligibility_status": eligibility_status,
                "exclusion_reason": "; ".join(exclusion_reasons) if exclusion_reasons else None,
                "explanation": explanation,
                # Tie-breaking metadata
                "total_amount": q.total_amount,
                "delivery_days": q.delivery_days,
                "vendor_rating": vendor_rating,
            })

        # Rank eligible quotes with deterministic tie-breaking:
        # 1. final_score descending
        # 2. total_amount ascending (lower price wins)
        # 3. delivery_days ascending (faster delivery wins)
        # 4. vendor_rating descending (higher rating wins)
        eligible_evals = [e for e in evaluations if e["eligibility_status"] == "ELIGIBLE"]
        eligible_evals.sort(
            key=lambda x: (-x["final_score"], x["total_amount"], x["delivery_days"], -x["vendor_rating"])
        )
        for rank, e in enumerate(eligible_evals, start=1):
            e["rank"] = rank

        ineligible_evals = [e for e in evaluations if e["eligibility_status"] == "INELIGIBLE"]
        for e in ineligible_evals:
            e["rank"] = None

        return eligible_evals + ineligible_evals
