from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from app.schemas.schemas import NegotiationBounds


class NegotiationService:
    """
    Deterministic negotiation policy engine.
    Calculates permitted target prices, maximum acceptable limits, and estimated savings.
    Guarantees that projected savings are marked as estimates and never treated as vendor commitments.
    """

    DEFAULT_TARGET_DISCOUNT_PCT = Decimal("0.05")  # 5% target strategic discount

    @classmethod
    def calculate_negotiation_bounds(
        cls,
        original_amount: Decimal,
        budget_limit: Decimal,
        quantity: int,
        target_discount_pct: Optional[Decimal] = None
    ) -> NegotiationBounds:
        if original_amount <= Decimal("0.00"):
            raise ValueError("Original quotation amount must be positive.")
        if budget_limit <= Decimal("0.00"):
            raise ValueError("Budget limit must be positive.")

        discount_pct = target_discount_pct or cls.DEFAULT_TARGET_DISCOUNT_PCT

        # Target price: original amount discounted by target_pct, capped by approved budget limit
        discounted_price = (original_amount * (Decimal("1.00") - discount_pct)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        target_price = min(discounted_price, budget_limit)

        # Maximum acceptable price is strictly bounded by budget ceiling and original quotation
        maximum_acceptable_price = min(original_amount, budget_limit)

        # Estimated savings (labeled as non-committed projection)
        estimated_savings = (original_amount - target_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        justification = (
            f"Enterprise volume commitment of {quantity} units, prompt payment terms within 15 days, "
            f"and market benchmark pricing justify an estimated strategic discount of {discount_pct * Decimal('100.00')}% "
            f"to ₹{target_price:,.2f} (Estimated non-committed savings: ₹{estimated_savings:,.2f})."
        )

        return NegotiationBounds(
            target_price=target_price,
            maximum_acceptable_price=maximum_acceptable_price,
            estimated_savings=estimated_savings,
            is_estimate=True,
            justification=justification
        )
