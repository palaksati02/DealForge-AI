import json
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db, SessionLocal
from app.db.repositories.procurement_repo import ProcurementRepository
from app.db.models.entities import ProcurementPolicy, ProcurementAuditLog
from app.schemas.schemas import (
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    WorkflowStatusResponse,
    AgentLogResponse,
    ApprovalDecisionRequest
)
from app.agents.procurement_crew import ProcurementWorkflowEngine
from app.services.report_service import ReportService
from app.services.replanning_service import ReplanningService
from app.core.security import get_current_user_optional, require_role, User
from app.core.logging import logger

router = APIRouter(prefix="/procurement", tags=["Procurement Lifecycle"])


class ReplanRequestPayload(BaseModel):
    trigger_type: str  # "BUDGET_CUT", "VENDOR_STOCKOUT", "NEGOTIATION_REJECTION"
    new_budget: Optional[Decimal] = None
    vendor_id: Optional[str] = None
    negotiation_id: Optional[str] = None
    reason: Optional[str] = None


def _run_workflow_async(request_id: str, workflow_id: str):
    db = SessionLocal()
    try:
        engine = ProcurementWorkflowEngine(db)
        engine.execute_workflow(request_id=request_id, workflow_id=workflow_id)
    except Exception as e:
        logger.error(f"Error in background procurement execution for {workflow_id}: {e}")
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


