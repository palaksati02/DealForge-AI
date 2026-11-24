from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from app.schemas.schemas import QuoteCalculationBreakdown


class PricingService:
    """
    Deterministic financial calculation engine.
    Calculates subtotal, bulk discounts, applicable tax (GST 18%), and shipping fees.
    Always uses Python Decimal with 2 decimal places precision.
    """

    GST_TAX_RATE = Decimal("0.18")  # Standard 18% GST on enterprise IT hardware
    BASE_SHIPPING_FLAT = Decimal("5000.00")
    SHIPPING_PER_UNIT = Decimal("100.00")

    @classmethod
    def calculate_bulk_discount_percentage(cls, quantity: int, discount_rules: Optional[Dict[str, Any]] = None) -> Decimal:
        if not discount_rules or "tiers" not in discount_rules:
            return Decimal("0.00")

        tiers = discount_rules.get("tiers", [])
        # Tiers format: [{"min_qty": 20, "discount_pct": 5.0}, {"min_qty": 50, "discount_pct": 8.0}]
        applicable_discount = Decimal("0.00")
        for tier in tiers:
            min_qty = tier.get("min_qty", 0)
            pct = Decimal(str(tier.get("discount_pct", 0.0)))
            if quantity >= min_qty and pct > applicable_discount:
                applicable_discount = pct

        return applicable_discount

    @classmethod
    def calculate_quote_breakdown(
        cls,
        unit_price: Decimal,
        quantity: int,
        discount_rules: Optional[Dict[str, Any]] = None,
        apply_shipping: bool = True
    ) -> QuoteCalculationBreakdown:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if unit_price <= Decimal("0.00"):
            raise ValueError("Unit price must be positive.")

        # 1. Base Subtotal = unit_price * quantity
        base_subtotal = (unit_price * Decimal(quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Discount
        discount_pct = cls.calculate_bulk_discount_percentage(quantity, discount_rules)
        discount_amount = (base_subtotal * (discount_pct / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Taxable Amount
        taxable_amount = base_subtotal - discount_amount

        # 4. Tax (18% GST)
        tax_amount = (taxable_amount * cls.GST_TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 5. Shipping
        shipping_cost = Decimal("0.00")
        if apply_shipping:
            shipping_cost = (cls.BASE_SHIPPING_FLAT + (cls.SHIPPING_PER_UNIT * Decimal(quantity))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 6. Final Total
        final_total = taxable_amount + tax_amount + shipping_cost

        return QuoteCalculationBreakdown(
            base_subtotal=base_subtotal,
            discount_percentage=discount_pct,
            discount_amount=discount_amount,
            taxable_amount=taxable_amount,
            tax_rate_percentage=cls.GST_TAX_RATE * Decimal("100.00"),
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            final_total=final_total
        )
