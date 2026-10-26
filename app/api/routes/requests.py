from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import PurchaseRequestCreate, PurchaseRequestResponse
from app.agents.procurement_crew import ProcurementWorkflowEngine

router = APIRouter(prefix="/requests", tags=["Purchase Requests"])


@router.post("", response_model=PurchaseRequestResponse)
def create_purchase_request(payload: PurchaseRequestCreate, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    engine = ProcurementWorkflowEngine(db)

    # Initial extraction of requirements from text
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
        requester=payload.requester,
        raw_request_text=payload.raw_request_text,
        product_requirements=extracted.model_dump(mode="json"),
        quantity=extracted.quantity,
        budget_limit=extracted.budget_limit,
        currency=extracted.currency,
        delivery_deadline_days=extracted.delivery_deadline_days,
        warranty_requirement_months=extracted.warranty_requirement_months,
    )
    return req


@router.get("", response_model=List[PurchaseRequestResponse])
def list_purchase_requests(limit: int = 50, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    return repo.get_all_purchase_requests(limit=limit)


@router.get("/{request_id}", response_model=PurchaseRequestResponse)
def get_purchase_request(request_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    req = repo.get_purchase_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    return req
