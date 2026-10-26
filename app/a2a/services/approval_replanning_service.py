import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from app.a2a.models import AgentCard, AgentCapability, A2ATaskStatus, A2ATaskResponse
from app.services.approval_service import ApprovalService
from app.core.config import settings
from app.core.logging import logger


class ApprovalReplanningA2AService:
    SERVICE_ID = "approval-replanning"
    ENDPOINT_BASE = "/a2a/approval-replanning"

    def __init__(self):
        self.tasks: Dict[str, A2ATaskResponse] = {}

    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="DealForge Approval and Replanning Service",
            description="Autonomous A2A agent service for governance risk assessment, human approval escalation gating, and dynamic replanning.",
            version="1.0.0",
            protocol="A2A/1.0",
            service_id=self.SERVICE_ID,
            endpoint_base=self.ENDPOINT_BASE,
            capabilities=[
                AgentCapability(
                    name="EVALUATE_GOVERNANCE_RISK",
                    description="Calculate comprehensive risk score and determine whether mandatory human approval is required.",
                ),
                AgentCapability(
                    name="PLAN_RECOVERY",
                    description="Identify earliest invalidated workflow stage and construct recovery plan for modified conditions.",
                ),
            ],
            supported_actions=["EVALUATE_GOVERNANCE_RISK", "PLAN_RECOVERY"],
        )

    def execute_task(
        self,
        task_id: str,
        request_id: str,
        action: str,
        input_data: Dict[str, Any]
    ) -> A2ATaskResponse:
        logger.info(f"ApprovalReplanningA2AService executing task [{task_id}] (Action: {action}, Req: {request_id})")
        started_at = datetime.datetime.now(datetime.timezone.utc)

        try:
            if action == "EVALUATE_GOVERNANCE_RISK":
                total_cost = Decimal(str(input_data["total_cost"]))
                budget_limit = Decimal(str(input_data["budget_limit"]))
                is_compliant = bool(input_data.get("is_compliant", True))
                vendor_rating = float(input_data.get("vendor_rating", 4.0))
                delivery_days = int(input_data.get("delivery_days", 10))
                warranty_months = int(input_data.get("warranty_months", 24))

                # Calculate Risk Score (0 - 100)
                risk_score = 0.0
                risk_factors = []

                if total_cost > budget_limit:
                    overrun = float(total_cost - budget_limit)
                    risk_score += 45.0
                    risk_factors.append(f"Financial Overrun: Exceeds approved budget by ₹{overrun:,.2f}")

                if total_cost >= settings.AUTO_APPROVAL_THRESHOLD:
                    risk_score += 20.0
                    risk_factors.append(f"High-Value Transaction: ₹{float(total_cost):,.2f} exceeds auto-approval threshold ₹{float(settings.AUTO_APPROVAL_THRESHOLD):,.2f}")

                if not is_compliant:
                    risk_score += 50.0
                    risk_factors.append("Governance Liability: Failed mandatory compliance checks")

                if vendor_rating < 4.0:
                    risk_score += 15.0
                    risk_factors.append(f"Sub-optimal Vendor Rating: {vendor_rating:.2f}/5.00")

                if delivery_days > 12:
                    risk_score += 10.0
                    risk_factors.append(f"Delivery Risk: Timeline ({delivery_days} days) close to deadline")

                if warranty_months < 24:
                    risk_score += 15.0
                    risk_factors.append(f"Short Warranty SLA: {warranty_months} months")

                risk_score = min(100.0, max(5.0, risk_score))

                if risk_score >= 70.0:
                    category = "HIGH"
                    action_rec = "REJECT" if not is_compliant else "ESCALATE"
                    human_review = True
                elif risk_score >= 35.0:
                    category = "MEDIUM"
                    action_rec = "REVIEW"
                    human_review = True
                else:
                    category = "LOW"
                    action_rec = "APPROVE"
                    human_review = False

                requires_approval, approval_reason = ApprovalService.evaluate_approval_requirement(
                    total_amount=total_cost,
                    budget_limit=budget_limit,
                    risk_assessment={"risk_category": category, "risk_score": risk_score, "human_review_required": human_review},
                    is_compliant=is_compliant
                )

                output_data = {
                    "risk_category": category,
                    "risk_score": round(risk_score, 2),
                    "risk_factors": risk_factors,
                    "requires_approval": requires_approval or human_review,
                    "approval_reason": approval_reason or f"Risk Score {risk_score:.1f} ({category}) demands oversight.",
                    "recommended_action": action_rec
                }

                completed_at = datetime.datetime.now(datetime.timezone.utc)
                response = A2ATaskResponse(
                    task_id=task_id,
                    request_id=request_id,
                    service_id=self.SERVICE_ID,
                    status=A2ATaskStatus.COMPLETED,
                    output_data=output_data,
                    started_at=started_at,
                    completed_at=completed_at
                )
                self.tasks[task_id] = response
                return response

            elif action == "PLAN_RECOVERY":
                trigger_event = input_data.get("trigger_event", "BUDGET_REDUCED")
                replan_data = input_data.get("replan_data", {})

                if trigger_event == "BUDGET_REDUCED":
                    earliest_invalidated_step = "BUDGET_VALIDATION"
                    actions_to_rerun = ["BUDGET_VALIDATION", "EVALUATION", "NEGOTIATION", "APPROVAL_CHECK"]
                elif trigger_event in ["VENDOR_UNAVAILABLE", "VENDOR_STOCKOUT"]:
                    earliest_invalidated_step = "VENDOR_RESEARCH"
                    actions_to_rerun = ["VENDOR_RESEARCH", "PRICE_ANALYSIS", "COMPLIANCE", "EVALUATION", "NEGOTIATION", "APPROVAL_CHECK"]
                elif trigger_event == "APPROVAL_REJECTED":
                    earliest_invalidated_step = "NEGOTIATION"
                    actions_to_rerun = ["NEGOTIATION", "EVALUATION", "APPROVAL_CHECK"]
                else:
                    earliest_invalidated_step = "VENDOR_RESEARCH"
                    actions_to_rerun = ["VENDOR_RESEARCH", "PRICE_ANALYSIS", "EVALUATION"]

                output_data = {
                    "trigger_event": trigger_event,
                    "earliest_invalidated_step": earliest_invalidated_step,
                    "stages_to_rerun": actions_to_rerun,
                    "replan_plan_id": str(uuid.uuid4()),
                    "explanation": f"Condition change ({trigger_event}) invalidated state at {earliest_invalidated_step}. Staged rollback prepared."
                }

                completed_at = datetime.datetime.now(datetime.timezone.utc)
                response = A2ATaskResponse(
                    task_id=task_id,
                    request_id=request_id,
                    service_id=self.SERVICE_ID,
                    status=A2ATaskStatus.COMPLETED,
                    output_data=output_data,
                    started_at=started_at,
                    completed_at=completed_at
                )
                self.tasks[task_id] = response
                return response
            else:
                raise ValueError(f"Unsupported action '{action}' for ApprovalReplanningA2AService")

        except Exception as e:
            logger.error(f"ApprovalReplanningA2AService task [{task_id}] failed: {e}")
            completed_at = datetime.datetime.now(datetime.timezone.utc)
            response = A2ATaskResponse(
                task_id=task_id,
                request_id=request_id,
                service_id=self.SERVICE_ID,
                status=A2ATaskStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=completed_at
            )
            self.tasks[task_id] = response
            return response

    def get_task_status(self, task_id: str) -> Optional[A2ATaskResponse]:
        return self.tasks.get(task_id)


approval_replanning_service = ApprovalReplanningA2AService()
