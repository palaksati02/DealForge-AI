import {
  DashboardSummary,
  PurchaseRequest,
  WorkflowStatus,
  ProcurementReport,
  ApprovalItem,
  PurchaseOrderItem,
  User,
} from '../types';

const API_BASE = '/api';

export class ApiClient {
  private static token: string | null = localStorage.getItem('df_token');

  static setToken(token: string | null) {
    this.token = token;
    if (token) localStorage.setItem('df_token', token);
    else localStorage.removeItem('df_token');
  }

  static getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  // --- Auth & Users ---
  static async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Invalid email or password');
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  static async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch user profile');
    return res.json();
  }

  static async listUsers(): Promise<User[]> {
    const res = await fetch(`${API_BASE}/auth/users`);
    if (!res.ok) return [];
    return res.json();
  }

  // --- Dashboard ---
  static async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    if (!res.ok) throw new Error('Failed to load dashboard summary');
    return res.json();
  }

  // --- Requests ---
  static async createRequest(payload: {
    requester: string;
    raw_request_text: string;
    quantity_override?: number;
    budget_override?: number;
    deadline_override_days?: number;
    warranty_override_months?: number;
    category_override?: string;
  }): Promise<PurchaseRequest> {
    const res = await fetch(`${API_BASE}/procurement/requests?auto_start=true`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to submit purchase request');
    return res.json();
  }

  static async getRequest(requestId: string): Promise<PurchaseRequest> {
    const res = await fetch(`${API_BASE}/procurement/requests/${requestId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error('Request not found');
    return res.json();
  }

  static async listRequests(): Promise<PurchaseRequest[]> {
    const res = await fetch(`${API_BASE}/requests?limit=50`);
    if (!res.ok) return [];
    return res.json();
  }

  // --- Workflow ---
  static async getWorkflowStatus(requestId: string): Promise<WorkflowStatus> {
    const res = await fetch(`${API_BASE}/procurement/requests/${requestId}/status`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch workflow status');
    return res.json();
  }

  // --- Report ---
  static async getReport(requestId: string): Promise<ProcurementReport> {
    const res = await fetch(`${API_BASE}/procurement/requests/${requestId}/report`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load procurement report');
    return res.json();
  }

  // --- Approvals ---
  static async getPendingApprovals(): Promise<ApprovalItem[]> {
    const res = await fetch(`${API_BASE}/approvals/pending`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) return [];
    return res.json();
  }

  static async submitApprovalDecision(
    requestId: string,
    decision: 'APPROVED' | 'REJECTED',
    decidedBy: string,
    comments?: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/procurement/requests/${requestId}/approval`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        decision,
        decided_by: decidedBy,
        comments: comments || '',
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to record approval' }));
      throw new Error(err.detail || 'Approval failed');
    }
    return res.json();
  }

  // --- Replanning ---
  static async triggerReplan(
    requestId: string,
    triggerType: 'BUDGET_CUT' | 'VENDOR_STOCKOUT' | 'NEGOTIATION_REJECTION',
    payload: { new_budget?: number; vendor_id?: string; negotiation_id?: string; reason?: string }
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/procurement/requests/${requestId}/replan`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        trigger_type: triggerType,
        ...payload,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to replan' }));
      throw new Error(err.detail || 'Replanning failed');
    }
    return res.json();
  }

  // --- Purchase Orders ---
  static async listPurchaseOrders(): Promise<PurchaseOrderItem[]> {
    const res = await fetch(`${API_BASE}/purchase-orders`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) return [];
    return res.json();
  }

  // --- Audit Logs ---
  static async getAuditLogs(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/procurement/audit-logs`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) return [];
    return res.json();
  }
}
