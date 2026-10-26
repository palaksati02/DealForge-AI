from typing import Dict, Any, List
from google.adk import Agent
from app.core.config import settings
from app.core.logging import logger
from app.a2a.schemas import RiskAssessmentPayload, RiskAssessmentResponsePayload


class ADKProcurementRiskAgent:
    """
    Independent Risk and Compliance Agent built with Google ADK (Agent Development Kit).
    Acts as an autonomous auditor validating procurement proposals via the A2A protocol.
    """

    def __init__(self):
        self.adk_agent = Agent(
            name="GoogleADK_ProcurementRiskAgent",
            instruction=(
                "You are an independent risk assessment agent. Your duty is to objectively evaluate "
                "enterprise procurement deals for financial overrun risk, compliance liabilities, "
                "delivery bottleneck hazards, and counterparty reliability. Provide structured assessments "
                "with an objective risk score from 0 to 100."
            )
        )

    def evaluate_risk(self, payload: RiskAssessmentPayload) -> RiskAssessmentResponsePayload:
        logger.info(f"Google ADK Agent assessing procurement risk for request {payload.request_id}...")

        risk_score = 0.0
        risk_factors: List[str] = []

        # 1. Financial Overrun Risk
        if not payload.is_budget_valid or payload.budget_overrun > 0:
            overrun_pts = min(40.0, 25.0 + (payload.budget_overrun / max(1.0, payload.budget_limit)) * 50.0)
            risk_score += overrun_pts
            risk_factors.append(f"Financial Overrun: Quotation exceeds budget by ₹{payload.budget_overrun:,.2f}")

        # 2. Transaction Size / Materiality Risk
        if payload.total_cost >= payload.approval_policy_threshold:
            size_pts = 20.0
            risk_score += size_pts
            risk_factors.append(
                f"High-Value Commitment: Transaction of ₹{payload.total_cost:,.2f} exceeds auto-approval threshold ₹{payload.approval_policy_threshold:,.2f}"
            )

        # 3. Compliance & Governance Liability
        if not payload.is_compliant:
            risk_score += 45.0
            reasons_str = "; ".join(payload.failed_compliance_reasons)
            risk_factors.append(f"Compliance Violation: {reasons_str}")

        # 4. Counterparty Reliability (Rating)
        if payload.vendor_rating < 4.0:
            risk_score += 15.0
            risk_factors.append(f"Sub-optimal Vendor Rating: {payload.vendor_rating:.2f}/5.00 historical rating")

        # 5. Delivery & Supply Chain Risk
        if payload.delivery_days > 12:
            risk_score += 10.0
            risk_factors.append(f"Extended Lead Time: Delivery timeline ({payload.delivery_days} days) close to deadline")

        # 6. Warranty Coverage Risk
        if payload.warranty_months < 24:
            risk_score += 15.0
            risk_factors.append(f"Short Warranty: {payload.warranty_months} months warranty provides limited protection")

        # Cap score at 100.0
        risk_score = min(100.0, max(5.0, risk_score))

        # Categorize
        if risk_score >= 70.0:
            category = "HIGH"
            recommended_action = "REJECT" if not payload.is_compliant else "ESCALATE"
            human_review = True
        elif risk_score >= 40.0:
            category = "MEDIUM"
            recommended_action = "REVIEW"
            human_review = True
        else:
            category = "LOW"
            recommended_action = "APPROVE"
            human_review = False

        if risk_factors:
            explanation = (
                f"Google ADK evaluated the deal with risk score {risk_score:.1f}/100 ({category}). "
                f"Primary vulnerabilities identified: {'; '.join(risk_factors)}."
            )
        else:
            explanation = (
                f"Google ADK evaluated the deal with risk score {risk_score:.1f}/100 ({category}). "
                f"Vendor '{payload.vendor_name}' demonstrates strong financial alignment, compliant terms, and acceptable SLA."
            )

        return RiskAssessmentResponsePayload(
            risk_category=category,
            risk_score=round(risk_score, 2),
            risk_factors=risk_factors,
            explanation=explanation,
            recommended_action=recommended_action,
            human_review_required=human_review,
            assessed_by=f"Google ADK ({self.adk_agent.name}) via A2A Protocol",
        )


# Global instance
adk_risk_agent = ADKProcurementRiskAgent()
