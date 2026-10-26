from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import VendorQuoteResponse

router = APIRouter(prefix="/requests/{request_id}/quotes", tags=["Vendor Quotes"])


@router.get("", response_model=List[VendorQuoteResponse])
def get_request_quotes(request_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    quotes = repo.get_quotes_by_request(request_id)
    results = []
    for q in quotes:
        results.append(
            VendorQuoteResponse(
                quote_id=q.quote_id,
                request_id=q.request_id,
                vendor_id=q.vendor_id,
                vendor_name=q.vendor.vendor_name if q.vendor else None,
                unit_price=q.unit_price,
                quantity=q.quantity,
                discount=q.discount,
                tax=q.tax,
                shipping_cost=q.shipping_cost,
                total_amount=q.total_amount,
                delivery_days=q.delivery_days,
                warranty_months=q.warranty_months,
                availability_status=q.availability_status,
                quote_status=q.quote_status,
                calculation_breakdown=q.calculation_breakdown,
                created_at=q.created_at,
            )
        )
    return results
