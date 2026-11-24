import datetime
import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
from app.db.models.entities import (
    Vendor,
    Product,
    VendorProduct,
    PurchaseRequest,
    VendorQuote,
    ComplianceRule,
    Evaluation,
    Negotiation,
    Approval,
    PurchaseOrder,
    AgentLog,
    WorkflowState,
)
from app.db.base import utc_now


class ProcurementRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Vendor & Product Queries ---
    def get_all_vendors(self, active_only: bool = False) -> List[Vendor]:
        query = select(Vendor)
        if active_only:
            query = query.where(Vendor.active_status == True)
        return list(self.db.scalars(query).all())

    def get_vendor_by_id(self, vendor_id: str) -> Optional[Vendor]:
        return self.db.scalar(select(Vendor).where(Vendor.vendor_id == vendor_id))

    def search_vendor_products(self, category: Optional[str] = None, keyword: Optional[str] = None) -> List[VendorProduct]:
        query = select(VendorProduct).join(Vendor).join(Product)
        if category:
            query = query.where(Product.category.ilike(f"%{category}%"))
        if keyword:
            query = query.where(Product.product_name.ilike(f"%{keyword}%"))
        return list(self.db.scalars(query).all())

    def get_vendor_product(self, vendor_id: str, product_id: str) -> Optional[VendorProduct]:
        return self.db.scalar(
            select(VendorProduct).where(
                and_(VendorProduct.vendor_id == vendor_id, VendorProduct.product_id == product_id)
            )
        )

    # --- Purchase Requests ---
    def create_purchase_request(
        self,
        requester: str,
        raw_request_text: str,
        product_requirements: Dict[str, Any],
        quantity: int,
        budget_limit: Decimal,
        currency: str = "INR",
        delivery_deadline_days: int = 14,
        warranty_requirement_months: int = 24,
    ) -> PurchaseRequest:
        req_id = str(uuid.uuid4())
        req = PurchaseRequest(
            request_id=req_id,
            requester=requester,
            raw_request_text=raw_request_text,
            product_requirements=product_requirements,
            quantity=quantity,
            budget_limit=budget_limit,
            currency=currency,
            delivery_deadline_days=delivery_deadline_days,
            warranty_requirement_months=warranty_requirement_months,
            status="SUBMITTED",
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def get_purchase_request(self, request_id: str) -> Optional[PurchaseRequest]:
        return self.db.scalar(select(PurchaseRequest).where(PurchaseRequest.request_id == request_id))

    def get_all_purchase_requests(self, limit: int = 50) -> List[PurchaseRequest]:
        return list(self.db.scalars(select(PurchaseRequest).order_by(desc(PurchaseRequest.created_at)).limit(limit)).all())

    def update_purchase_request_status(self, request_id: str, status: str):
        req = self.get_purchase_request(request_id)
        if req:
            req.status = status
            self.db.commit()

    # --- Vendor Quotes ---
    def create_quote(
        self,
        request_id: str,
        vendor_id: str,
        unit_price: Decimal,
        quantity: int,
        discount: Decimal,
        tax: Decimal,
        shipping_cost: Decimal,
        total_amount: Decimal,
        delivery_days: int,
        warranty_months: int,
        availability_status: str,
        calculation_breakdown: Dict[str, Any],
    ) -> VendorQuote:
        quote = VendorQuote(
            quote_id=str(uuid.uuid4()),
            request_id=request_id,
            vendor_id=vendor_id,
            unit_price=unit_price,
            quantity=quantity,
            discount=discount,
            tax=tax,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            delivery_days=delivery_days,
            warranty_months=warranty_months,
            availability_status=availability_status,
            quote_status="RECEIVED",
            calculation_breakdown=calculation_breakdown,
        )
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        return quote

    def get_quotes_by_request(self, request_id: str) -> List[VendorQuote]:
        return list(self.db.scalars(select(VendorQuote).where(VendorQuote.request_id == request_id)).all())

    def get_quote_by_id(self, quote_id: str) -> Optional[VendorQuote]:
        return self.db.scalar(select(VendorQuote).where(VendorQuote.quote_id == quote_id))

    # --- Compliance Rules ---
    def get_active_compliance_rules(self) -> List[ComplianceRule]:
        return list(self.db.scalars(select(ComplianceRule).where(ComplianceRule.active_status == True)).all())

    # --- Evaluations ---
    def save_evaluation(
        self,
        request_id: str,
        quote_id: str,
        price_score: Decimal,
        delivery_score: Decimal,
        warranty_score: Decimal,
        compliance_score: Decimal,
        specification_score: Decimal,
        final_score: Decimal,
        eligibility_status: str,
        explanation: str,
        exclusion_reason: Optional[str] = None,
        rank: Optional[int] = None,
    ) -> Evaluation:
        eval_obj = self.db.scalar(select(Evaluation).where(Evaluation.quote_id == quote_id))
        if eval_obj:
            eval_obj.price_score = price_score
            eval_obj.delivery_score = delivery_score
            eval_obj.warranty_score = warranty_score
            eval_obj.compliance_score = compliance_score
            eval_obj.specification_score = specification_score
            eval_obj.final_score = final_score
            eval_obj.eligibility_status = eligibility_status
            eval_obj.explanation = explanation
            eval_obj.exclusion_reason = exclusion_reason
            eval_obj.rank = rank
        else:
            eval_obj = Evaluation(
                evaluation_id=str(uuid.uuid4()),
                request_id=request_id,
                quote_id=quote_id,
                price_score=price_score,
                delivery_score=delivery_score,
                warranty_score=warranty_score,
                compliance_score=compliance_score,
                specification_score=specification_score,
                final_score=final_score,
                eligibility_status=eligibility_status,
                explanation=explanation,
                exclusion_reason=exclusion_reason,
                rank=rank,
            )
            self.db.add(eval_obj)
        self.db.commit()
        self.db.refresh(eval_obj)
        return eval_obj

    def get_evaluations_by_request(self, request_id: str) -> List[Evaluation]:
        return list(
            self.db.scalars(
                select(Evaluation).where(Evaluation.request_id == request_id).order_by(desc(Evaluation.final_score))
            ).all()
        )

    # --- Negotiations ---
    def save_negotiation(
        self,
        request_id: str,
        quote_id: str,
        original_amount: Decimal,
        target_amount: Decimal,
        counter_offer_amount: Decimal,
        justification: str,
        draft_message: str,
        negotiation_status: str = "PROPOSED",
    ) -> Negotiation:
        neg = self.db.scalar(select(Negotiation).where(Negotiation.quote_id == quote_id))
        if neg:
            neg.original_amount = original_amount
            neg.target_amount = target_amount
            neg.counter_offer_amount = counter_offer_amount
            neg.justification = justification
            neg.draft_message = draft_message
            neg.negotiation_status = negotiation_status
        else:
            neg = Negotiation(
                negotiation_id=str(uuid.uuid4()),
                request_id=request_id,
                quote_id=quote_id,
                original_amount=original_amount,
                target_amount=target_amount,
                counter_offer_amount=counter_offer_amount,
                justification=justification,
                draft_message=draft_message,
                negotiation_status=negotiation_status,
            )
            self.db.add(neg)
        self.db.commit()
        self.db.refresh(neg)
        return neg

    def get_negotiations_by_request(self, request_id: str) -> List[Negotiation]:
        return list(self.db.scalars(select(Negotiation).where(Negotiation.request_id == request_id)).all())

    def get_negotiation_by_id(self, negotiation_id: str) -> Optional[Negotiation]:
        return self.db.scalar(select(Negotiation).where(Negotiation.negotiation_id == negotiation_id))

    # --- Approvals ---
    def create_approval(
        self,
        request_id: str,
        quote_id: str,
        risk_assessment: Dict[str, Any],
        approval_reason: str,
        requested_by: str = "DealForge AI System",
    ) -> Approval:
        approval = Approval(
            approval_id=str(uuid.uuid4()),
            request_id=request_id,
            quote_id=quote_id,
            risk_assessment=risk_assessment,
            approval_reason=approval_reason,
            requested_by=requested_by,
            decision="PENDING",
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def get_pending_approvals(self) -> List[Approval]:
        return list(
            self.db.scalars(
                select(Approval).where(Approval.decision == "PENDING").order_by(desc(Approval.created_at))
            ).all()
        )

    def get_approval_by_id(self, approval_id: str) -> Optional[Approval]:
        return self.db.scalar(select(Approval).where(Approval.approval_id == approval_id))

    def record_approval_decision(
        self,
        approval_id: str,
        decision: str,
        decided_by: str,
        comments: Optional[str] = None,
    ) -> Optional[Approval]:
        approval = self.get_approval_by_id(approval_id)
        if approval:
            approval.decision = decision
            approval.decided_by = decided_by
            approval.comments = comments
            approval.decided_at = utc_now()
            self.db.commit()
            self.db.refresh(approval)
        return approval

    # --- Purchase Orders ---
    def get_purchase_order_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        return self.db.scalar(select(PurchaseOrder).where(PurchaseOrder.order_number == order_number))

    def get_purchase_order_by_request(self, request_id: str) -> Optional[PurchaseOrder]:
        return self.db.scalar(select(PurchaseOrder).where(PurchaseOrder.request_id == request_id))

    def get_all_purchase_orders(self) -> List[PurchaseOrder]:
        return list(self.db.scalars(select(PurchaseOrder).order_by(desc(PurchaseOrder.created_at))).all())

    def create_purchase_order(
        self,
        request_id: str,
        vendor_id: str,
        quote_id: str,
        approved_total: Decimal,
        approved_by: str,
        currency: str = "INR",
        order_details: Optional[Dict[str, Any]] = None,
    ) -> PurchaseOrder:
        # Idempotency check: don't create duplicate PO for same request
        existing_po = self.get_purchase_order_by_request(request_id)
        if existing_po:
            return existing_po

        # Generate unique formal PO number
        count = self.db.query(PurchaseOrder).count() + 1
        order_number = f"PO-DF-{datetime.date.today().year}-{count:04d}"
        while self.get_purchase_order_by_order_number(order_number):
            count += 1
            order_number = f"PO-DF-{datetime.date.today().year}-{count:04d}"

        po = PurchaseOrder(
            purchase_order_id=str(uuid.uuid4()),
            request_id=request_id,
            vendor_id=vendor_id,
            quote_id=quote_id,
            order_number=order_number,
            approved_total=approved_total,
            currency=currency,
            status="ISSUED",
            approved_by=approved_by,
            order_details=order_details or {},
        )
        self.db.add(po)
        self.db.commit()
        self.db.refresh(po)
        return po

    # --- Workflow State Persistence ---
    def save_workflow_state(
        self,
        workflow_id: str,
        request_id: str,
        current_step: str,
        status: str,
        state_data: Dict[str, Any],
        last_error: Optional[str] = None,
    ) -> WorkflowState:
        state = self.db.scalar(select(WorkflowState).where(WorkflowState.workflow_id == workflow_id))
        if state:
            state.current_step = current_step
            state.status = status
            state.state_data = state_data
            state.last_error = last_error
        else:
            state = WorkflowState(
                workflow_id=workflow_id,
                request_id=request_id,
                current_step=current_step,
                status=status,
                state_data=state_data,
                last_error=last_error,
            )
            self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        return self.db.scalar(select(WorkflowState).where(WorkflowState.workflow_id == workflow_id))

    def get_workflow_state_by_request(self, request_id: str) -> Optional[WorkflowState]:
        return self.db.scalar(select(WorkflowState).where(WorkflowState.request_id == request_id))

    # --- Agent Audit Logs ---
    def log_agent_event(
        self,
        workflow_id: str,
        request_id: str,
        agent_name: str,
        event_type: str,
        status: str = "SUCCESS",
        input_summary: Optional[str] = None,
        output_summary: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> AgentLog:
        log_entry = AgentLog(
            log_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            request_id=request_id,
            agent_name=agent_name,
            event_type=event_type,
            status=status,
            input_summary=input_summary,
            output_summary=output_summary,
            error_message=error_message,
            metadata_json=metadata_json or {},
            started_at=utc_now(),
            completed_at=utc_now(),
        )
        self.db.add(log_entry)
        self.db.commit()
        return log_entry

    def get_workflow_logs(self, workflow_id: str) -> List[AgentLog]:
        logs = list(
            self.db.scalars(
                select(AgentLog).where(AgentLog.workflow_id == workflow_id).order_by(AgentLog.started_at)
            ).all()
        )
        # Ensure chronological step order: STEP_START always precedes STEP_COMPLETE within identical second timestamps
        def log_order_key(log: AgentLog):
            # 0 for START, 1 for PROGRESS/TOOL, 2 for COMPLETE/SUCCESS/DECISION
            if "START" in log.event_type or log.status == "PENDING":
                weight = 0
            elif "COMPLETE" in log.event_type or log.status == "SUCCESS":
                weight = 2
            else:
                weight = 1
            return (log.started_at, weight)

        logs.sort(key=log_order_key)
        return logs
