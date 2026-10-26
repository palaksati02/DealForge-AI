# DealForge AI — Security Architecture & Governance Specification

## 1. Executive Summary

DealForge AI implements enterprise-grade security and governance controls designed for corporate procurement operations. The platform guarantees:
1. **Confidentiality & Integrity**: Role-Based Access Control (RBAC), bcrypt-hashed credentials, signed JSON Web Tokens (JWT), and parameter-validated API surfaces.
2. **Deterministic Governance**: Multi-tier monetary thresholds, mandatory human approval gates, and tamper-resistant audit logs.
3. **Defense-in-Depth**: Strict separation of concerns between agent orchestration, tool execution (MCP), inter-service communications (A2A), and database persistence (SQLAlchemy 2.x parameterized queries).

---

## 2. Authentication & Session Security

### 2.1 Password Hashing
- DealForge AI uses **bcrypt** with automatic cryptographic salt generation.
- Passwords are never stored in plaintext or reversible formats.
- Seed users and new user registrations pass through `bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())`.
- Verification utilizes constant-time comparison `bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))` to protect against timing attacks.

### 2.2 JSON Web Tokens (JWT)
- **Token Type**: Bearer authentication standard (`RFC 6750`).
- **Signature Algorithm**: HMAC-SHA256 (`HS256`).
- **Configuration**:
  - `JWT_SECRET`: Loaded strictly from environment variable; defaults to a cryptographically secure random sequence in production.
  - `JWT_ALGORITHM`: `HS256`.
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: Configurable (default: 480 minutes / 8 hours).
- **Claims Carried**:
  - `sub`: User email / username.
  - `user_id`: Integer primary key of the authenticated user.
  - `role`: Canonical role name string (`PROCUREMENT_MANAGER`, `FINANCE_APPROVER`, `SYSTEM_ADMIN`).
  - `exp`: Unix timestamp defining token expiration.

### 2.3 Authentication Endpoints
- `POST /api/auth/login`: Accepts `{"email": "...", "password": "..."}` or OAuth2 password form fields. Returns access token, token type, and user profile with role.
- `GET /api/auth/me`: Validates bearer token and returns current user context.
- `GET /api/auth/users`: Protected endpoint (Admin and Manager roles) listing seeded/system users for development or assignment.

---

## 3. Role-Based Access Control (RBAC)

DealForge AI enforces strict principle-of-least-privilege RBAC using FastAPI dependency injection (`require_role([...])` and `get_current_user`).

### 3.1 Role Hierarchy & Permissions

| Role | Permitted Actions | Prohibited Actions |
|---|---|---|
| **`PROCUREMENT_MANAGER`** | Submit purchase requests, run multi-agent workflows, initiate negotiations, view live matrices, download reports. | Approve requests exceeding their spending threshold (₹10,00,000), modify global compliance policies, delete audit records. |
| **`FINANCE_APPROVER`** | Review high-value proposals, inspect Google ADK risk audits, approve/reject procurement decisions, authorize PO release. | Initiate new procurement runs, bypass compliance failure blocks without formal replanning. |
| **`SYSTEM_ADMIN`** | Update system compliance policies, configure vendor catalogs, inspect all audit logs, manage users, perform emergency overrides. | Authorize self-issued procurement purchases without two-person separation of duties. |

### 3.2 Endpoint Access Control Matrix

| Endpoint | Method | Required Roles / Access Level |
|---|---|---|
| `/api/auth/login` | POST | Public |
| `/api/procurement/requests` | POST | `PROCUREMENT_MANAGER`, `FINANCE_APPROVER`, `SYSTEM_ADMIN` |
| `/api/procurement/requests/{id}/status` | GET | Authenticated (Any valid role) |
| `/api/procurement/requests/{id}/report` | GET | Authenticated (Any valid role) |
| `/api/procurement/requests/{id}/approval` | POST | `FINANCE_APPROVER`, `SYSTEM_ADMIN` (Enforced governance gate) |
| `/api/procurement/requests/{id}/replan` | POST | `PROCUREMENT_MANAGER`, `SYSTEM_ADMIN` |
| `/api/procurement/policies` | GET | Authenticated (Any valid role) |
| `/api/procurement/audit-logs` | GET | Authenticated (Audit trail review) |
| `/api/procurement/workflows/{id}/stream` | GET | Authenticated (Real-time SSE event feed) |

---

## 4. Financial Governance & Approval State Machine

### 4.1 Financial Approval Thresholds
- **Tier 1 (Auto-Approval Eligible)**: Deals $\le ₹10,00,000$ with zero policy violations and risk score $< 40$.
- **Tier 2 (Mandatory Finance Approval)**:
  - Total PO amount $> ₹10,00,000$ ($10\text{ Lakhs}$).
  - Budget overrun of any magnitude.
  - Google ADK risk score $\ge 40/100$ or flagged compliance warnings.
  - Delivery SLA variance or single-source vendor selection.

### 4.2 State Machine Transitions & Safeguards

