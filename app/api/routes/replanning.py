from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.replanning_service import ReplanningService

router = APIRouter(prefix="/replanning", tags=["Dynamic Replanning"])


class ReplanBudgetRequest(BaseModel):
    workflow_id: str
    request_id: str
    new_budget: Decimal


class ReplanStockoutRequest(BaseModel):
    workflow_id: str
    request_id: str
    vendor_id: str


class ReplanNegotiationRequest(BaseModel):
    workflow_id: str
    negotiation_id: str


@router.post("/budget-cut")
def replan_on_budget_cut(payload: ReplanBudgetRequest, db: Session = Depends(get_db)):
    try:
        return ReplanningService.handle_budget_reduction(
            db=db,
            workflow_id=payload.workflow_id,
            request_id=payload.request_id,
            new_budget=payload.new_budget
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/vendor-stockout")
def replan_on_vendor_stockout(payload: ReplanStockoutRequest, db: Session = Depends(get_db)):
    try:
        return ReplanningService.handle_vendor_stockout(
            db=db,
            workflow_id=payload.workflow_id,
            request_id=payload.request_id,
            vendor_id=payload.vendor_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/negotiation-rejection")
def replan_on_negotiation_rejection(payload: ReplanNegotiationRequest, db: Session = Depends(get_db)):
    try:
        return ReplanningService.handle_negotiation_rejection(
            db=db,
            workflow_id=payload.workflow_id,
            negotiation_id=payload.negotiation_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
