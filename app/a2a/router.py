from fastapi import APIRouter, HTTPException
from app.a2a.models import AgentCard, A2ATaskSubmission, A2ATaskResponse
from app.a2a.services.vendor_research_service import vendor_research_service
from app.a2a.services.procurement_analysis_service import procurement_analysis_service
from app.a2a.services.negotiation_service import negotiation_a2a_service
from app.a2a.services.approval_replanning_service import approval_replanning_service
from app.core.logging import logger

router = APIRouter(prefix="/a2a", tags=["Agent-to-Agent Protocol"])

SERVICES = {
    "vendor-research": vendor_research_service,
    "procurement-analysis": procurement_analysis_service,
    "negotiation": negotiation_a2a_service,
    "approval-replanning": approval_replanning_service,
}


@router.get("", tags=["Agent-to-Agent Protocol"])
def list_a2a_services():
    """List all registered protocol-compliant A2A services."""
    return {
        "protocol": "A2A/1.0",
        "services": [s.get_agent_card() for s in SERVICES.values()]
    }


# --- Agent Cards Discovery ---
@router.get("/{service_id}/.well-known/agent.json", response_model=AgentCard)
@router.get("/{service_id}/card", response_model=AgentCard)
def get_service_agent_card(service_id: str):
    """Publish the Agent Card describing identity, protocol, and capabilities."""
    service = SERVICES.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"A2A Service '{service_id}' not found")
    return service.get_agent_card()


# --- Task Lifecycle Endpoints ---
@router.post("/{service_id}/tasks", response_model=A2ATaskResponse)
def submit_a2a_task(service_id: str, submission: A2ATaskSubmission):
    """Submit a task to a separately addressable A2A service."""
    service = SERVICES.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"A2A Service '{service_id}' not found")

    logger.info(f"A2A task submitted to [{service_id}] from [{submission.sender_agent}] (Action: {submission.action})")
    response = service.execute_task(
        task_id=submission.task_id,
        request_id=submission.request_id,
        action=submission.action,
        input_data=submission.input_data
    )
    return response


@router.get("/{service_id}/tasks/{task_id}", response_model=A2ATaskResponse)
def get_a2a_task_status(service_id: str, task_id: str):
    """Retrieve status and structured output for an existing A2A task."""
    service = SERVICES.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"A2A Service '{service_id}' not found")

    task = service.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found in service '{service_id}'")
    return task
