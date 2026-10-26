# DealForge AI — Repository Audit and Technical Discovery Report

## Executive Summary

A comprehensive technical audit of the DealForge AI repository was conducted. DealForge AI is intended to be an Agentic Multi-Agent Procurement Automation System orchestrated by Google Agent Development Kit (ADK), utilizing CrewAI for specialized procurement analysis, Model Context Protocol (MCP) for tool exposure, genuine Agent-to-Agent (A2A) protocol communication, FastAPI, MySQL 8.x, SQLAlchemy 2.x, Alembic, and a React + TypeScript + Tailwind CSS frontend dashboard.

This audit establishes the baseline of existing implementations, identifies critical architectural inversions and structural gaps, and forms the foundation for the implementation roadmap.

---

## 1. Repository Inventory

| Directory / File | Type | Purpose | Current Implementation Status |
| :--- | :--- | :--- | :--- |
| `app/main.py` | Python / FastAPI | Application entrypoint | Configures FastAPI, mounts routers, static files, and ADK sub-app. Lacks auth middleware and request ID correlation. |
| `app/adk_service/agent.py` | Python | Google ADK Agent | Implements `ADKProcurementRiskAgent` using `google.adk.Agent`. Relegated to a secondary risk-scoring component instead of main orchestrator. |
| `app/adk_service/server.py` | Python / FastAPI | ADK Service HTTP Server | Exposes `/a2a/v1/message` endpoint receiving ad-hoc envelopes. |
| `app/agents/crew.py` | Python | CrewAI Crew Definition | Defines 8 CrewAI agents, but has `tasks=[]` and is never executed in the application runtime. |
| `app/agents/procurement_crew.py` | Python | Procedural Workflow Engine | `ProcurementWorkflowEngine` class manually implements all agent steps in procedural Python, bypassing CrewAI task execution and calling DB directly. |
| `app/a2a/client.py` | Python | Inter-Agent Communication | Custom HTTP client that POSTs `A2AMessageEnvelope` to `/a2a/v1/message`. Not the standard A2A protocol. |
| `app/a2a/schemas.py` | Python / Pydantic | A2A Schemas | Defines custom JSON envelope (`A2AMessageEnvelope`) and payload models. Lacks Agent Cards, task lifecycle states, and JSON-RPC compliance. |
| `app/mcp/server.py` | Python / FastMCP | MCP Server | Instantiates `FastMCP("DealForge-Procurement-Server")` with 10 tools. Works via stdio, but is not connected to running agents. |
| `app/mcp/tools/procurement_tools.py` | Python | MCP Tool Implementations | Standalone functions wrapping database repository and service calls. |
| `app/core/config.py` | Python / Pydantic | Configuration | `Settings` class loading `.env`. Includes database, LLM, and rule parameters. |
| `app/core/logging.py` | Python | Logging | Basic console logger. Lacks structured JSON logging, correlation IDs, and request tracing. |
| `app/db/base.py` | Python / SQLAlchemy | ORM Base | Declarative Base and UTC timestamp helper. |
| `app/db/session.py` | Python / SQLAlchemy | Session & Engine | SQLAlchemy 2.0 engine and `SessionLocal` generator with MySQL / SQLite support. |
| `app/db/models/entities.py` | Python / SQLAlchemy | Data Entities | 10 entities: `Vendor`, `Product`, `VendorProduct`, `PurchaseRequest`, `VendorQuote`, `ComplianceRule`, `Evaluation`, `Negotiation`, `Approval`, `PurchaseOrder`, `AgentLog`, `WorkflowState`. |
| `app/db/repositories/procurement_repo.py` | Python | Data Access Layer | Comprehensive CRUD repository for existing entities. |
| `app/db/seed.py` | Python | Database Seeder | Seeds 8 synthetic vendors, 4 products, 14 listings, and 5 compliance rules. |
| `app/services/` | Python | Domain Services | Deterministic business services (`pricing_service`, `budget_service`, `compliance_service`, `evaluation_service`, `approval_service`, `purchase_order_service`, `replanning_service`). |
| `app/api/routes/` | Python / FastAPI | REST Routes | 10 route modules (`requests`, `workflows`, `vendors`, `quotes`, `evaluations`, `negotiations`, `approvals`, `purchase_orders`, `dashboard`, `replanning`). |
| `frontend/` | HTML / CSS / JS | Dashboard UI | Legacy vanilla JavaScript (`index.html`, `style.css`, `app.js`). Not React, TypeScript, or Tailwind CSS. |
| `tests/` | Python / Pytest | Test Suite | `test_services.py` passes (5 tests). `test_end_to_end_and_api.py` crashes due to missing `google-adk` package. |
| `requirements.txt` | Config | Dependencies | Pins outdated or uninstalled dependencies. Missing official A2A SDK and proper Google ADK / CrewAI pins. |
| `docker-compose.yml` | Docker | Container Setup | MySQL and DealForge app containers. Lacks separate MCP and A2A service definitions. |

