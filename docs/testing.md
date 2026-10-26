# DealForge AI — Automated Testing & Verification Playbook

## 1. Overview & Testing Philosophy

DealForge AI adheres to strict automated verification principles. In compliance with the **Senior Software Engineering Implementation Playbook**, every core system capability—ranging from deterministic financial calculations to multi-agent protocol communication and human-in-the-loop governance—is validated through comprehensive automated tests.

### Key Guarantees
- **100% Deterministic Arithmetic**: Financial calculations, GST application, discount brackets, and multi-criteria scoring are verified to the exact penny using Python `Decimal`.
- **Zero Mocking of Business Logic**: Business services (`PricingService`, `BudgetService`, `ComplianceService`, `EvaluationService`, `NegotiationService`) are tested with actual mathematical assertions, not mocked return values.
- **Protocol Fidelity**: Model Context Protocol (MCP) and Agent-to-Agent (A2A) communications are verified using real FastAPI test clients and FastMCP tool interfaces.
- **Dual-Database Compatibility**: The test suite runs against in-memory SQLite (with `StaticPool` isolation) for high-speed continuous integration and against live MySQL 8.x for staging verification.

---

## 2. Test Architecture & Structure

The test suite is organized into 6 focused test modules under the `tests/` directory:

```
tests/
├── conftest.py                           # Database fixtures, test client, seeds, auth helpers
├── test_services.py                      # 8 Unit tests: Deterministic procurement business logic
├── test_mcp.py                           # 6 Integration tests: MCP FastMCP server and 16 tools
├── test_a2a.py                           # 6 Protocol tests: A2A agent cards, endpoints, envelopes
├── test_end_to_end_and_api.py            # 5 Workflow tests: ADK orchestrator, API, SSE streams
├── test_api_lifecycle_and_security.py    # 5 Security tests: JWT, RBAC, human gates, PO release
└── test_e2e_scenarios.py                 # 10 Scenario tests: All mandatory Playbook procurement flows
```

**Total Automated Coverage**: **40 Tests**, 100% passing.

---

## 3. Comprehensive Test Suite Breakdown

### 3.1 Unit Testing: Business Logic (`tests/test_services.py`)
Validates the five deterministic calculation engines in isolation:
1. `test_pricing_service_base_calculation`: Base subtotal, tiered quantity discounts, 18% GST, and freight surcharges.
2. `test_pricing_service_tiered_discounts`: Quantity-bracket step functions (e.g., 5% at 20 units, 10% at 50 units).
3. `test_budget_service_within_and_exceeded`: Strict budget comparison, variance calculation, and tolerance limits.
4. `test_compliance_service_full_pass`: Verification that active, certified vendors meeting warranty and delivery SLAs pass.
5. `test_compliance_service_disqualifications`: Inactive vendors, insufficient stock, expired certifications, and delivery breaches trigger deterministic rejection.
6. `test_evaluation_service_multi_criteria_scoring`: Weighted scoring model (40% price, 25% warranty, 20% delivery, 15% rating) normalized across quotes.
7. `test_negotiation_service_counter_offer_bounds`: Upper and lower negotiation boundaries calculated from historical margins and budget ceiling.
8. `test_negotiation_service_outcome_simulation`: Deterministic simulation of vendor acceptance, counter-compromise, and rejection based on discount depth.

### 3.2 Protocol Testing: Model Context Protocol (`tests/test_mcp.py`)
Validates standardized MCP tool access to MySQL procurement data:
1. `test_mcp_server_initialization`: FastMCP server instantiates with registered tools and metadata.
2. `test_mcp_list_tools`: All 16 FastMCP tools are properly registered and discoverable.
3. `test_mcp_get_vendor_catalog`: Querying products by category and specs through MCP tools.
4. `test_mcp_calculate_quote_tool`: Invoking the deterministic pricing tool via MCP interface.
5. `test_mcp_compliance_check_tool`: Tool execution returns structured compliance audit results.
6. `test_mcp_client_integration`: Standalone MCP client initializes, fetches schema, and executes tools.

### 3.3 Protocol Testing: Agent-to-Agent (A2A) (`tests/test_a2a.py`)
Validates protocol compliance, Agent Cards, and message routing:
1. `test_agent_cards_well_known`: `GET /.well-known/agent-card.json` returns valid schema for all 4 services.
2. `test_a2a_vendor_research_service`: Service card and `/process` endpoint for vendor discovery.
3. `test_a2a_procurement_analysis_service`: CrewAI specialist delegation and evaluation envelope response.
4. `test_a2a_negotiation_service`: Counter-offer calculation and drafting via A2A protocol.
5. `test_a2a_approval_replanning_service`: Governance risk assessment and replanning strategy generation.
6. `test_a2a_invalid_envelope_handling`: Malformed JSON or unknown agent target returns standardized error envelopes.

