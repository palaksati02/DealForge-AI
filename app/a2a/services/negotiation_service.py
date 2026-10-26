import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from app.a2a.models import AgentCard, AgentCapability, A2ATaskStatus, A2ATaskResponse
from app.services.negotiation_service import NegotiationService
from app.core.logging import logger


class NegotiationA2AService:
    SERVICE_ID = "negotiation"
    ENDPOINT_BASE = "/a2a/negotiation"

    def __init__(self):
        self.tasks: Dict[str, A2ATaskResponse] = {}

    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="DealForge Negotiation Service",
            description="Autonomous A2A agent service for strategic counter-offer calculation, target price bounding, and draft formulation.",
            version="1.0.0",
            protocol="A2A/1.0",
            service_id=self.SERVICE_ID,
            endpoint_base=self.ENDPOINT_BASE,
            capabilities=[
                AgentCapability(
                    name="FORMULATE_COUNTER_OFFER",
                    description="Calculate permitted target price, maximum acceptable price, and generate a draft negotiation letter.",
                ),
            ],
            supported_actions=["FORMULATE_COUNTER_OFFER"],
        )

    def execute_task(
        self,
        task_id: str,
        request_id: str,
        action: str,
        input_data: Dict[str, Any]
    ) -> A2ATaskResponse:
        logger.info(f"NegotiationA2AService executing task [{task_id}] (Action: {action}, Req: {request_id})")
        started_at = datetime.datetime.now(datetime.timezone.utc)

        try:
            if action == "FORMULATE_COUNTER_OFFER":
                original_amount = Decimal(str(input_data["original_amount"]))
                budget_limit = Decimal(str(input_data["budget_limit"]))
                quantity = int(input_data.get("quantity", 1))
                vendor_name = input_data.get("vendor_name", "Vendor")
                quote_id = input_data.get("quote_id", "Q-001")
                category = input_data.get("category", "Equipment")

                bounds = NegotiationService.calculate_negotiation_bounds(
                    original_amount=original_amount,
                    budget_limit=budget_limit,
                    quantity=quantity
                )

                draft_message = (
                    f"Dear {vendor_name} Sales Team,\n\n"
                    f"Thank you for submitting quotation {quote_id} for our procurement of {quantity} units "
                    f"of {category}. While your proposal is highly competitive, our approved corporate target "
                    f"is ₹{bounds.target_price:,.2f} based on volume commitment and guaranteed payment terms within 15 days.\n\n"
                    f"Please confirm if your commercial team can meet this target price to proceed with an immediate Purchase Order.\n\n"
                    f"Warm regards,\nDealForge Enterprise Procurement Team"
                )

                output_data = {
                    "quote_id": quote_id,
                    "vendor_name": vendor_name,
                    "original_amount": float(original_amount),
                    "target_price": float(bounds.target_price),
                    "maximum_acceptable_price": float(bounds.maximum_acceptable_price),
                    "estimated_savings": float(bounds.estimated_savings),
                    "is_estimate": True,
                    "justification": bounds.justification,
                    "draft_message": draft_message
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
                raise ValueError(f"Unsupported action '{action}' for NegotiationA2AService")

        except Exception as e:
            logger.error(f"NegotiationA2AService task [{task_id}] failed: {e}")
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


negotiation_a2a_service = NegotiationA2AService()
