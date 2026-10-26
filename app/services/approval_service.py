from decimal import Decimal
from typing import Dict, Any, Tuple
from app.core.config import settings
from app.schemas.schemas import RiskAssessmentSchema


class ApprovalService:
    """
    Deterministic Approval Policy Engine.
    Enforces governance thresholds and determines if human manager approval is required.
    LLM recommendations cannot bypass strict financial thresholds.
    """

    @classmethod
    def evaluate_approval_requirement(
        cls,
        total_amount: Decimal,
        budget_limit: Decimal,
        risk_assessment: Dict[str, Any],
        is_compliant: bool,
    ) -> Tuple[bool, str]:
        reasons = []

        # 1. Budget overrun check
        if total_amount > budget_limit:
            overrun = total_amount - budget_limit
            reasons.append(f"Budget overrun of ₹{overrun:,.2f} exceeds approved ceiling ₹{budget_limit:,.2f}")

        # 2. Financial threshold check (e.g. >= ₹10,00,000 requires VP/Manager approval)
        if total_amount >= settings.AUTO_APPROVAL_THRESHOLD:
            reasons.append(
                f"Total procurement amount ₹{total_amount:,.2f} exceeds auto-approval threshold of ₹{settings.AUTO_APPROVAL_THRESHOLD:,.2f}"
            )

        # 3. Google ADK Risk Assessment Check
        risk_category = risk_assessment.get("risk_category", "LOW").upper()
        if risk_category in ["HIGH", "CRITICAL"]:
            reasons.append(f"Google ADK risk agent flagged {risk_category} risk ({risk_assessment.get('explanation', '')})")

        if risk_assessment.get("human_review_required", False):
            reasons.append("Independent risk assessment specifically recommended human review")

        # 4. Compliance check
        if not is_compliant:
            reasons.append("One or more compliance criteria unresolved")

        requires_human_approval = len(reasons) > 0
        explanation = "; ".join(reasons) if requires_human_approval else "Criteria met for automated straight-through processing."

        return requires_human_approval, explanation
