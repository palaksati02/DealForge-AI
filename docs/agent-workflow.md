# DealForge AI — Multi-Agent Workflow and Protocol Architecture

## 1. High-Level Architectural Division

```mermaid
flowchart TD
    User([Procurement Manager]) -->|Natural Language Prompt| FastAPI[FastAPI REST API / SSE]
    FastAPI -->|Initiates| ADK[Google ADK Primary Orchestrator]
    
    subgraph "Google ADK Orchestration Engine"
        ADK --> ReqAgent[GoogleADK_RequirementAnalysisAgent]
        ADK --> VendorAgent[GoogleADK_VendorResearchAgent]
        ADK --> CoordAgent[GoogleADK_ProcurementCoordinationAgent]
        ADK --> ApprAgent[GoogleADK_ApprovalReplanningAgent]
    end

    subgraph "Standardized Tool Interface (FastMCP)"
        VendorAgent -->|MCP Tool Calls| MCPServer[DealForge MCP Server]
        MCPServer --> MySQL[(MySQL 8.4 Relational DB)]
    end

    subgraph "A2A Inter-Agent Protocol (Port 8000 /a2a/*)"
        CoordAgent -->|A2A Task Dispatch| A2A_VR[/a2a/vendor-research]
        CoordAgent -->|A2A Task Dispatch| A2A_PA[/a2a/procurement-analysis]
        CoordAgent -->|A2A Task Dispatch| A2A_NEG[/a2a/negotiation]
        ApprAgent -->|A2A Task Dispatch| A2A_AR[/a2a/approval-replanning]
    end

    subgraph "CrewAI Specialist Analysis Crew"
        A2A_PA --> PriceSpec[Price Analysis Specialist]
        A2A_PA --> CompSpec[Compliance Specialist]
        A2A_PA --> EvalSpec[Deal Evaluation Specialist]
        A2A_PA --> NegSpec[Negotiation Specialist]
    end

    ADK -->|State & Audit Commits| MySQL
    ApprAgent -->|Risk Score Threshold Check| ApprovalGate{Approval Required?}
    ApprovalGate -->|Yes: Total > ₹10L| PausedState([Workflow Paused in MySQL])
    ApprovalGate -->|No| AutoCommit([Auto-Generate Purchase Order])
    PausedState -->|Human Sign-off via API| Resumed([Workflow Resumed]) --> AutoCommit
```

---

## 2. Agent Roles and Framework Responsibilities

### A. Google Agent Development Kit (ADK) — Primary Orchestrator
- **Role:** Controls top-level procurement workflow orchestration, state machine transitions, human-in-the-loop governance gates, and dynamic replanning triggers.
- **Agents:**
  1. `GoogleADK_RequirementAnalysisAgent`: Extracts structured procurement requirements (quantity, budget ceiling, deadline days, warranty SLA, category, specifications) from unstructured natural language requests.
  2. `GoogleADK_VendorResearchAgent`: Coordinates supplier discovery and inventory checks using standardized MCP tools.
  3. `GoogleADK_ProcurementCoordinationAgent`: Orchestrates specialist analysis by dispatching tasks to A2A protocol endpoints.
  4. `GoogleADK_ApprovalReplanningAgent`: Performs governance risk assessment, audits delegation-of-authority thresholds, and replans downstream stages when environmental conditions change.

### B. CrewAI — Specialized Procurement Analysis Crew
- **Role:** Delegated execution of domain-specific multi-attribute analysis within the `procurement-analysis` A2A service.
- **Specialists:**
  1. `Price Analysis Specialist`: Evaluates pricing structures, applies tiered bulk discounts, calculates standard 18% GST and flat logistics costs using exact Python `Decimal` arithmetic.
  2. `Compliance Specialist`: Audits active ERP directory status, warranty SLA compliance, lead-time deadlines, and minimum order quantities (MOQ), outputting deterministic `PASS`, `FAIL`, or `UNKNOWN`.
  3. `Deal Evaluation Specialist`: Executes multi-attribute weighted scoring (Price: 35%, Delivery: 20%, Warranty: 15%, Compliance: 20%, Specs: 10%) with mathematical tie-breaking.
  4. `Negotiation Specialist`: Establishes algorithmically bounded target prices, estimates non-committed projected savings, and drafts persuasive vendor communication.

### C. Model Context Protocol (FastMCP)
- Standardized tool interface exposing 16 validated procurement tools:
  - `search_vendors`, `get_vendor_details`, `get_vendor_certifications`
  - `search_products`, `get_product_details`, `get_vendor_product_pricing`
  - `calculate_quote_total`, `validate_budget_ceiling`
  - `verify_vendor_compliance`, `get_procurement_policies`
  - `create_quotation_record`, `save_evaluation_scores`, `save_negotiation_draft`
  - `create_approval_request`, `generate_purchase_order`, `get_workflow_audit_trail`
- Invoked via `MCPProcurementClient` with parameterized repository queries.

### D. Agent-to-Agent (A2A) Protocol
- Standardized protocol interfaces featuring machine-readable Agent Cards at `/.well-known/agent-card.json`.
- Separately addressable service endpoints:
  - `/a2a/vendor-research`
  - `/a2a/procurement-analysis`
  - `/a2a/negotiation`
  - `/a2a/approval-replanning`
- Implements standard task lifecycles: `SUBMITTED -> RUNNING -> COMPLETED` (or `FAILED`).

---

## 3. Workflow State Machine Lifecycle

```
CREATED
   ↓
REQUIREMENT_VALIDATION
   ↓
VENDOR_RESEARCH
   ↓
ANALYSIS (Delegated to CrewAI via A2A)
   ↓
EVALUATION (Weighted Ranking)
   ↓
NEGOTIATION (Bounded Counter-offer)
   ↓
AWAITING_APPROVAL (Paused for Human Sign-off if Total > ₹10,00,000)
   ↓
APPROVED (Authorized by Manager / Finance)
   ↓
FINALIZED (Purchase Order Issued & Committed to MySQL)
```

*Exception Transitions:*
- `BLOCKED_NEED_CLARIFICATION`: Insufficient or contradictory prompt parameters.
- `FAILED_NO_VENDORS`: Zero active vendors available in MySQL catalog.
- `FAILED_ALL_DISQUALIFIED`: All candidates fail mandatory compliance rules or budget limits.
- `REPLANNING`: Triggered upon budget reduction, vendor stockout, or rejected approval.
