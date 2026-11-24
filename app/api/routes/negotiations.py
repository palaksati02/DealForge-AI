from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.procurement_repo import ProcurementRepository
from app.schemas.schemas import NegotiationResponse, CounterOfferRequest

router = APIRouter(tags=["Negotiations"])


@router.get("/requests/{request_id}/negotiations", response_model=List[NegotiationResponse])
def get_request_negotiations(request_id: str, db: Session = Depends(get_db)):
    repo = ProcurementRepository(db)
    negs = repo.get_negotiations_by_request(request_id)
    results = []
    for n in negs:
        quote = repo.get_quote_by_id(n.quote_id)
        results.append(
            NegotiationResponse(
                negotiation_id=n.negotiation_id,
                request_id=n.request_id,
                quote_id=n.quote_id,
                vendor_name=quote.vendor.vendor_name if (quote and quote.vendor) else None,
                original_amount=n.original_amount,
                target_amount=n.target_amount,
                counter_offer_amount=n.counter_offer_amount,
                justification=n.justification,
                draft_message=n.draft_message,
                negotiation_status=n.negotiation_status,
                vendor_response=n.vendor_response,
            )
        )
    return results


@router.post("/negotiations/{negotiation_id}/counter-offer", response_model=NegotiationResponse)
def submit_or_simulate_counter_offer(
    negotiation_id: str,
    payload: CounterOfferRequest,
    db: Session = Depends(get_db)
):
    repo = ProcurementRepository(db)
    neg = repo.get_negotiation_by_id(negotiation_id)
    if not neg:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    neg.counter_offer_amount = payload.revised_counter_offer
    if payload.revised_message:
        neg.draft_message = payload.revised_message

    if payload.simulate_vendor_reply:
        # Realistic simulation: If counter-offer is >= 93% of original, vendor accepts; otherwise counters
        discount_ratio = payload.revised_counter_offer / neg.original_amount
        if discount_ratio >= Decimal("0.93"):
            neg.negotiation_status = "ACCEPTED"
            neg.vendor_response = (
                f"Vendor Acceptance: In consideration of the enterprise volume and prompt payment terms, "
                f"we agree to the revised counter-offer total of ₹{payload.revised_counter_offer:,.2f}."
            )
        else:
            neg.negotiation_status = "COUNTERED"
            compromise = (neg.original_amount * Decimal("0.96")).quantize(Decimal("0.01"))
            neg.vendor_response = (
                f"Vendor Counter-Proposal: We cannot meet ₹{payload.revised_counter_offer:,.2f} due to component cost floors. "
                f"However, we can offer a 4% adjustment to ₹{compromise:,.2f} with complimentary express delivery."
            )
    else:
        neg.negotiation_status = "SENT"

    db.commit()
    db.refresh(neg)

    quote = repo.get_quote_by_id(neg.quote_id)
    return NegotiationResponse(
        negotiation_id=neg.negotiation_id,
        request_id=neg.request_id,
        quote_id=neg.quote_id,
        vendor_name=quote.vendor.vendor_name if (quote and quote.vendor) else None,
        original_amount=neg.original_amount,
        target_amount=neg.target_amount,
        counter_offer_amount=neg.counter_offer_amount,
        justification=neg.justification,
        draft_message=neg.draft_message,
        negotiation_status=neg.negotiation_status,
        vendor_response=neg.vendor_response,
    )
