from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import PurchaseOrderResponse

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get("", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    pos = repo.get_all_purchase_orders()
    results = []
    for po in pos:
        results.append(
            PurchaseOrderResponse(
                purchase_order_id=po.purchase_order_id,
                request_id=po.request_id,
                vendor_id=po.vendor_id,
                vendor_name=po.vendor.vendor_name if po.vendor else None,
                quote_id=po.quote_id,
                order_number=po.order_number,
                approved_total=po.approved_total,
                currency=po.currency,
                status=po.status,
                approved_by=po.approved_by,
                order_details=po.order_details,
                created_at=po.created_at,
            )
        )
    return results


@router.get("/{purchase_order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(purchase_order_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    pos = repo.get_all_purchase_orders()
    po = next((p for p in pos if p.purchase_order_id == purchase_order_id or p.order_number == purchase_order_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    return PurchaseOrderResponse(
        purchase_order_id=po.purchase_order_id,
        request_id=po.request_id,
        vendor_id=po.vendor_id,
        vendor_name=po.vendor.vendor_name if po.vendor else None,
        quote_id=po.quote_id,
        order_number=po.order_number,
        approved_total=po.approved_total,
        currency=po.currency,
        status=po.status,
        approved_by=po.approved_by,
        order_details=po.order_details,
        created_at=po.created_at,
    )
