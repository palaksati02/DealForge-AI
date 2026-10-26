from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import EvaluationResponse

router = APIRouter(prefix="/requests/{request_id}/evaluations", tags=["Evaluations"])


@router.get("", response_model=List[EvaluationResponse])
def get_request_evaluations(request_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    evals = repo.get_evaluations_by_request(request_id)
    results = []
    for e in evals:
        quote = repo.get_quote_by_id(e.quote_id)
        results.append(
            EvaluationResponse(
                evaluation_id=e.evaluation_id,
                request_id=e.request_id,
                quote_id=e.quote_id,
                vendor_id=quote.vendor_id if quote else None,
                vendor_name=quote.vendor.vendor_name if (quote and quote.vendor) else None,
                price_score=e.price_score,
                delivery_score=e.delivery_score,
                warranty_score=e.warranty_score,
                compliance_score=e.compliance_score,
                specification_score=e.specification_score,
                final_score=e.final_score,
                eligibility_status=e.eligibility_status,
                exclusion_reason=e.exclusion_reason,
                explanation=e.explanation,
                rank=e.rank,
            )
        )
    return results
