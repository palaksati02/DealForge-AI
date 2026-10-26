export interface User {
  user_id: string;
  email: string;
  full_name: string;
  role_name: string;
  department?: string;
}

export interface PurchaseRequest {
  request_id: string;
  requester: string;
  raw_request_text: string;
  product_requirements: Record<string, any>;
  quantity: number;
  budget_limit: number;
  currency: string;
  delivery_deadline_days: number;
  warranty_requirement_months: number;
  status: string;
  created_at: string;
}

export interface AgentLog {
  log_id: string;
  workflow_id: string;
  agent_name: string;
  event_type: string;
  status: string;
  input_summary?: string;
  output_summary?: string;
  started_at: string;
  completed_at?: string;
}

export interface WorkflowStatus {
  workflow_id: string;
  request_id: string;
  current_step: string;
  status: string;
  state_data?: Record<string, any>;
  last_error?: string;
  logs: AgentLog[];
}

export interface VendorQuote {
  quote_id: string;
  vendor_id: string;
  vendor_name: string;
  vendor_rating?: number;
  unit_price: number;
  quantity: number;
  discount: number;
  shipping_cost: number;
  total_amount: number;
  delivery_days: number;
  warranty_months: number;
  eligibility_status: string;
  exclusion_reason?: string;
  final_score: number;
  rank?: number;
}

export interface NegotiationItem {
  negotiation_id: string;
  original_amount: number;
  target_amount: number;
  counter_offer_amount: number;
  savings: number;
  justification: string;
  status: string;
  vendor_response?: string;
}

export interface ApprovalItem {
  approval_id: string;
  request_id: string;
  quote_id: string;
  vendor_name?: string;
  total_amount?: number;
  budget_limit?: number;
  approval_reason: string;
  requested_by: string;
  decision: string;
  decided_by?: string;
  comments?: string;
  risk_assessment?: Record<string, any>;
  created_at: string;
}

export interface PurchaseOrderItem {
  purchase_order_id: string;
  request_id: string;
  order_number: string;
  vendor_name: string;
  approved_total: number;
  currency: string;
  status: string;
  approved_by: string;
  created_at: string;
}

export interface DashboardSummary {
  total_requests: number;
  active_workflows: number;
  pending_approvals: number;
  issued_purchase_orders: number;
  total_spend_approved: number;
  estimated_savings: number;
  average_vendor_rating: number;
  recent_requests: PurchaseRequest[];
  recent_purchase_orders: PurchaseOrderItem[];
}

export interface ProcurementReport {
  request_id: string;
  workflow_id?: string;
  status: string;
  generated_at: string;
  request_details: Record<string, any>;
  vendor_matrix: VendorQuote[];
  negotiations: NegotiationItem[];
  approvals: Record<string, any>[];
  purchase_order?: Record<string, any>;
  agent_execution_logs: AgentLog[];
  markdown_report: string;
}
