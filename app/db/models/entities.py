import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Integer, Numeric, Boolean, Text, DateTime, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, utc_now


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # Procurement Manager, Finance Reviewer, Administrator
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.role_id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    vendor_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("4.00"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    vendor_products: Mapped[List["VendorProduct"]] = relationship("VendorProduct", back_populates="vendor", cascade="all, delete-orphan")
    quotes: Mapped[List["VendorQuote"]] = relationship("VendorQuote", back_populates="vendor")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="vendor")
    certifications: Mapped[List["VendorCertification"]] = relationship("VendorCertification", back_populates="vendor", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    specifications: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    vendor_products: Mapped[List["VendorProduct"]] = relationship("VendorProduct", back_populates="product", cascade="all, delete-orphan")


class VendorProduct(Base):
    __tablename__ = "vendor_products"

    vendor_product_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    delivery_days: Mapped[int] = mapped_column(Integer, default=7)
    warranty_months: Mapped[int] = mapped_column(Integer, default=12)
    minimum_order_quantity: Mapped[int] = mapped_column(Integer, default=1)
    discount_rules: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="vendor_products")
    product: Mapped["Product"] = relationship("Product", back_populates="vendor_products")


class VendorCertification(Base):
    __tablename__ = "vendor_certifications"

    certification_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False, index=True)
    certification_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # ISO 9001, ISO 27001, BIS, RoHS, CE
    issued_by: Mapped[str] = mapped_column(String(255), nullable=False)
    valid_from: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED", index=True)  # VERIFIED, EXPIRED, UNKNOWN
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="certifications")


class ProcurementPolicy(Base):
    __tablename__ = "procurement_policies"

    policy_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # POL-AUTO-APP, POL-ISO-REQ, POL-WARR-MIN
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="GENERAL")
    threshold_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("1000000.00"))
    mandatory_certifications: Mapped[List[str]] = mapped_column(JSON, default=list)
    min_warranty_months: Mapped[int] = mapped_column(Integer, default=24)
    max_delivery_days: Mapped[int] = mapped_column(Integer, default=14)
    requires_finance_review: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    rule_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)  # VENDOR_ACTIVE, MIN_WARRANTY, MAX_DELIVERY, ISO_CERTIFICATION, MOQ_CHECK
    threshold: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    mandatory_flag: Mapped[bool] = mapped_column(Boolean, default=True)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True)


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    requester: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_request_text: Mapped[str] = mapped_column(Text, nullable=False)
    product_requirements: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    delivery_deadline_days: Mapped[int] = mapped_column(Integer, default=14)
    warranty_requirement_months: Mapped[int] = mapped_column(Integer, default=24)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    items: Mapped[List["ProcurementItem"]] = relationship("ProcurementItem", back_populates="request", cascade="all, delete-orphan")
    quotes: Mapped[List["VendorQuote"]] = relationship("VendorQuote", back_populates="request", cascade="all, delete-orphan")
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="request", cascade="all, delete-orphan")
    negotiations: Mapped[List["Negotiation"]] = relationship("Negotiation", back_populates="request", cascade="all, delete-orphan")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="request", cascade="all, delete-orphan")
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="request")
    workflow_state: Mapped[Optional["WorkflowState"]] = relationship("WorkflowState", back_populates="request", uselist=False, cascade="all, delete-orphan")
    audit_logs: Mapped[List["ProcurementAuditLog"]] = relationship("ProcurementAuditLog", back_populates="request", cascade="all, delete-orphan")


class ProcurementItem(Base):
    __tablename__ = "procurement_items"

    item_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    specifications: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    target_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="items")


class VendorQuote(Base):
    __tablename__ = "vendor_quotes"

    quote_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendors.vendor_id"), nullable=False, index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    delivery_days: Mapped[int] = mapped_column(Integer, nullable=False)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False)
    availability_status: Mapped[str] = mapped_column(String(50), default="IN_STOCK")  # IN_STOCK, PARTIAL, OUT_OF_STOCK
    quote_status: Mapped[str] = mapped_column(String(50), default="RECEIVED")  # RECEIVED, EVALUATED, SELECTED, REJECTED, NEGOTIATED
    calculation_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="quotes")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="quotes")
    evaluation: Mapped[Optional["Evaluation"]] = relationship("Evaluation", back_populates="quote", uselist=False, cascade="all, delete-orphan")
    negotiation: Mapped[Optional["Negotiation"]] = relationship("Negotiation", back_populates="quote", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), nullable=False, index=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendor_quotes.quote_id", ondelete="CASCADE"), nullable=False, index=True)
    price_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    delivery_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    warranty_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    compliance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    specification_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    final_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), index=True)
    eligibility_status: Mapped[str] = mapped_column(String(50), default="ELIGIBLE")  # ELIGIBLE, INELIGIBLE
    exclusion_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="evaluations")
    quote: Mapped["VendorQuote"] = relationship("VendorQuote", back_populates="evaluation")


class Negotiation(Base):
    __tablename__ = "negotiations"

    negotiation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), nullable=False, index=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendor_quotes.quote_id", ondelete="CASCADE"), nullable=False, index=True)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    counter_offer_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    draft_message: Mapped[str] = mapped_column(Text, nullable=False)
    negotiation_status: Mapped[str] = mapped_column(String(50), default="PROPOSED")  # PROPOSED, SENT, ACCEPTED, COUNTERED, REJECTED
    vendor_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="negotiations")
    quote: Mapped["VendorQuote"] = relationship("VendorQuote", back_populates="negotiation")


class Approval(Base):
    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), nullable=False, index=True)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendor_quotes.quote_id"), nullable=False)
    risk_assessment: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    approval_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(255), default="System Workflow")
    decision: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED, REVISION_REQUESTED
    decided_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approver_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="approvals")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    purchase_order_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id"), nullable=False, index=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendors.vendor_id"), nullable=False)
    quote_id: Mapped[str] = mapped_column(String(36), ForeignKey("vendor_quotes.quote_id"), nullable=False)
    order_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    approved_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[str] = mapped_column(String(50), default="ISSUED", index=True)  # ISSUED, COMPLETED, CANCELLED
    approved_by: Mapped[str] = mapped_column(String(255), nullable=False)
    order_details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="purchase_orders")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="purchase_orders")


class ProcurementAuditLog(Base):
    __tablename__ = "procurement_audit_logs"

    audit_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # CREATE_REQUEST, SUBMIT_APPROVAL, APPROVE, REJECT, REPLAN, ISSUE_PO
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now, index=True)

    # Relationships
    request: Mapped[Optional["PurchaseRequest"]] = relationship("PurchaseRequest", back_populates="audit_logs")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # STEP_START, STEP_COMPLETE, TOOL_CALL, DECISION, ERROR, REPLAN
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS")  # SUCCESS, WARNING, ERROR, PENDING
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class WorkflowState(Base):
    __tablename__ = "workflow_states"

    workflow_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requests.request_id", ondelete="CASCADE"), unique=True, nullable=False)
    current_step: Mapped[str] = mapped_column(String(100), default="INIT")
    status: Mapped[str] = mapped_column(String(50), default="RUNNING")
    state_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    request: Mapped["PurchaseRequest"] = relationship("PurchaseRequest", back_populates="workflow_state")
