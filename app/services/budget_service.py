from decimal import Decimal
from app.schemas.schemas import BudgetValidationResult
from app.core.config import settings


class BudgetService:
    """
    Deterministic budget validation service.
    Enforces corporate financial limits.
    Budget violations are never masked or modified.
    """

    @classmethod
    def validate_budget(cls, total_cost: Decimal, budget_limit: Decimal, currency: str = "INR") -> BudgetValidationResult:
        if total_cost < Decimal("0.00") or budget_limit < Decimal("0.00"):
            raise ValueError("Amounts cannot be negative.")

        difference = budget_limit - total_cost
        is_valid = difference >= Decimal("0.00")
        overrun_amount = Decimal("0.00") if is_valid else abs(difference)

        if is_valid:
            explanation = (
                f"Within budget: Total cost ₹{total_cost:,.2f} is within the approved budget limit of ₹{budget_limit:,.2f} "
                f"(Remaining surplus: ₹{difference:,.2f})."
            )
        else:
            explanation = (
                f"BUDGET OVERRUN DETECTED: Total cost ₹{total_cost:,.2f} exceeds approved limit of ₹{budget_limit:,.2f} "
                f"by ₹{overrun_amount:,.2f}. Automatic finalisation blocked."
            )

        return BudgetValidationResult(
            budget_limit=budget_limit,
            total_cost=total_cost,
            is_valid=is_valid,
            difference=difference,
            overrun_amount=overrun_amount,
            currency=currency,
            explanation=explanation,
        )
