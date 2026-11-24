from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import VendorResponse, VendorProductResponse

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.get("", response_model=List[VendorResponse])
def list_vendors(active_only: bool = False, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    vendors = repo.get_all_vendors(active_only=active_only)
    return vendors


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    v = repo.get_vendor_by_id(vendor_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return v


@router.get("/catalog/products", response_model=List[VendorProductResponse])
def search_catalog_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    vps = repo.search_vendor_products(category=category)
    results = []
    for vp in vps:
        results.append(
            VendorProductResponse(
                vendor_product_id=vp.vendor_product_id,
                vendor_id=vp.vendor_id,
                product_id=vp.product_id,
                unit_price=vp.unit_price,
                currency=vp.currency,
                stock_quantity=vp.stock_quantity,
                delivery_days=vp.delivery_days,
                warranty_months=vp.warranty_months,
                minimum_order_quantity=vp.minimum_order_quantity,
                discount_rules=vp.discount_rules,
                vendor_name=vp.vendor.vendor_name,
                product_name=vp.product.product_name,
            )
        )
    return results