---

## 2. Feature Matrix & Gap Analysis

| Feature | Existing Implementation | Gap | Evidence | Planned Action |
| :--- | :--- | :--- | :--- | :--- |
| **ADK Orchestration** | `app/adk_service/agent.py` uses `google.adk.Agent` solely for risk assessment. | ADK is relegated to a leaf risk node. ADK must be the primary workflow coordinator orchestrating Requirement Analysis, Vendor Research, Procurement Coordination, and Approval & Replanning. | `app/adk_service/agent.py:8-23`, `app/agents/procurement_crew.py:21` | Refactor main lifecycle so Google ADK agents coordinate the end-to-end procurement process. |
| **CrewAI** | `app/agents/crew.py` defines 8 agents with `tasks=[]`. In `procurement_crew.py`, steps are procedural Python code. | CrewAI is not actually executing tasks in the workflow. It must serve as the specialized procurement analysis crew (Price Analysis, Compliance, Deal Evaluation, Negotiation). | `app/agents/crew.py:122`, `app/agents/procurement_crew.py:198-403` | Implement a genuine CrewAI analysis crew with sequential tasks and deterministic tool bindings, delegated to via A2A. |
| **MCP** | `app/mcp/server.py` defines 10 tools with `FastMCP`. | MCP tools are defined, but agents do not call them through an MCP client protocol; agents call repository and domain services directly in Python. | `app/agents/procurement_crew.py:18-19`, `app/mcp/tools/procurement_tools.py` | Implement official MCP client adapter connecting ADK agents and services to MCP server over streamable HTTP / stdio. |
| **A2A** | `app/a2a/client.py` and `app/adk_service/server.py` send custom JSON envelopes (`A2AMessageEnvelope`) over HTTP POST. | Not a genuine protocol-compatible A2A implementation. Missing Agent Cards (`/.well-known/agent.json`), standard task lifecycle (SUBMIT, STATUS, CANCEL), and separately addressable services. | `app/a2a/schemas.py:8-19`, `app/adk_service/server.py:40` | Implement genuine protocol-compatible A2A services with Agent Cards, task lifecycle management, and typed data contracts. |
| **MySQL & Alembic** | SQLAlchemy models in `entities.py`, SQLite/MySQL session in `session.py`, seeder in `seed.py`. | Missing 5 required entities: `users`, `roles`, `vendor_certifications`, `procurement_policies`, `procurement_items`, `procurement_audit_logs`. No Alembic migrations configured. Only 8 demo vendors instead of 10+. | `app/db/models/entities.py`, absence of `alembic/` directory, `app/db/seed.py:12-70` | Implement all 15 normalized tables, initialize Alembic migrations, expand seed data to 10+ synthetic vendors with all edge-case scenarios. |
| **Frontend** | Vanilla HTML5/CSS3/JS in `frontend/index.html` and `frontend/js/app.js`. | Project specification strictly requires React, TypeScript, and Tailwind CSS covering Screens A through G. | `frontend/index.html`, `frontend/js/app.js`, `frontend/css/style.css` | Build modern React + TypeScript + Tailwind CSS application with responsive UI, live API data, and no fake timers. |
| **Security & Auth** | No authentication or authorization. Any caller can approve requests via `POST /api/approvals/{id}/decision`. API keys stored in `.env`. | Missing JWT authentication, RBAC (Procurement Manager, Finance Reviewer, Admin), state-machine transition validation, and audit trail. | `app/api/routes/approvals.py:41-62`, `app/core/config.py:21` | Implement JWT authentication, RBAC dependencies on FastAPI endpoints, state transition guards, and audit logging. |
| **Tests & Verification** | 5 unit tests in `test_services.py`. `test_end_to_end_and_api.py` fails during collection due to missing `google.adk`. | Incomplete test suite. Missing coverage for MCP tools, A2A communication, ADK coordination, replanning recovery, and 10 mandatory E2E scenarios. | `tests/test_end_to_end_and_api.py:1-12`, test execution crash log | Implement comprehensive Pytest suite covering all 20 test areas and 10 mandatory end-to-end scenarios. |
| **LangGraph Prohibition** | Repository audit found zero occurrences of LangGraph. | Compliant. Ensure no LangGraph transitive dependencies or imports are introduced. | Global codebase search for `langgraph` returned 0 hits | Preserve prohibition of LangGraph. |

