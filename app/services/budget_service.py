from decimal import Decimal
from app.schemas.schemas import BudgetValidationResult
from app.core.config import settings


class BudgetService:
    """
    Deterministic budget validation service.
    Enforces corporate financial limits and approval escalation levels.
    A quotation above a strict budget limit must NEVER be labelled compliant.
    """

    DUAL_APPROVAL_THRESHOLD = Decimal("2500000.00")  # ₹25,00,000

    @classmethod
    def validate_budget(
        cls,
        total_cost: Decimal,
        budget_limit: Decimal,
        currency: str = "INR"
    ) -> BudgetValidationResult:
        if total_cost < Decimal("0.00") or budget_limit < Decimal("0.00"):
            raise ValueError("Amounts cannot be negative.")

        difference = budget_limit - total_cost
        is_valid = difference >= Decimal("0.00")
        overrun_amount = Decimal("0.00") if is_valid else abs(difference)

        if is_valid:
            budget_status = "COMPLIANT_WITHIN_BUDGET"
            # Determine required approval level within budget
            if total_cost <= settings.AUTO_APPROVAL_THRESHOLD:
                required_approval_level = "NONE"
            elif total_cost <= cls.DUAL_APPROVAL_THRESHOLD:
                required_approval_level = "PROCUREMENT_MANAGER"
            else:
                required_approval_level = "FINANCE_REVIEWER"

            explanation = (
                f"Within budget: Total cost ₹{total_cost:,.2f} is within the approved budget limit of ₹{budget_limit:,.2f} "
                f"(Remaining surplus: ₹{difference:,.2f}). Required approval level: {required_approval_level}."
            )
        else:
            budget_status = "BUDGET_OVERRUN"
            required_approval_level = "EXECUTIVE_ESCALATION"
            explanation = (
                f"BUDGET OVERRUN DETECTED: Total cost ₹{total_cost:,.2f} strictly exceeds approved limit of ₹{budget_limit:,.2f} "
                f"by ₹{overrun_amount:,.2f}. Marked as non-compliant overrun requiring executive escalation."
            )

        return BudgetValidationResult(
            budget_limit=budget_limit,
            total_cost=total_cost,
            is_valid=is_valid,
            budget_status=budget_status,
            difference=difference,
            overrun_amount=overrun_amount,
            required_approval_level=required_approval_level,
            currency=currency,
            explanation=explanation,
        )