```
[NEW REQUEST]
      │
      ▼
[ANALYZING / QUOTING]
      │
      ▼
[COMPLIANCE_EVALUATION]
      ├── Failure (Hard) ──► [REPLANNING_REQUIRED] ──► [REPLAN_INITIATED]
      │                                                        │
      └── Pass                                                 │
            │                                                  │
            ▼                                                  ▼
     [PRICE_RANKING] ◄─────────────────────────────────────────┘
            │
            ▼
    [RISK_ASSESSMENT]
            │
            ├── Auto-Approve (Amount <= 10L & Low Risk) ──► [APPROVED] ──► [PO_ISSUED]
            │
            └── Over-Threshold / High-Risk
                      │
                      ▼
            [WAITING_FOR_APPROVAL]
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
     [APPROVED]             [REJECTED]
           │                     │
           ▼                     ▼
      [PO_ISSUED]          [TERMINATED]
```

### 4.3 Idempotency & Duplicate PO Prevention
- **Unique Constraint**: Purchase Orders are generated with a deterministic, idempotent key derived from `request_id` (format: `PO-REQ-{id:04d}-{hash}`).
- **Database Unique Index**: `purchase_orders.po_number` and `purchase_orders.request_id` are strictly enforced unique keys.
- **Workflow State Verification**: A PO is generated only when the workflow transitions from `APPROVED` to `PO_ISSUED`. Attempting to approve an already approved request returns HTTP 400 with `Request is already approved/issued`.

---

## 5. Input Validation, Injection Defense & Data Integrity

### 5.1 Parameterized SQL Queries (SQLAlchemy 2.x)
- **Zero Raw String Concatenation**: All database operations in `ProcurementRepository` utilize SQLAlchemy ORM `select()`, `update()`, and parameterized filters (`where(Model.attribute == value)`).
- **Protection**: SQL injection through input prompts, vendor names, or product IDs is completely mitigated at the driver level.

### 5.2 Pydantic V2 Strict Schema Validation
- All inbound JSON bodies are parsed into strongly typed Pydantic models with explicit field constraints:
  - `budget_limit`: `condecimal(gt=0)`
  - `quantity`: `conint(gt=0)`
  - `max_delivery_days`: `conint(gt=0)`
  - `status`: Enumerated whitelist strings (`APPROVED`, `REJECTED`, etc.)
- Unexpected or malicious keys are rejected with structured HTTP 422 Unprocessable Entity responses.

### 5.3 Deterministic Decimal Financial Math
- Floating-point arithmetic is strictly prohibited in financial paths:
  - Base subtotals, bulk discount percentages, 18% GST calculations, freight surcharges, and total spend are calculated using Python `Decimal` (`ROUND_HALF_UP`).
  - Stored in MySQL as `DECIMAL(15, 2)`.
  - Eliminates IEEE 754 precision rounding vulnerabilities.

---

## 6. Audit Logging & Non-Repudiation

### 6.1 Relational Audit Trail (`procurement_audit_logs`)
Every state change, approval decision, human override, and financial commitment is recorded to the `procurement_audit_logs` table with:
- `log_id`: Auto-incrementing primary key.
- `request_id`: Foreign key reference to `purchase_requests`.
- `action`: Canonical action string (e.g., `WORKFLOW_STARTED`, `VENDOR_EVALUATED`, `APPROVAL_GRANTED`, `PO_GENERATED`).
- `actor`: User email, service name, or agent card identifier.
- `details`: Structured JSON snapshot of parameters, scores, and rationale.
- `created_at`: UTC timestamp.

### 6.2 Agent Execution Logs (`agent_logs`)
- Every ADK agent step, CrewAI specialist action, MCP tool invocation, and A2A envelope transmission records execution latency, payload summaries, and outcome status (`SUCCESS`, `WARNING`, `FAILED`).
- Provides deep observability for forensic debugging and compliance audits.

---

## 7. Model Context Protocol (MCP) & A2A Isolation

### 7.1 FastMCP Boundary Controls
- FastMCP tool server executes read-only operations for vendor research and quotes.
- State-mutating tools (e.g., recording approved quotes or creating purchase orders) require verified request contexts.
- No arbitrary code execution or unvalidated system shell access tools exist within the MCP server definition.

### 7.2 A2A Communication Integrity
- A2A endpoints communicate via standardized JSON envelopes:
  - Sender and recipient URIs (`agent://orchestrator/adk-core` $\rightarrow$ `agent://analysis/crewai-specialist`).
  - Strict payload typing and message IDs.
  - Fail-safe fallback: If an external agent service times out or errors, the caller defaults to a conservative fail-safe state (`HIGH_RISK`, `REQUIRES_HUMAN_INTERVENTION`) rather than silently skipping safety checks.

---

## 8. Secrets & Environment Configuration

- **Zero Hardcoded Secrets**: Secrets and database credentials must never be committed to git.
- **Environment Template**: `.env.example` documents required variable names with safe placeholder tokens only.
- **Production Checklist**:
  1. Generate a 256-bit random string for `JWT_SECRET` (`openssl rand -hex 32`).
  2. Set strong MySQL credentials (`DB_PASSWORD`).
  3. Ensure `DEMO_MODE=False` in production to enforce strict production credentials.
  4. Restrict CORS origins (`CORS_ORIGINS`) to authorized frontend domains.
