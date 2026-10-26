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
    Role,
    User,
    VendorCertification,
    ProcurementPolicy,
    ProcurementItem,
    ProcurementAuditLog,
)
from app.db.base import utc_now


def clean_json(data: Any) -> Any:
    if data is None:
        return {}
    if isinstance(data, dict):
        return {str(k): clean_json(v) for k, v in data.items()}
    if isinstance(data, (list, tuple, set)):
        return [clean_json(v) for v in data]
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, (datetime.datetime, datetime.date)):
        return data.isoformat()
    return data


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
            risk_assessment=clean_json(risk_assessment),
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
        cleaned_state = clean_json(state_data)
        state = self.db.scalar(select(WorkflowState).where(WorkflowState.workflow_id == workflow_id))
        if state:
            state.current_step = current_step
            state.status = status
            state.state_data = cleaned_state
            state.last_error = last_error
        else:
            state = WorkflowState(
                workflow_id=workflow_id,
                request_id=request_id,
                current_step=current_step,
                status=status,
                state_data=cleaned_state,
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
            metadata_json=clean_json(metadata_json or {}),
            started_at=utc_now(),
            completed_at=utc_now(),
        )
        self.db.add(log_entry)
        self.db.commit()
        return log_entry

    def get_workflow_logs(self, workflow_id: str) -> List[AgentLog]:
        return list(
            self.db.scalars(
                select(AgentLog).where(AgentLog.workflow_id == workflow_id).order_by(AgentLog.started_at)
            ).all()
        )

    # --- Roles & Users ---
    def create_role(self, role_name: str, description: Optional[str] = None, permissions: Optional[Dict[str, Any]] = None) -> Role:
        role = Role(
            role_id=str(uuid.uuid4()),
            role_name=role_name,
            description=description,
            permissions=permissions or {}
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_role_by_name(self, role_name: str) -> Optional[Role]:
        return self.db.scalar(select(Role).where(Role.role_name == role_name))

    def create_user(
        self,
        email: str,
        full_name: str,
        hashed_password: str,
        role_name: str,
        department: Optional[str] = None
    ) -> User:
        role = self.get_role_by_name(role_name)
        if not role:
            role = self.create_role(role_name=role_name)

        user = User(
            user_id=str(uuid.uuid4()),
            email=email.lower().strip(),
            full_name=full_name,
            hashed_password=hashed_password,
            role_id=role.role_id,
            department=department
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.email == email.lower().strip()))

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.user_id == user_id))

    def get_all_users(self) -> List[User]:
        return list(self.db.scalars(select(User)).all())

    # --- Vendor Certifications ---
    def add_vendor_certification(
        self,
        vendor_id: str,
        certification_name: str,
        issued_by: str,
        verification_status: str = "VERIFIED",
        valid_until: Optional[datetime.datetime] = None
    ) -> VendorCertification:
        cert = VendorCertification(
            certification_id=str(uuid.uuid4()),
            vendor_id=vendor_id,
            certification_name=certification_name,
            issued_by=issued_by,
            verification_status=verification_status,
            valid_until=valid_until
        )
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def get_vendor_certifications(self, vendor_id: str) -> List[VendorCertification]:
        return list(self.db.scalars(select(VendorCertification).where(VendorCertification.vendor_id == vendor_id)).all())

    # --- Procurement Policies ---
    def create_policy(
        self,
        policy_code: str,
        policy_name: str,
        threshold_amount: Decimal,
        mandatory_certifications: Optional[List[str]] = None,
        min_warranty_months: int = 24,
        max_delivery_days: int = 14,
        requires_finance_review: bool = True
    ) -> ProcurementPolicy:
        policy = ProcurementPolicy(
            policy_id=str(uuid.uuid4()),
            policy_code=policy_code,
            policy_name=policy_name,
            threshold_amount=threshold_amount,
            mandatory_certifications=mandatory_certifications or [],
            min_warranty_months=min_warranty_months,
            max_delivery_days=max_delivery_days,
            requires_finance_review=requires_finance_review
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def get_policy_by_code(self, policy_code: str) -> Optional[ProcurementPolicy]:
        return self.db.scalar(select(ProcurementPolicy).where(ProcurementPolicy.policy_code == policy_code))

    def get_all_policies(self) -> List[ProcurementPolicy]:
        return list(self.db.scalars(select(ProcurementPolicy).where(ProcurementPolicy.is_active == True)).all())

    # --- Procurement Items ---
    def add_procurement_item(
        self,
        request_id: str,
        product_name: str,
        category: str,
        quantity: int,
        specifications: Optional[Dict[str, Any]] = None,
        target_unit_price: Optional[Decimal] = None
    ) -> ProcurementItem:
        item = ProcurementItem(
            item_id=str(uuid.uuid4()),
            request_id=request_id,
            product_name=product_name,
            category=category,
            quantity=quantity,
            specifications=clean_json(specifications or {}),
            target_unit_price=target_unit_price
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_procurement_items(self, request_id: str) -> List[ProcurementItem]:
        return list(self.db.scalars(select(ProcurementItem).where(ProcurementItem.request_id == request_id)).all())

    # --- Procurement Audit Logs ---
    def log_procurement_audit(
        self,
        action: str,
        actor: str,
        request_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> ProcurementAuditLog:
        entry = ProcurementAuditLog(
            audit_id=str(uuid.uuid4()),
            request_id=request_id,
            action=action,
            actor=actor,
            actor_role=actor_role,
            details=clean_json(details or {}),
            ip_address=ip_address
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_audit_logs(self, request_id: Optional[str] = None, limit: int = 100) -> List[ProcurementAuditLog]:
        query = select(ProcurementAuditLog).order_by(desc(ProcurementAuditLog.timestamp))
        if request_id:
            query = query.where(ProcurementAuditLog.request_id == request_id)
        return list(self.db.scalars(query.limit(limit)).all())