@router.post("/requests", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
def submit_procurement_request(
    payload: PurchaseRequestCreate,
    background_tasks: BackgroundTasks,
    auto_start: bool = True,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Submit a natural-language procurement purchase request and automatically kick off the Google ADK workflow."""
    repo = ProcurementRepository(db)
    engine = ProcurementWorkflowEngine(db)

    requester_name = current_user.full_name if current_user else payload.requester

    # Extract requirements using Google ADK Requirement Analysis Agent
    extracted = engine.run_requirement_agent(
        raw_text=payload.raw_request_text,
        overrides={
            "quantity": payload.quantity_override,
            "budget_limit": payload.budget_override,
            "delivery_deadline_days": payload.deadline_override_days,
            "warranty_requirement_months": payload.warranty_override_months,
            "category": payload.category_override,
        }
    )

    req = repo.create_purchase_request(
        requester=requester_name,
        raw_request_text=payload.raw_request_text,
        product_requirements=extracted.model_dump(mode="json"),
        quantity=extracted.quantity,
        budget_limit=extracted.budget_limit,
        currency=extracted.currency,
        delivery_deadline_days=extracted.delivery_deadline_days,
        warranty_requirement_months=extracted.warranty_requirement_months,
    )

    repo.log_procurement_audit(
        action="REQUEST_SUBMITTED",
        actor=requester_name,
        actor_role=current_user.role.role_name if (current_user and current_user.role) else "Requester",
        request_id=req.request_id,
        details={"quantity": req.quantity, "budget_limit": float(req.budget_limit)}
    )

    if auto_start:
        workflow_id = str(uuid.uuid4())
        background_tasks.add_task(_run_workflow_async, req.request_id, workflow_id)

    return req


@router.get("/requests/{request_id}", response_model=PurchaseRequestResponse)
def get_procurement_request_by_id(request_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    req = repo.get_purchase_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"Procurement request '{request_id}' not found")
    return req


@router.get("/requests/{request_id}/status", response_model=WorkflowStatusResponse)
def get_procurement_workflow_status(request_id: str, db: Session = Depends(get_db)):
    """Fetch current workflow state, step, and agent execution logs for a request."""
    repo = ProcurementRepository(db)
    state = repo.get_workflow_state_by_request(request_id)
    if not state:
        req = repo.get_purchase_request(request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Procurement request not found")
        return WorkflowStatusResponse(
            workflow_id="",
            request_id=request_id,
            current_step="PENDING_ORCHESTRATION",
            status=req.status,
            state_data={},
            logs=[]
        )

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


@router.get("/requests/{request_id}/report")
def get_procurement_report(request_id: str, db: Session = Depends(get_db)):
    """Generate comprehensive auditable multi-agent procurement report."""
    try:
        return ReportService.generate_procurement_report(db, request_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error compiling procurement report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate procurement report: {str(e)}")


@router.post("/requests/{request_id}/approval")
def submit_request_approval(
    request_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Submit approval or rejection for a paused procurement workflow."""
    repo = ProcurementRepository(db)
    pending_list = repo.get_pending_approvals()
    approval = next((a for a in pending_list if a.request_id == request_id), None)
    if not approval:
        raise HTTPException(status_code=404, detail=f"No pending approval found for request '{request_id}'")

    decider_name = current_user.full_name if current_user else payload.decided_by
    decider_role = current_user.role.role_name if (current_user and current_user.role) else "Procurement Manager"

    engine = ProcurementWorkflowEngine(db)
    res = engine.resume_workflow(
        approval_id=approval.approval_id,
        decision=payload.decision.upper(),
        decided_by=decider_name,
        comments=payload.comments,
        approver_role=decider_role
    )
    return res


@router.post("/requests/{request_id}/replan")
def trigger_procurement_replanning(
    request_id: str,
    payload: ReplanRequestPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Trigger dynamic replanning when conditions change (budget cut, vendor stockout, etc.)."""
    repo = ProcurementRepository(db)
    wf_state = repo.get_workflow_state_by_request(request_id)
    if not wf_state:
        raise HTTPException(status_code=404, detail=f"No active workflow found for request '{request_id}'")

    trigger = payload.trigger_type.upper()
    try:
        if trigger == "BUDGET_CUT":
            if not payload.new_budget:
                raise HTTPException(status_code=400, detail="new_budget is required for BUDGET_CUT")
            return ReplanningService.handle_budget_reduction(
                db=db,
                workflow_id=wf_state.workflow_id,
                request_id=request_id,
                new_budget=payload.new_budget
            )
        elif trigger == "VENDOR_STOCKOUT":
            if not payload.vendor_id:
                raise HTTPException(status_code=400, detail="vendor_id is required for VENDOR_STOCKOUT")
            return ReplanningService.handle_vendor_stockout(
                db=db,
                workflow_id=wf_state.workflow_id,
                request_id=request_id,
                vendor_id=payload.vendor_id
            )
        elif trigger == "NEGOTIATION_REJECTION":
            if not payload.negotiation_id:
                raise HTTPException(status_code=400, detail="negotiation_id is required for NEGOTIATION_REJECTION")
            return ReplanningService.handle_negotiation_rejection(
                db=db,
                workflow_id=wf_state.workflow_id,
                negotiation_id=payload.negotiation_id
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported trigger_type '{payload.trigger_type}'")
    except Exception as e:
        logger.error(f"Error handling replanning: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/policies")
def list_procurement_policies(db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    return repo.get_all_policies()


@router.get("/audit-logs")
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    entries = list(
        db.scalars(
            db.query(ProcurementAuditLog).order_by(desc(ProcurementAuditLog.timestamp)).limit(limit)
        ).all()
    ) if hasattr(db, 'scalars') else db.query(ProcurementAuditLog).order_by(desc(ProcurementAuditLog.timestamp)).limit(limit).all()
    return [
        {
            "audit_id": a.audit_id,
            "request_id": a.request_id,
            "action": a.action,
            "actor": a.actor,
            "actor_role": a.actor_role,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "details": a.details
        }
        for a in entries
    ]


@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_events(workflow_id: str):
    """Server-Sent Events (SSE) stream delivering real-time agent execution events."""
    async def event_generator():
        sent_log_ids = set()
        retries_without_new_data = 0
        while retries_without_new_data < 60:
            db = SessionLocal()
            try:
                repo = ProcurementRepository(db)
                state = repo.get_workflow_state(workflow_id)
                logs = repo.get_workflow_logs(workflow_id)

                new_logs = [l for l in logs if l.log_id not in sent_log_ids]
                for l in new_logs:
                    sent_log_ids.add(l.log_id)
                    event_data = {
                        "type": "AGENT_EVENT",
                        "workflow_id": workflow_id,
                        "current_step": state.current_step if state else "UNKNOWN",
                        "workflow_status": state.status if state else "RUNNING",
                        "log": {
                            "log_id": l.log_id,
                            "agent_name": l.agent_name,
                            "event_type": l.event_type,
                            "status": l.status,
                            "output_summary": l.output_summary,
                            "started_at": l.started_at.isoformat() if l.started_at else None,
                        }
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                if state and state.status in ["COMPLETED", "FAILED", "PAUSED"] and not new_logs:
                    final_event = {
                        "type": "WORKFLOW_STATUS",
                        "workflow_id": workflow_id,
                        "current_step": state.current_step,
                        "workflow_status": state.status,
                        "state_data": state.state_data,
                    }
                    yield f"data: {json.dumps(final_event)}\n\n"
                    break

                if not new_logs:
                    retries_without_new_data += 1
                else:
                    retries_without_new_data = 0
            finally:
                db.close()
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
