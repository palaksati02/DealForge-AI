# DealForge AI — API Specification and Endpoint Reference

The DealForge AI platform exposes a production-ready RESTful API with Server-Sent Events (SSE) support under `/api`.

Interactive Swagger UI documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 1. Authentication & RBAC (`/api/auth`)

### `POST /api/auth/login`
Authenticates a user and returns a signed JWT bearer token.
- **Request Body:**
  ```json
  {
    "email": "manager@dealforge.ai",
    "password": "Manager@123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "user_id": "user-mgr-01",
      "email": "manager@dealforge.ai",
      "full_name": "Rajesh Sharma (Procurement Lead)",
      "role_name": "Procurement Manager",
      "department": "Global Procurement"
    }
  }
  ```

### `GET /api/auth/me`
Retrieves the profile of the authenticated user.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** `UserProfileResponse`

---

## 2. Procurement Lifecycle (`/api/procurement`)

### `POST /api/procurement/requests`
Submits a natural-language purchase request and initiates multi-agent orchestration.
- **Request Body:**
  ```json
  {
    "requester": "Engineering Department",
    "raw_request_text": "Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, a maximum budget of ₹38,00,000, delivery within 14 days, and a minimum two-year warranty.",
    "quantity_override": 50,
    "budget_override": 3800000.0,
    "deadline_override_days": 14,
    "warranty_override_months": 24,
    "category_override": "Laptops"
  }
  ```
- **Response (201 Created):** `PurchaseRequestResponse`

### `GET /api/procurement/requests/{request_id}/status`
Fetches the active workflow state and chronological agent audit logs.
- **Response (200 OK):**
  ```json
  {
    "workflow_id": "wf-1234-abcd",
    "request_id": "req-5678-efgh",
    "current_step": "AWAITING_APPROVAL",
    "status": "PAUSED",
    "state_data": {
      "approval_id": "appr-001",
      "approval_reason": "Total procurement amount ₹3,727,000.00 exceeds auto-approval threshold of ₹1,000,000.00."
    },
    "logs": [...]
  }
  ```

### `GET /api/procurement/requests/{request_id}/report`
Generates a complete, auditable multi-agent procurement dossier.
- **Response (200 OK):**
  - `request_details`: Formatted request parameters
  - `vendor_matrix`: Full multi-criteria comparison table with scores & rankings
  - `negotiations`: Target prices, counter-offers, and projected savings
  - `approvals`: Governance audit logs and decisions
  - `purchase_order`: Committed order details (if finalized)
  - `agent_execution_logs`: Complete chronological agent trail
  - `markdown_report`: Formatted executive Markdown document

### `POST /api/procurement/requests/{request_id}/approval`
Submits human approval or rejection for a paused workflow.
- **Request Body:**
  ```json
  {
    "decision": "APPROVED",
    "decided_by": "Priya Venkatesh",
    "comments": "Approved as technical compliance and budget thresholds are met."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "workflow_id": "wf-1234-abcd",
    "status": "COMPLETED",
    "current_step": "FINALIZED",
    "decision": "APPROVED",
    "order_number": "PO-DF-2026-94812",
    "approved_total": 3727000.0
  }
  ```

### `POST /api/procurement/requests/{request_id}/replan`
Triggers dynamic replanning when conditions change.
- **Triggers:** `BUDGET_CUT`, `VENDOR_STOCKOUT`, `NEGOTIATION_REJECTION`
- **Request Body:**
  ```json
  {
    "trigger_type": "BUDGET_CUT",
    "new_budget": 3200000.0
  }
  ```

### `GET /api/procurement/workflows/{workflow_id}/stream`
Server-Sent Events (SSE) streaming real-time agent execution events directly to clients.

---

## 3. Operational Dashboards & Records

- `GET /api/dashboard/summary`: Aggregate counts, committed spend, projected savings, and recent records.
- `GET /api/vendors`: Active supplier directory and performance ratings.
- `GET /api/purchase-orders`: Full database ledger of issued purchase commitments.
- `GET /api/procurement/policies`: Corporate procurement governance rules.
- `GET /api/procurement/audit-logs`: Chronological corporate audit entries.

---

## 4. A2A Inter-Agent Protocol (`/a2a/*`)

- `GET /a2a/{service}/.well-known/agent-card.json`: Returns RFC-compliant Agent Card metadata.
- `POST /a2a/{service}/tasks`: Dispatches a task to the agent service.
- `GET /a2a/{service}/tasks/{task_id}`: Retrieves task execution status.