---

## 3. Runtime Path Analysis

### Existing Runtime Path (As Inspected)
1. User submits request via frontend `fetch("/api/requests/submit")` or `POST /api/requests`.
2. `requests.py` persists a `PurchaseRequest` in MySQL and returns `request_id`.
3. Frontend triggers `POST /api/workflows/{request_id}/start`.
4. `ProcurementWorkflowEngine` runs in FastAPI background task:
   - Uses regex to parse category, budget, quantity.
   - Queries `VendorProduct` via SQLAlchemy repo.
   - Computes quote prices with `PricingService`.
   - Runs compliance check with `ComplianceService`.
   - Evaluates quotes with `EvaluationService`.
   - Formulates negotiation text via string templates.
   - Calls `A2AClient.request_risk_assessment()` which HTTP POSTs to `ADKProcurementRiskAgent` on `/adk-service`.
   - If risk score > threshold or amount > ₹10,00,000, sets status to `PAUSED` and creates `Approval` record.
   - Otherwise, auto-creates `PurchaseOrder`.
5. Frontend polls `/api/workflows/{id}/status` to update stepper.

### Required Target Runtime Path
1. **User Request Submission**: Authenticated user submits natural-language or structured request via React dashboard.
2. **ADK Primary Orchestration**: Google ADK `RequirementAnalysisAgent` extracts and validates schemas (asking for clarification if mandatory fields are missing).
3. **Vendor Research**: ADK `VendorResearchAgent` invokes MCP `search_vendors` and `get_vendor_details` tools backed by MySQL.
4. **Deterministic Pricing & Compliance**: Deterministic domain services calculate exact `Decimal` costs and evaluate compliance (`PASS`, `FAIL`, `UNKNOWN`).
5. **Specialized CrewAI Analysis via A2A**: ADK coordinates with A2A `ProcurementAnalysisService` which executes the CrewAI Analysis Crew (`PriceAnalysisSpecialist`, `ComplianceSpecialist`, `DealEvaluationSpecialist`, `NegotiationSpecialist`).
6. **Eligibility & Ranking**: Deterministic weighted scoring algorithm ranks eligible vendors. Ineligible vendors are excluded.
7. **Negotiation Constraints**: Target price and counter-offer formulated within deterministic bounds.
8. **Approval Gating**: Policy thresholds checked. If approval is required, request pauses in `AWAITING_APPROVAL` with state persisted in MySQL.
9. **Human Decision**: Authenticated manager or finance reviewer approves/rejects via protected endpoint.
10. **Dynamic Replanning / PO Finalization**:
    - If approved: Purchase order generated, audit logged, status becomes `FINALIZED`.
    - If rejected or conditions change (budget cut, stockout): ADK `ApprovalReplanningAgent` invalidates stale state and reruns affected stages safely.

---

## 4. Verification Evidence & Key Findings

1. **Python Environment**: Python 3.11.9 is installed on Windows.
2. **Database**: MySQL Server 8.4.9 is running on `127.0.0.1:3306`. Database `dealforge_db` has been created and verified.
3. **Official MCP SDK**: Official Python `mcp` 1.26.0 is installed in the environment.
4. **Google ADK & CrewAI**: `google-adk` 2.13.0 and `crewai` 1.15.28 are available on PyPI and ready for stabilization.
5. **Node.js**: Node v22.23.2 and npm 10.9.1 are installed and available for React + TypeScript + Tailwind CSS dashboard development.
6. **LangGraph**: Verified completely absent from repository.