### 3.4 Integration Testing: API & ADK Workflow (`tests/test_end_to_end_and_api.py`)
Validates Google ADK root orchestration and FastAPI endpoints:
1. `test_create_procurement_request_api`: `POST /api/procurement/requests` creates request and initializes state.
2. `test_adk_orchestrator_execution`: `ADKProcurementOrchestrator` steps through all 4 agents and persists intermediate states.
3. `test_get_procurement_status_api`: `GET /api/procurement/requests/{id}/status` returns real-time progress and quotes.
4. `test_sse_workflow_stream`: `GET /api/procurement/workflows/{id}/stream` delivers real-time Server-Sent Events.
5. `test_comprehensive_report_generation`: `GET /api/procurement/requests/{id}/report` compiles full Markdown and JSON.

### 3.5 Security, Governance & Lifecycle (`tests/test_api_lifecycle_and_security.py`)
Validates enterprise authentication, role enforcement, and PO issuance:
1. `test_auth_login_and_jwt_generation`: Authentication generates valid JWT with role claims; invalid credentials rejected.
2. `test_rbac_procurement_manager_permissions`: Procurement Managers can create requests and view quotes but cannot approve high-value POs.
3. `test_rbac_finance_approval_gate`: Finance Approvers can review risk and authorize approvals.
4. `test_approval_flow_and_idempotent_po_generation`: Approving generates a formal PO once; re-approving returns idempotent response.
5. `test_dynamic_replanning_on_budget_reduction`: Submitting lower budget triggers dynamic replanning without restarting workflow.

---

## 4. The 10 Mandatory Playbook Scenarios (`tests/test_e2e_scenarios.py`)

The Senior Playbook specifies 10 concrete, non-negotiable procurement scenarios. All 10 are automated and verified:

| # | Scenario Title | Description & Target Outcome | Verification Assertion |
|---|---|---|---|
| **1** | **Compliant Winner Selection** | High-rated, fully certified vendor with sufficient stock and warranty wins the contract. | Winner has `is_eligible=True`, highest multi-criteria score ($\approx 95.8$), and valid certification. |
| **2** | **Cheap Non-Compliant Disqualification** | Lower-priced vendor with expired ISO certification or warranty shortfall is disqualified before ranking. | Disqualified vendor receives `is_eligible=False` and status `FAILED_COMPLIANCE`; winner is next eligible compliant vendor. |
| **3** | **Budget Overrun Approval Gate** | Multi-million Rupee purchase exceeding threshold pauses at `WAITING_FOR_APPROVAL`. | Workflow status halts at `WAITING_FOR_APPROVAL`; approval record generated with required approver role. |
| **4** | **Successful Negotiation Flow** | Vendor counter-offer matches requested 8% concession within acceptable margins. | Concession recorded; revised quote calculation replaces baseline in final evaluation; new PO reflects savings. |
| **5** | **Rejected Counter-Offer Flow** | Vendor rejects deep 25% discount; system gracefully proceeds with original best quote. | Negotiation status marked `REJECTED`; orchestrator falls back to original best evaluated quote without workflow crash. |
| **6** | **In-Flight Budget Cut Replanning** | Finance slashes budget by 20% mid-flight; orchestrator replans and filters out now-unaffordable quotes. | Request `budget_limit` updated; replanning agent re-filters eligible pool; selects compliant quote within new ceiling. |
| **7** | **Out-of-Stock Replanning** | Preferred vendor suffers sudden inventory stockout; system automatically pivots to runner-up supplier. | Stockout detected; runner-up evaluated and selected; audit log records vendor disqualification due to inventory shortage. |
| **8** | **Idempotent Purchase Order Release** | Multiple approval clicks or network retries must never issue duplicate Purchase Orders. | First approval creates PO with unique `po_number`; subsequent calls return existing PO with identical details. |
| **9** | **Audit Trail Immutability** | Every state change, price computation, and human interaction writes an append-only audit log. | `procurement_audit_logs` contains chronological records with timestamp, actor, action name, and details payload. |
| **10** | **Deterministic Demo Mode** | Full end-to-end execution completes seamlessly with zero external LLM API keys. | `DEMO_MODE=True` executes complete 8-step pipeline, produces final report, and generates PO with 100% deterministic logic. |

---

## 5. How to Run the Tests

### 5.1 Prerequisites
Ensure the Python virtual environment is activated and dependencies are installed:
```powershell
# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 5.2 Execute the Full Test Suite
Run all 40 tests with verbose output:
```powershell
python -m pytest tests/ -v
```

### 5.3 Run Individual Test Suites
```powershell
# 1. Deterministic Business Logic Services
python -m pytest tests/test_services.py -v

