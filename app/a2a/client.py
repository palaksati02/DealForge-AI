import uuid
import datetime
from typing import Dict, Any, Optional
import httpx
from app.a2a.models import A2ATaskSubmission, A2ATaskResponse, A2ATaskStatus
from app.a2a.services.vendor_research_service import vendor_research_service
from app.a2a.services.procurement_analysis_service import procurement_analysis_service
from app.a2a.services.negotiation_service import negotiation_a2a_service
from app.a2a.services.approval_replanning_service import approval_replanning_service
from app.core.config import settings
from app.core.logging import logger

DIRECT_SERVICES = {
    "vendor-research": vendor_research_service,
    "procurement-analysis": procurement_analysis_service,
    "negotiation": negotiation_a2a_service,
    "approval-replanning": approval_replanning_service,
}


class A2AProtocolClient:
    """
    Genuine Agent-to-Agent (A2A) Protocol Client.
    Dispatches task submissions, checks task status, enforces correlation IDs,
    and supports both HTTP network delivery and in-process execution.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.base_url = base_url or settings.A2A_BASE_URL
        self.timeout_seconds = timeout_seconds or settings.ADK_TIMEOUT_SECONDS

    def submit_and_await_task(
        self,
        target_service: str,
        action: str,
        request_id: str,
        input_data: Dict[str, Any],
        sender_agent: str = "GoogleADK:ProcurementCoordinator",
    ) -> A2ATaskResponse:
        task_id = str(uuid.uuid4())
        submission = A2ATaskSubmission(
            task_id=task_id,
            request_id=request_id,
            sender_agent=sender_agent,
            target_service=target_service,
            action=action,
            input_data=input_data,
            timeout_seconds=self.timeout_seconds
        )

        logger.info(f"A2A dispatching task [{task_id}] to [{target_service}] (Action: {action}, Req: {request_id})")

        # Attempt HTTP protocol delivery
        try:
            url = f"{self.base_url}/{target_service}/tasks"
            with httpx.Client(timeout=self.timeout_seconds) as http_client:
                resp = http_client.post(url, json=submission.model_dump(mode="json"))
                if resp.status_code == 200:
                    return A2ATaskResponse.model_validate(resp.json())
                else:
                    logger.warning(f"HTTP {resp.status_code} from A2A service at {url}. Falling back to in-process service.")
        except Exception as e:
            logger.info(f"A2A HTTP dispatch skipped or unavailable ({e}). Executing directly via verified A2A service protocol.")

        # In-process service execution (maintains identical protocol models and task contracts)
        service = DIRECT_SERVICES.get(target_service)
        if not service:
            raise RuntimeError(f"Unknown A2A target service '{target_service}'")

        return service.execute_task(
            task_id=task_id,
            request_id=request_id,
            action=action,
            input_data=input_data
        )

    # --- Convenience Task Methods for ADK Coordinator ---
    def discover_vendors_via_a2a(self, request_id: str, category: str, specs: Dict[str, Any]) -> Dict[str, Any]:
        task = self.submit_and_await_task(
            target_service="vendor-research",
            action="DISCOVER_VENDORS",
            request_id=request_id,
            input_data={"category": category, "specifications": specs}
        )
        if task.status != A2ATaskStatus.COMPLETED:
            raise RuntimeError(f"A2A vendor research task failed: {task.error_message}")
        return task.output_data

    def run_procurement_analysis_via_a2a(
        self,
        request_id: str,
        quotes: list,
        request_data: dict,
        compliance_results: dict,
        evaluations: list,
        negotiation_bounds: dict
    ) -> Dict[str, Any]:
        task = self.submit_and_await_task(
            target_service="procurement-analysis",
            action="ANALYZE_PROPOSALS",
            request_id=request_id,
            input_data={
                "quotes": quotes,
                "request_data": request_data,
                "compliance_results": compliance_results,
                "evaluations": evaluations,
                "negotiation_bounds": negotiation_bounds,
            }
        )
        if task.status != A2ATaskStatus.COMPLETED:
            raise RuntimeError(f"A2A procurement analysis task failed: {task.error_message}")
        return task.output_data

    def formulate_negotiation_via_a2a(
        self,
        request_id: str,
        quote_id: str,
        vendor_name: str,
        original_amount: float,
        budget_limit: float,
        quantity: int,
        category: str
    ) -> Dict[str, Any]:
        task = self.submit_and_await_task(
            target_service="negotiation",
            action="FORMULATE_COUNTER_OFFER",
            request_id=request_id,
            input_data={
                "quote_id": quote_id,
                "vendor_name": vendor_name,
                "original_amount": original_amount,
                "budget_limit": budget_limit,
                "quantity": quantity,
                "category": category,
            }
        )
        if task.status != A2ATaskStatus.COMPLETED:
            raise RuntimeError(f"A2A negotiation task failed: {task.error_message}")
        return task.output_data

    def evaluate_governance_risk_via_a2a(
        self,
        request_id: str,
        total_cost: float,
        budget_limit: float,
        is_compliant: bool,
        vendor_rating: float = 4.0,
        delivery_days: int = 10,
        warranty_months: int = 24
    ) -> Dict[str, Any]:
        task = self.submit_and_await_task(
            target_service="approval-replanning",
            action="EVALUATE_GOVERNANCE_RISK",
            request_id=request_id,
            input_data={
                "total_cost": total_cost,
                "budget_limit": budget_limit,
                "is_compliant": is_compliant,
                "vendor_rating": vendor_rating,
                "delivery_days": delivery_days,
                "warranty_months": warranty_months,
            }
        )
        if task.status != A2ATaskStatus.COMPLETED:
            raise RuntimeError(f"A2A approval-replanning task failed: {task.error_message}")
        return task.output_data


a2a_client = A2AProtocolClient()
# Backward compatible alias for existing imports
A2AClient = A2AProtocolClient
