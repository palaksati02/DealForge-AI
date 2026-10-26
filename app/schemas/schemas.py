import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Authentication & User Schemas ---
class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    full_name: str
    role_name: str
    department: Optional[str] = None
    is_active: bool


# --- Requirement Analysis Schemas ---
class PurchaseRequestExtract(BaseModel):
    category: str = Field(..., description="Product category, e.g., Laptops, Servers, Displays")
    product_name_hint: Optional[str] = Field(None, description="Extracted product model or name hint")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="RAM, CPU, storage, display, etc.")
    quantity: int = Field(..., gt=0, description="Number of units required")
    budget_limit: Decimal = Field(..., gt=0, description="Maximum budget limit in target currency")
    currency: str = Field("INR", description="Currency code (e.g. INR)")
    delivery_deadline_days: int = Field(14, gt=0, description="Mandatory delivery deadline in calendar days")
    warranty_requirement_months: int = Field(24, ge=0, description="Mandatory minimum warranty in months")
    mandatory_certifications: List[str] = Field(default_factory=list, description="Required certifications, e.g. ISO 9001, RoHS, BIS")
    missing_fields: List[str] = Field(default_factory=list, description="List of any missing essential fields")
    is_clarification_needed: bool = Field(False, description="True if mandatory details are ambiguous or missing")
    clarification_question: Optional[str] = None
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)


class PurchaseRequestCreate(BaseModel):
    requester: str = Field("Procurement Officer", description="Name/Role of requester")
    raw_request_text: str = Field(..., min_length=5, description="Natural language request")
    category_override: Optional[str] = None
    quantity_override: Optional[int] = None
    budget_override: Optional[Decimal] = None
    deadline_override_days: Optional[int] = None
    warranty_override_months: Optional[int] = None


class PurchaseRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: str
    requester: str
    raw_request_text: str
    product_requirements: Dict[str, Any]
    quantity: int
    budget_limit: Decimal
    currency: str
    delivery_deadline_days: int
    warranty_requirement_months: int
    status: str
    created_at: datetime.datetime


# --- Vendor & Product Schemas ---
class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_id: str
    vendor_name: str
    contact_email: str
    phone: Optional[str]
    address: Optional[str]
    active_status: bool
    vendor_rating: Decimal


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    product_name: str
    category: str
    specifications: Dict[str, Any]


class VendorProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_product_id: str
    vendor_id: str
    product_id: str
    unit_price: Decimal
    currency: str
    stock_quantity: int
    delivery_days: int
    warranty_months: int
    minimum_order_quantity: int
    discount_rules: Dict[str, Any]
    vendor_name: Optional[str] = None
    product_name: Optional[str] = None


# --- Quote & Pricing Schemas ---
class QuoteCalculationBreakdown(BaseModel):
    base_subtotal: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    tax_rate_percentage: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    final_total: Decimal
    effective_unit_price: Decimal
    budget_utilization_percentage: Optional[Decimal] = None
    remaining_budget: Optional[Decimal] = None


class VendorQuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quote_id: str
    request_id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    unit_price: Decimal
    quantity: int
    discount: Decimal
    tax: Decimal
    shipping_cost: Decimal
    total_amount: Decimal
    delivery_days: int
    warranty_months: int
    availability_status: str
    quote_status: str
    calculation_breakdown: Dict[str, Any]
    created_at: datetime.datetime


# --- Budget Validation Schemas ---
class BudgetValidationResult(BaseModel):
    budget_limit: Decimal
    total_cost: Decimal
    is_valid: bool
    budget_status: str = "COMPLIANT_WITHIN_BUDGET"  # COMPLIANT_WITHIN_BUDGET, BUDGET_OVERRUN
    difference: Decimal  # Positive = surplus, Negative = overrun
    overrun_amount: Decimal
    required_approval_level: str = "NONE"  # NONE, PROCUREMENT_MANAGER, FINANCE_REVIEWER, EXECUTIVE_ESCALATION
    currency: str = "INR"
    explanation: str


# --- Compliance Schemas ---
class ComplianceCheckItem(BaseModel):
    rule_name: str
    rule_type: str
    status: str  # PASS, FAIL, UNKNOWN
    passed: bool  # True only if status == "PASS"
    mandatory: bool
    details: str


