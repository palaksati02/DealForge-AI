# DealForge AI — Implementation Roadmap & Execution Checklist

This roadmap outlines the phased execution strategy to transform the DealForge AI repository into an integrated, production-grade, multi-agent procurement system.

---

## Phase Checklist & Status

- [x] **Phase 1: Repository Audit and Technical Discovery**
  - [x] Complete inventory of existing components and code assets.
  - [x] Feature matrix and gap analysis.
  - [x] Runtime path analysis and architecture baseline.
  - [x] Verification of existing test suite, Python environment, and MySQL database.
  - [x] Production of `docs/repository-audit.md`, `docs/architecture.md`, `docs/implementation-roadmap.md`, `docs/dependency-compatibility.md`.

- [ ] **Phase 2: Dependency Compatibility and Project Foundation**
  - [ ] Pin compatible dependencies (`google-adk`, `crewai`, `mcp`, `fastapi`, `sqlalchemy`, `alembic`, `pydantic`).
  - [ ] Validate Python 3.11 environment and official SDK imports.
  - [ ] Enforce zero LangGraph dependency.
  - [ ] Update `.env.example` with documented configuration placeholders.
  - [ ] Implement structured JSON logging with correlation IDs and error handling.
  - [ ] Update Docker Compose configuration for multi-service setup.

- [ ] **Phase 3: MySQL Schema, Migrations and Data Access**
  - [ ] Implement all 15 normalized tables in `app/db/models/entities.py`:
    1. `users`
    2. `roles`
    3. `vendors`
    4. `products`
    5. `vendor_products`
    6. `vendor_quotes`
    7. `vendor_certifications`
    8. `procurement_policies`
    9. `purchase_requests`
    10. `procurement_items`
    11. `evaluations`
    12. `negotiations`
    13. `approvals`
    14. `procurement_audit_logs`
    15. `purchase_orders`
  - [ ] Initialize and execute Alembic migrations.
  - [ ] Expand synthetic seed data to 10+ distinct vendors covering all required edge scenarios:
    - Compliant winner
    - Cheap but non-compliant vendor (fails mandatory certification / active flag)
    - Budget violation scenario
    - Negotiation opportunity
    - High-value purchase requiring dual executive approval
    - Missing / unknown certification data
    - Disqualified / out-of-stock vendor
  - [ ] Implement database integration tests verifying foreign keys, constraints, and transactions.

- [ ] **Phase 4: Deterministic Procurement Business Logic**
  - [ ] Enhance Pydantic request schemas with missing field detection and clarification requirements.
  - [ ] Standardize monetary calculations using Python `Decimal` across subtotals, volume discounts, 18% GST, shipping, and effective unit prices.
  - [ ] Upgrade compliance checks to return explicit `PASS`, `FAIL`, or `UNKNOWN` with database certification verification.
  - [ ] Refine multi-criteria scoring algorithm with configurable weights, score normalization, tie-breaking, and mandatory eligibility gating.
  - [ ] Enforce negotiation target boundaries and maximum acceptable price limits.
  - [ ] Unit tests for arithmetic precision, boundary conditions, and eligibility rules.

- [ ] **Phase 5: Implement the MCP Procurement Server**
  - [ ] Enhance FastMCP server with typed input/output Pydantic schemas.
  - [ ] Implement full suite of procurement tools (catalog search, profile lookup, inventory check, pricing calculation, budget verification, compliance auditing, policy retrieval, audit logging, PO issuance).
  - [ ] Restrict database access via repository layer with parameterized queries.
  - [ ] Provide MCP client adapter for seamless tool invocation from agents.
  - [ ] Add unit tests for tool schemas, error handling, and client execution.

- [ ] **Phase 6: Implement Genuine A2A Agent Services**
  - [ ] Implement 4 separately addressable A2A services:
    - `VendorResearchService`
    - `ProcurementAnalysisService`
    - `NegotiationService`
    - `ApprovalReplanningService`
  - [ ] Publish standard Agent Cards (`/.well-known/agent.json`) for each service.
  - [ ] Implement task lifecycle handling (`SUBMIT`, `STATUS`, `CANCEL`) with correlation IDs.
  - [ ] Connect CrewAI analysis crew inside `ProcurementAnalysisService`.
  - [ ] Integration tests verifying inter-service task dispatch and structured response handling.

- [ ] **Phase 7: Google ADK Main Orchestration**
  - [ ] Implement Google ADK primary coordinator agents:
    - `RequirementAnalysisAgent`
    - `VendorResearchAgent`
    - `ProcurementCoordinationAgent`
    - `ApprovalReplanningAgent`
  - [ ] Orchestrate the end-to-end procurement workflow through Google ADK.
  - [ ] Connect ADK agents to MCP tools and A2A services.
  - [ ] Persist all stage transitions and execution events in MySQL.

