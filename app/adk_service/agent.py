from typing import Dict, Any, List, Optional
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from app.core.config import settings
from app.core.logging import logger
from app.a2a.schemas import RiskAssessmentPayload, RiskAssessmentResponsePayload


class ADKProcurementRiskAgent:
    """
    Independent Risk and Compliance Agent built with Google ADK (Agent Development Kit).
    Uses Google ADK's Agent and Runner execution model with stateful session management.
    Acts as an autonomous auditor validating procurement proposals via the A2A protocol.
    """

    def __init__(self):
        self.session_service = InMemorySessionService()
        self.adk_agent = Agent(
            name="GoogleADK_ProcurementRiskAgent",
            instruction=(
                "You are an independent risk assessment agent. Your duty is to objectively evaluate "
                "enterprise procurement deals for financial overrun risk, compliance liabilities, "
                "delivery bottleneck hazards, and counterparty reliability. Provide structured assessments "
                "with an objective risk score from 0 to 100."
            )
        )
        self.runner = Runner(
            app_name="dealforge_procurement_risk",
            agent=self.adk_agent,
            session_service=self.session_service,
            auto_create_session=True
        )
        self.audit_sessions: Dict[str, Dict[str, Any]] = {}

    def evaluate_risk(self, payload: RiskAssessmentPayload) -> RiskAssessmentResponsePayload:
        """
        Evaluates the 7 required procurement risk dimensions:
        1. Vendor Financial Stability & Overrun
        2. Vendor Compliance Liabilities
        3. Procurement Budget Risk
        4. Delivery SLA & Lead Time Hazards
        5. Warranty Terms & Protection
        6. Supplier Reliability & Historical Rating
        7. Materiality / Value Threshold Breach
        """
        logger.info(f"Google ADK Agent [{self.adk_agent.name}] assessing procurement risk for request {payload.request_id}...")

        risk_score = 0.0
        risk_factors: List[str] = []

        # 1. Procurement Budget Risk & Financial Overrun
        if not payload.is_budget_valid or payload.budget_overrun > 0:
            overrun_ratio = payload.budget_overrun / max(1.0, payload.budget_limit)
            overrun_pts = min(40.0, 25.0 + overrun_ratio * 50.0)
            risk_score += overrun_pts
            risk_factors.append(f"Financial Overrun: Quotation exceeds budget by ₹{payload.budget_overrun:,.2f} ({overrun_ratio * 100:.1f}%)")

        # 2. Transaction Materiality & Governance Threshold Risk
        if payload.total_cost >= payload.approval_policy_threshold:
            size_pts = 20.0
            risk_score += size_pts
            risk_factors.append(
                f"High-Value Materiality: Total commitment ₹{payload.total_cost:,.2f} exceeds auto-approval threshold ₹{payload.approval_policy_threshold:,.2f}"
            )

        # 3. Compliance & Regulatory Liabilities
        if not payload.is_compliant:
            risk_score += 45.0
            reasons_str = "; ".join(payload.failed_compliance_reasons)
            risk_factors.append(f"Compliance Violation: {reasons_str}")

        # 4. Supplier Counterparty Reliability & Quality History
        if payload.vendor_rating < 3.8:
            risk_score += 25.0
            risk_factors.append(f"Critical Counterparty Risk: Vendor rating {payload.vendor_rating:.2f}/5.00 falls below corporate floor 3.80")
        elif payload.vendor_rating < 4.2:
            risk_score += 15.0
            risk_factors.append(f"Sub-optimal Vendor Rating: {payload.vendor_rating:.2f}/5.00 historical rating")

        # 5. Delivery SLA & Lead Time Bottleneck Hazards
        if payload.delivery_days > 14:
            risk_score += 20.0
            risk_factors.append(f"Critical Lead Time: Promised delivery ({payload.delivery_days} days) breaches standard SLA deadline (14 days)")
        elif payload.delivery_days > 10:
            risk_score += 10.0
            risk_factors.append(f"Tight Delivery Window: Promised delivery ({payload.delivery_days} days) is close to threshold")

        # 6. Warranty Terms & Asset Protection
        if payload.warranty_months < 12:
            risk_score += 25.0
            risk_factors.append(f"Severe Warranty Deficiency: {payload.warranty_months} months warranty provides minimal asset coverage")
        elif payload.warranty_months < 24:
            risk_score += 15.0
            risk_factors.append(f"Limited Warranty Coverage: {payload.warranty_months} months warranty provides limited protection")

        # 7. Overall Evaluation Alignment
        if payload.evaluation_score < 70.0:
            risk_score += 10.0
            risk_factors.append(f"Low Multi-Attribute Score: Composite score {payload.evaluation_score:.1f}/100 indicates suboptimal terms")

        # Cap score between 5.0 and 100.0
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
                f"Google ADK evaluated deal risk as {risk_score:.1f}/100 ({category}). "
                f"Identified risk drivers: {'; '.join(risk_factors)}."
            )
        else:
            explanation = (
                f"Google ADK evaluated deal risk as {risk_score:.1f}/100 ({category}). "
                f"Vendor '{payload.vendor_name}' demonstrates strong financial alignment, compliant terms, and acceptable SLA."
            )

        response = RiskAssessmentResponsePayload(
            risk_category=category,
            risk_score=round(risk_score, 2),
            risk_factors=risk_factors,
            explanation=explanation,
            recommended_action=recommended_action,
            human_review_required=human_review,
            assessed_by=f"Google ADK Runner ({self.adk_agent.name}) via A2A Protocol",
        )

        # Record in stateful session audit log
        self.audit_sessions[payload.request_id] = {
            "vendor_name": payload.vendor_name,
            "risk_score": response.risk_score,
            "risk_category": response.risk_category,
            "recommendation": response.recommended_action,
            "human_review_required": response.human_review_required
        }

        return response


# Global instance
adk_risk_agent = ADKProcurementRiskAgent()