class ComplianceValidationResult(BaseModel):
    vendor_id: str
    is_compliant: bool
    overall_status: str  # PASS, FAIL, UNKNOWN
    checks: List[ComplianceCheckItem]
    failed_reasons: List[str]


# --- Evaluation Schemas ---
class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evaluation_id: str
    request_id: str
    quote_id: str
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    price_score: Decimal
    delivery_score: Decimal
    warranty_score: Decimal
    compliance_score: Decimal
    specification_score: Decimal
    final_score: Decimal
    eligibility_status: str  # ELIGIBLE, CONDITIONALLY_ELIGIBLE, INELIGIBLE
    exclusion_reason: Optional[str] = None
    explanation: str
    rank: Optional[int] = None


# --- Negotiation Schemas ---
class NegotiationBounds(BaseModel):
    target_price: Decimal
    maximum_acceptable_price: Decimal
    estimated_savings: Decimal
    is_estimate: bool = True
    justification: str


class NegotiationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    negotiation_id: str
    request_id: str
    quote_id: str
    vendor_name: Optional[str] = None
    original_amount: Decimal
    target_amount: Decimal
    counter_offer_amount: Decimal
    justification: str
    draft_message: str
    negotiation_status: str
    vendor_response: Optional[str] = None


class CounterOfferRequest(BaseModel):
    revised_counter_offer: Decimal = Field(..., gt=0)
    revised_message: Optional[str] = None
    simulate_vendor_reply: bool = Field(True, description="Whether to simulate vendor acceptance/rejection")


# --- Google ADK & A2A Risk Schemas ---
class RiskAssessmentSchema(BaseModel):
    risk_category: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    risk_score: Decimal = Field(..., description="Risk score between 0.00 and 100.00")
    risk_factors: List[str] = Field(default_factory=list)
    explanation: str
    recommended_action: str = Field(..., description="APPROVE, REVIEW, REJECT, ESCALATE")
    human_review_required: bool = True


# --- Approval Schemas ---
class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: str
    request_id: str
    quote_id: str
    vendor_name: Optional[str] = None
    total_amount: Optional[Decimal] = None
    budget_limit: Optional[Decimal] = None
    risk_assessment: Dict[str, Any]
    approval_reason: str
    requested_by: str
    decision: str
    decided_by: Optional[str]
    approver_role: Optional[str] = None
    comments: Optional[str]
    version: int = 1
    created_at: datetime.datetime
    decided_at: Optional[datetime.datetime]


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="APPROVED, REJECTED, or REVISION_REQUESTED")
    decided_by: str = Field("Procurement Manager", description="Identity of approver")
    approver_role: Optional[str] = Field(None, description="Role of approver")
    comments: Optional[str] = Field(None, description="Approval or rejection notes")


# --- Purchase Order Schemas ---
class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    purchase_order_id: str
    request_id: str
    vendor_id: str
    vendor_name: Optional[str] = None
    quote_id: str
    order_number: str
    approved_total: Decimal
    currency: str
    status: str
    approved_by: str
    order_details: Dict[str, Any]
    created_at: datetime.datetime


# --- Policy & Audit Schemas ---
class ProcurementPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_id: str
    policy_code: str
    policy_name: str
    category: str
    threshold_amount: Decimal
    mandatory_certifications: List[str]
    min_warranty_months: int
    max_delivery_days: int
    requires_finance_review: bool
    is_active: bool


class ProcurementAuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    request_id: Optional[str]
    action: str
    actor: str
    actor_role: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    timestamp: datetime.datetime


# --- Workflow & Agent Log Schemas ---
class AgentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    workflow_id: str
    request_id: str
    agent_name: str
    event_type: str
    status: str
    input_summary: Optional[str]
    output_summary: Optional[str]
    error_message: Optional[str]
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime]


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    request_id: str
    current_step: str
    status: str
    state_data: Dict[str, Any]
    last_error: Optional[str]
    logs: List[AgentLogResponse] = []


# --- Dashboard Summary ---
class DashboardSummaryResponse(BaseModel):
    total_requests: int
    active_workflows: int
    pending_approvals: int
    issued_purchase_orders: int
    total_spend_approved: Decimal
    estimated_savings: Decimal
    average_vendor_rating: Decimal
    recent_requests: List[PurchaseRequestResponse] = []
    recent_pos: List[PurchaseOrderResponse] = []
