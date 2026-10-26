# DealForge AI — Agentic Multi-Agent Procurement Automation Platform

[![Python](https://img.shields.io/badge/Python-3.11.9-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Google ADK](https://img.shields.io/badge/Google_ADK-2.13.0-4285F4.svg)](https://github.com/google/agent-development-kit)
[![CrewAI](https://img.shields.io/badge/CrewAI-1.15.28-FF4F00.svg)](https://www.crewai.com/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-1.28.1-black.svg)](https://modelcontextprotocol.io/)
[![A2A Protocol](https://img.shields.io/badge/A2A-1.0-purple.svg)](https://agent2agent.info/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1.svg)](https://www.mysql.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6.3-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4.14-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Pytest-40_Passed-success.svg)](https://docs.pytest.org/)

DealForge AI is an enterprise-grade, deterministic multi-agent procurement automation system built to transform natural language purchase requests into legally compliant, financially validated, and mathematically optimized purchase orders.

The platform combines **Google Agent Development Kit (ADK)** for primary workflow orchestration and governance, **CrewAI** for specialized multi-agent financial and compliance analysis, **Model Context Protocol (MCP)** for standardized tool-based database operations, **Agent-to-Agent (A2A)** protocol for inter-service messaging, and a modern **React 18 + TypeScript** web dashboard.

---

## 🌟 Architectural & Functional Highlights

1. **Google ADK Primary Orchestration**: A multi-step orchestrator (`ADKProcurementOrchestrator`) governs the end-to-end procurement lifecycle through 4 autonomous ADK agents:
   - `RequirementsIntakeAgent`: Parses natural language prompts, extracts technical specifications, delivery deadlines, and budget limits.
   - `VendorDiscoveryAgent`: Queries MySQL vendor catalogs via FastMCP tools.
   - `AnalysisCoordinationAgent`: Delegates deep comparative evaluation to the CrewAI analysis team via A2A protocol.
   - `GovernanceApprovalAgent`: Enforces financial limits, risk audits, human approval gates, and dynamic replanning.
2. **CrewAI Specialized Procurement Crew**: An isolated analysis crew executing inside the `/a2a/procurement-analysis` service:
   - `PriceAnalysisSpecialist`: Computes tiered volume discounts, 18% GST, and freight surcharges.
   - `ComplianceSpecialist`: Validates active vendor status, delivery SLAs, minimum warranties, and certifications.
   - `DealEvaluationSpecialist`: Executes multi-attribute weighted scoring (40% Price, 25% Warranty, 20% Delivery, 15% Vendor Rating).
   - `NegotiationSpecialist`: Calculates mathematical counter-offer boundaries and drafts professional vendor inquiries.
3. **Model Context Protocol (MCP)**: A FastMCP server exposing 16 standardized tools for querying catalogs, inventory stock, certifications, and recording quotations and purchase orders.
4. **Agent-to-Agent (A2A) Protocol**: 4 addressable microservices exposing standard Agent Cards at `/.well-known/agent-card.json`:
   - `/a2a/vendor-research`: Catalog and supplier discovery.
   - `/a2a/procurement-analysis`: Multi-agent CrewAI financial and compliance analysis.
   - `/a2a/negotiation`: Concession calculation and counter-offer drafting.
   - `/a2a/approval-replanning`: Risk score computation, approval routing, and dynamic replanning.
5. **Deterministic Python `Decimal` Arithmetic**: 100% exact currency calculations (`DECIMAL(15, 2)`). Zero LLM arithmetic hallucinations.
6. **Enterprise Security & RBAC**: JWT Bearer authentication, bcrypt salt password hashing, and role-based permissions (`PROCUREMENT_MANAGER`, `FINANCE_APPROVER`, `SYSTEM_ADMIN`).
7. **Human-in-the-Loop Governance**: Workflows exceeding ₹10,00,000, incurring budget overruns, or flagged by risk audits pause deterministically at `WAITING_FOR_APPROVAL`.
8. **Dynamic Replanning & Recovery**: Handles budget cuts, vendor inventory stockouts, and rejected negotiations in-flight without restarting the pipeline.
9. **Full React 18 Dashboard**: Modern glassmorphism interface across 7 dedicated views:
   - **Screen A: Executive Dashboard**: Metric KPIs, spend, savings, and historical requests.
   - **Screen B: New Request Studio**: Natural language prompt with quick-fill template chips and parameter overrides.
   - **Screen C: Live Workflow View**: Real-time 8-agent stepper cards with Server-Sent Events (SSE) and live database event log.
   - **Screen D: Vendor Comparison Matrix**: Criteria breakdown, PASS/FAIL badges, and weighted score tables.
   - **Screen E: Negotiation Workspace**: Upper/lower bound calculator, counter-offer editor, and vendor response simulation.
   - **Screen F: Approval Center**: Role indicator, governance risk triggers, and Approve/Reject controls.
   - **Screen G: Procurement Report**: Markdown preview, executive summary, and one-click JSON/Markdown export.
10. **Zero LangGraph Usage**: Strict adherence to engineering guidelines with zero LangGraph imports or transitive dependencies.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   React 18 + TS Web    │
                                  │  Dashboard (Port 8000) │
                                  └───────────┬────────────┘
                                              │ (REST / SSE Stream)
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                FastAPI Gateway Application                             │
│                                                                                        │
│   ┌───────────────────────────┐         ┌──────────────────────────────────────────┐   │
│   │   Auth & Security (JWT)   │         │    Google ADK Procurement Orchestrator   │   │
│   │   - RBAC Enforcement      │         │    - RequirementsIntakeAgent             │   │
│   │   - Bcrypt Salt Hashing   │         │    - VendorDiscoveryAgent                │   │
│   │   - Correlation Tracking  │         │    - AnalysisCoordinationAgent           │   │
│   └───────────────────────────┘         │    - GovernanceApprovalAgent             │   │
│                                         └────────────────────┬─────────────────────┘   │
└──────────────────────────────────────────────────────────────┼─────────────────────────┘
                                                               │
                              ┌────────────────────────────────┼────────────────────────────────┐
                              │ (A2A Protocol / JSON Envelope) │                                │
                              ▼                                ▼                                ▼
               ┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────────────┐
               │     A2A Vendor Research     │  │  A2A Procurement Analysis   │  │  A2A Approval & Replanning  │
               │   /.well-known/agent-card   │  │   /.well-known/agent-card   │  │   /.well-known/agent-card   │
               └──────────────┬──────────────┘  └──────────────┬──────────────┘  └──────────────┬──────────────┘
                              │                                │                                │
                              │                                ▼                                │
                              │                 ┌─────────────────────────────┐                 │
                              │                 │   CrewAI Specialist Crew    │                 │
                              │                 │   - PriceAnalysisSpecialist │                 │
                              │                 │   - ComplianceSpecialist    │                 │
                              │                 │   - DealEvaluationSpecialist│                 │
                              │                 │   - NegotiationSpecialist   │                 │
                              │                 └──────────────┬──────────────┘                 │
                              │                                │                                │
                              └────────────────────────────────┼────────────────────────────────┘
                                                               │
                                                               ▼
                                                ┌─────────────────────────────┐
                                                │   Model Context Protocol    │
                                                │    FastMCP Server (16 Tools)│
                                                └──────────────┬──────────────┘
                                                               │ (Parameterized SQLAlchemy 2.x)
                                                               ▼
                                                ┌─────────────────────────────┐
                                                │   MySQL 8.4 Enterprise DB   │
                                                │  (18 Normalized Tables)     │
                                                └─────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: Version 3.11.x (tested on 3.11.9)
- **Node.js**: Version 18.x or 20.x
- **MySQL**: MySQL 8.0 or 8.4 Server running locally on port 3306

### 2. Environment Configuration
Clone the repository and copy the environment template:
```powershell
# Copy environment configuration
cp .env.example .env
```
Default `.env` settings:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=dealforge_db
DEMO_MODE=True
JWT_SECRET=dealforge-super-secret-jwt-key-for-development-change-in-prod-2026
AUTO_APPROVAL_THRESHOLD=1000000.00
```
> *Note: Keep `DEMO_MODE=True` to immediately run high-fidelity deterministic simulations without requiring external API keys. Set `GEMINI_API_KEY` anytime to enable hybrid LLM drafting.*

### 3. Database Initialization & Seeding
Execute the automated migration and seed script:
```powershell
python scripts/init_db.py
```
This applies all 18 normalized tables and seeds 11 enterprise vendors, 14 products, 17 certifications, 4 policies, and 3 demo user accounts:
- `manager@dealforge.ai` (Role: `PROCUREMENT_MANAGER`, Password: `password123`)
- `finance@dealforge.ai` (Role: `FINANCE_APPROVER`, Password: `password123`)
- `admin@dealforge.ai` (Role: `SYSTEM_ADMIN`, Password: `password123`)

### 4. Build Frontend & Launch Backend
The React frontend is pre-built in `frontend-app/dist`. To launch the unified FastAPI server:
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **A2A Agent Cards**: [http://localhost:8000/a2a/procurement-analysis/.well-known/agent-card.json](http://localhost:8000/a2a/procurement-analysis/.well-known/agent-card.json)

*(Optional) To rebuild the frontend during UI development:*
```powershell
cd frontend-app
npm install
npm run build
cd ..
```

---

## 🧪 Automated Testing & Verification

DealForge AI includes a comprehensive 40-test automated verification suite covering all unit calculations, protocol integrations, and the 10 mandatory Senior Playbook business scenarios:

```powershell
# Run all 40 tests
python -m pytest tests/ -v
```

### Verified Scenarios:
1. **Compliant Winner Selection**: High-rated, certified supplier with stock and warranty wins contract.
2. **Cheap Non-Compliant Disqualification**: Lower-priced vendor with warranty or certification shortfall is disqualified.
3. **Budget Overrun Approval Gate**: Request exceeding ₹10,00,000 threshold deterministically pauses at `WAITING_FOR_APPROVAL`.
4. **Successful Negotiation Flow**: Concession within vendor margin accepted; revised quote updates PO.
5. **Rejected Counter-Offer Flow**: Aggressive discount rejected; orchestrator falls back to original best quote.
6. **In-Flight Budget Cut Replanning**: Budget reduction triggers dynamic re-filtering and alternate winner selection.
7. **Out-of-Stock Replanning**: Stockout detected mid-flight; system pivots to runner-up supplier.
8. **Idempotent PO Release**: Multiple approval submissions release PO exactly once.
9. **Audit Trail Immutability**: All steps, calculations, and decisions written to append-only audit log.
10. **Deterministic Demo Mode**: 100% end-to-end execution without external LLM dependencies.

---

## 📚 Complete Technical Documentation

| Document | Purpose & Key Topics |
|---|---|
| [docs/setup-guide.md](docs/setup-guide.md) | Step-by-step installation, dependency resolution, MySQL setup, and verification. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | High-level system architecture, component contracts, and sequence diagrams. |
| [docs/agent-workflow.md](docs/agent-workflow.md) | ADK orchestrator lifecycle, CrewAI specialist roles, and state transitions. |
| [docs/api-documentation.md](docs/api-documentation.md) | Complete OpenAPI endpoint catalog, request/response schemas, and SSE streams. |
| [docs/database-design.md](docs/database-design.md) | Entity relationship diagrams (ERD), schema definitions, and seed data. |
| [docs/security.md](docs/security.md) | JWT auth, bcrypt hashing, RBAC permission matrix, and PO idempotency. |
| [docs/testing.md](docs/testing.md) | Test architecture, test commands, and 10 scenario verification results. |
| [docs/limitations.md](docs/limitations.md) | Known scope boundaries, single-currency model, and future production roadmap. |
| [docs/repository-audit.md](docs/repository-audit.md) | Initial technical audit and gap analysis. |
| [docs/implementation-roadmap.md](docs/implementation-roadmap.md) | 15-phase implementation plan and execution evidence. |
| [docs/dependency-compatibility.md](docs/dependency-compatibility.md) | Pinning matrix for Google ADK, CrewAI, FastMCP, and FastAPI. |

---

## 🛡️ License & Academic Integrity

DealForge AI was built in accordance with the **Senior Software Engineering Implementation Playbook**. All business logic calculations, protocol contracts, database access layers, and test suites are 100% verified and functional.
