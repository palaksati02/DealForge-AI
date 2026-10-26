import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import WorkflowStatusResponse, AgentLogResponse
from app.agents.procurement_crew import ProcurementWorkflowEngine
from app.core.logging import logger

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def _run_workflow_background(request_id: str, workflow_id: str):
    db = SessionLocal()
    try:
        engine = ProcurementWorkflowEngine(db)
        engine.execute_workflow(request_id=request_id, workflow_id=workflow_id)
    except Exception as e:
        logger.error(f"Error running background workflow {workflow_id}: {e}")
        repo = ProcurementRepository(db)
        repo.save_workflow_state(
            workflow_id=workflow_id,
            request_id=request_id,
            current_step="FAILED",
            status="FAILED",
            state_data={"error": str(e)},
            last_error=str(e)
        )
    finally:
        db.close()


@router.post("/{request_id}/start")
def start_workflow(
    request_id: str,
    background_tasks: BackgroundTasks,
    sync: bool = False,
    db: Session = Depends(get_db)
):
    repo = ProcurementRepository(db)
    req = repo.get_purchase_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Purchase request not found")

    workflow_id = str(uuid.uuid4())

    if sync:
        engine = ProcurementWorkflowEngine(db)
        result = engine.execute_workflow(request_id=request_id, workflow_id=workflow_id)
        return result
    else:
        background_tasks.add_task(_run_workflow_background, request_id, workflow_id)
        return {
            "workflow_id": workflow_id,
            "request_id": request_id,
            "status": "RUNNING",
            "message": "Multi-agent procurement workflow initiated successfully in background."
        }


@router.get("/by-request/{request_id}/status", response_model=WorkflowStatusResponse)
def get_workflow_status_by_request(request_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    state = repo.get_workflow_state_by_request(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow state not found for request")

    logs = repo.get_workflow_logs(state.workflow_id)

    return WorkflowStatusResponse(
        workflow_id=state.workflow_id,
        request_id=state.request_id,
        current_step=state.current_step,
        status=state.status,
        state_data=state.state_data,
        last_error=state.last_error,
        logs=[AgentLogResponse.model_validate(l) for l in logs]
    )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
def get_workflow_status(workflow_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    state = repo.get_workflow_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow state not found")

    logs = repo.get_workflow_logs(workflow_id)

    return WorkflowStatusResponse(
        workflow_id=state.workflow_id,
        request_id=state.request_id,
        current_step=state.current_step,
        status=state.status,
        state_data=state.state_data,
        last_error=state.last_error,
        logs=[AgentLogResponse.model_validate(l) for l in logs]
    )


@router.get("/{workflow_id}/events", response_model=List[AgentLogResponse])
def get_workflow_events(workflow_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    logs = repo.get_workflow_logs(workflow_id)
    return [AgentLogResponse.model_validate(l) for l in logs]