- [ ] **Phase 8: CrewAI Procurement Analysis Crew**
  - [ ] Implement specialized CrewAI agents with domain backstories and explicit roles:
    - `PriceAnalysisSpecialist`
    - `ComplianceSpecialist`
    - `DealEvaluationSpecialist`
    - `NegotiationSpecialist`
  - [ ] Define explicit CrewAI tasks with structured inter-task outputs.
  - [ ] Integrate deterministic calculation tools into CrewAI execution.
  - [ ] Integration tests invoking CrewAI through the A2A service path.

- [ ] **Phase 9: FastAPI Application and Workflow Lifecycle**
  - [ ] Implement and verify all required REST endpoints:
    - `POST /api/procurement/requests`
    - `GET /api/procurement/requests`
    - `GET /api/procurement/requests/{id}`
    - `GET /api/procurement/requests/{id}/status`
    - `GET /api/procurement/requests/{id}/events`
    - `GET /api/procurement/requests/{id}/vendors`
    - `GET /api/procurement/requests/{id}/report`
    - `POST /api/procurement/requests/{id}/approval`
    - `POST /api/procurement/requests/{id}/replan`
    - `GET /api/vendors`
    - `GET /api/policies`
    - `GET /health`
  - [ ] Add background task worker with polling and Server-Sent Events (SSE) support.
  - [ ] Maintain consistent state machine lifecycle.

- [ ] **Phase 10: Security, Authentication and Human Approval**
  - [ ] Implement JWT token authentication with secure password hashing.
  - [ ] Implement RBAC dependencies for `Procurement Manager`, `Finance Reviewer`, and `Administrator`.
  - [ ] Enforce approval state verification, version checking, and idempotency protection.
  - [ ] Record complete audit trails for every consequential human decision.
  - [ ] Security tests for unauthorized access, invalid transitions, and duplicate approvals.

- [ ] **Phase 11: Dynamic Replanning and Recovery**
  - [ ] Implement versioned procurement state and staged dependency graph.
  - [ ] Support dynamic replanning triggers:
    - Purchase budget reduction
    - Vendor stockout / unavailability
    - Quotation expiry
    - Specification alteration
    - Rejected approval / revision request
  - [ ] Invalidate stale decisions and re-execute affected stages via ADK without corrupting audit history.
  - [ ] Integration tests demonstrating stage re-run and rollback consistency.

- [ ] **Phase 12: React Dashboard and Complete Frontend Integration**
  - [ ] Scaffold React 18 + TypeScript + Tailwind CSS application.
  - [ ] Build Screen A: Dashboard Overview with real metrics.
  - [ ] Build Screen B: New Procurement Request with extraction preview.
  - [ ] Build Screen C: Live Agent Workflow with stage stepper and event log.
  - [ ] Build Screen D: Vendor Comparison Matrix with criteria breakdown.
  - [ ] Build Screen E: Negotiation Workspace with counter-offer editor.
  - [ ] Build Screen F: Approval Center with RBAC actions and evidence.
  - [ ] Build Screen G: Final Procurement Report with export capability.
  - [ ] Connect frontend to live FastAPI endpoints (no fake timers or mock data).

- [ ] **Phase 13: Demo Mode and Graceful Failure**
  - [ ] Provide high-fidelity deterministic fallback mode when LLM API keys are absent.
  - [ ] Maintain 100% functionality of deterministic pricing, compliance, scoring, and approval gating in Demo Mode.
  - [ ] Explicitly display failure states and connection timeouts without hallucinating success.

- [ ] **Phase 14: Automated Testing and End-to-End Validation**
  - [ ] Run comprehensive Pytest test suite covering 20 test areas.
  - [ ] Implement and pass all 10 mandatory end-to-end scenarios:
    1. Compliant vendor selected successfully.
    2. Cheapest vendor rejected for non-compliance.
    3. All options exceed budget.
    4. Negotiation draft within permitted boundaries.
    5. Approval pause and resume.
    6. Rejected approval replanning.
    7. Vendor unavailability during procurement.
    8. Unavailable LLM triggering safe fallback.
    9. Agent failure without silent finalization.
    10. Duplicate approval idempotency.
  - [ ] Run frontend build and type checking (`npm run build`).

- [ ] **Phase 15: Documentation, Reproducibility and Final Handover**
  - [ ] Complete all technical documentation in `docs/` and `README.md`.
  - [ ] Document verified framework versions, startup commands, and test results.
  - [ ] Final verification in clean environment.