# 2. Model Context Protocol (MCP) Tools & Server
python -m pytest tests/test_mcp.py -v

# 3. Agent-to-Agent (A2A) Protocols & Endpoints
python -m pytest tests/test_a2a.py -v

# 4. Google ADK Orchestrator & REST API Endpoints
python -m pytest tests/test_end_to_end_and_api.py -v

# 5. Security, RBAC & Approval Lifecycle
python -m pytest tests/test_api_lifecycle_and_security.py -v

# 6. The 10 Senior Playbook Scenarios
python -m pytest tests/test_e2e_scenarios.py -v
```

### 5.4 Test Execution Summary

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.4.2
rootdir: c:\Users\KRISH\Downloads\dealforge_adk
collected 40 items

tests/test_services.py::test_pricing_service_base_calculation PASSED     [  2%]
tests/test_services.py::test_pricing_service_tiered_discounts PASSED     [  5%]
tests/test_services.py::test_budget_service_within_and_exceeded PASSED   [  7%]
tests/test_services.py::test_compliance_service_full_pass PASSED         [ 10%]
tests/test_services.py::test_compliance_service_disqualifications PASSED [ 12%]
tests/test_services.py::test_evaluation_service_multi_criteria_scoring PASSED [ 15%]
tests/test_services.py::test_negotiation_service_counter_offer_bounds PASSED [ 17%]
tests/test_services.py::test_negotiation_service_outcome_simulation PASSED [ 20%]
tests/test_mcp.py::test_mcp_server_initialization PASSED                 [ 22%]
tests/test_mcp.py::test_mcp_list_tools PASSED                            [ 25%]
tests/test_mcp.py::test_mcp_get_vendor_catalog PASSED                   [ 27%]
tests/test_mcp.py::test_mcp_calculate_quote_tool PASSED                  [ 30%]
tests/test_mcp.py::test_mcp_compliance_check_tool PASSED                 [ 32%]
tests/test_mcp.py::test_mcp_client_integration PASSED                   [ 35%]
tests/test_a2a.py::test_agent_cards_well_known PASSED                    [ 37%]
tests/test_a2a.py::test_a2a_vendor_research_service PASSED              [ 40%]
tests/test_a2a.py::test_a2a_procurement_analysis_service PASSED         [ 42%]
tests/test_a2a.py::test_a2a_negotiation_service PASSED                  [ 45%]
tests/test_a2a.py::test_a2a_approval_replanning_service PASSED          [ 47%]
tests/test_a2a.py::test_a2a_invalid_envelope_handling PASSED            [ 50%]
tests/test_end_to_end_and_api.py::test_create_procurement_request_api PASSED [ 52%]
tests/test_end_to_end_and_api.py::test_adk_orchestrator_execution PASSED [ 55%]
tests/test_end_to_end_and_api.py::test_get_procurement_status_api PASSED [ 57%]
tests/test_end_to_end_and_api.py::test_sse_workflow_stream PASSED       [ 60%]
tests/test_end_to_end_and_api.py::test_comprehensive_report_generation PASSED [ 62%]
tests/test_api_lifecycle_and_security.py::test_auth_login_and_jwt_generation PASSED [ 65%]
tests/test_api_lifecycle_and_security.py::test_rbac_procurement_manager_permissions PASSED [ 67%]
tests/test_api_lifecycle_and_security.py::test_rbac_finance_approval_gate PASSED [ 70%]
tests/test_api_lifecycle_and_security.py::test_approval_flow_and_idempotent_po_generation PASSED [ 72%]
tests/test_api_lifecycle_and_security.py::test_dynamic_replanning_on_budget_reduction PASSED [ 75%]
tests/test_e2e_scenarios.py::test_scenario_1_compliant_winner PASSED    [ 77%]
tests/test_e2e_scenarios.py::test_scenario_2_cheap_non_compliant_disqualification PASSED [ 80%]
tests/test_e2e_scenarios.py::test_scenario_3_budget_overrun_approval_gate PASSED [ 82%]
tests/test_e2e_scenarios.py::test_scenario_4_successful_negotiation PASSED [ 85%]
tests/test_e2e_scenarios.py::test_scenario_5_rejected_counter_offer PASSED [ 87%]
tests/test_e2e_scenarios.py::test_scenario_6_budget_cut_replanning PASSED [ 90%]
tests/test_e2e_scenarios.py::test_scenario_7_out_of_stock_replanning PASSED [ 92%]
tests/test_e2e_scenarios.py::test_scenario_8_idempotent_po_release PASSED [ 95%]
tests/test_e2e_scenarios.py::test_scenario_9_audit_trail_immutability PASSED [ 97%]
tests/test_e2e_scenarios.py::test_scenario_10_deterministic_demo_mode PASSED [100%]

============================= 40 passed in 67.92s =============================
```
