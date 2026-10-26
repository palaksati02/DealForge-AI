from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import ApprovalResponse, ApprovalDecisionRequest
from app.agents.procurement_crew import ProcurementWorkflowEngine

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("/pending", response_model=List[ApprovalResponse])
def get_pending_approvals(db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    approvals = repo.get_pending_approvals()
    results = []
    for a in approvals:
        quote = repo.get_quote_by_id(a.quote_id)
        req = repo.get_purchase_request(a.request_id)
        results.append(
            ApprovalResponse(
                approval_id=a.approval_id,
                request_id=a.request_id,
                quote_id=a.quote_id,
                vendor_name=quote.vendor.vendor_name if (quote and quote.vendor) else None,
                total_amount=quote.total_amount if quote else None,
                budget_limit=req.budget_limit if req else None,
                risk_assessment=a.risk_assessment,
                approval_reason=a.approval_reason,
                requested_by=a.requested_by,
                decision=a.decision,
                decided_by=a.decided_by,
                comments=a.comments,
                created_at=a.created_at,
                decided_at=a.decided_at,
            )
        )
    return results


@router.post("/{approval_id}/decision")
def submit_approval_decision(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db)
):
    repo = ProcurementRepository(db)
    appr = repo.get_approval_by_id(approval_id)
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if appr.decision != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval has already been finalized as {appr.decision}")

    engine = ProcurementWorkflowEngine(db)
    res = engine.resume_workflow(
        approval_id=approval_id,
        decision=payload.decision.upper(),
        decided_by=payload.decided_by,
        comments=payload.comments
    )
    return res
