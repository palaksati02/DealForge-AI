# DealForge AI — Enterprise Multi-Agent Procurement Automation System

> **Agentic AI Capstone Project**  
> An enterprise-grade, deterministic multi-agent procurement platform powered by **CrewAI**, **Google Agent Development Kit (Google ADK)**, **Model Context Protocol (FastMCP)**, **Agent-to-Agent (A2A) Protocol**, **Langfuse Cloud**, and **MySQL 8.x**.

---

## 🌟 11 Mandatory Academic Requirements Compliance Matrix

All 11 mandatory academic requirements are 100% fulfilled and verified:

| # | Academic Requirement | Implementation & Technical Architecture | Primary Files | Status |
| :-: | :--- | :--- | :--- | :-: |
| **1** | **Context Sharing & State Updates** | State machine persisted in MySQL table `workflow_states`. Output of Agent 1 $\rightarrow$ Agent 2 $\rightarrow$ ... $\rightarrow$ Agent 8. Pauses and resumes seamlessly. | `app/agents/procurement_crew.py`, `app/db/repositories/procurement_repo.py` | ✅ Complete |
| **2** | **Tool Integration using MCP** | Dedicated FastMCP server (`app.mcp.server`) exposing 10 external tools for catalog search, quote calculation, budget validation, and PO generation. | `app/mcp/server.py`, `app/mcp/client.py`, `app/mcp/tools/procurement_tools.py` | ✅ Complete |
| **3** | **Structured Output using Pydantic** | 12 Pydantic V2 schemas enforce strict validation. Outputs JSON API payloads, HTML UI tables, and formal Markdown Purchase Orders. | `app/schemas/schemas.py`, `app/services/purchase_order_service.py` | ✅ Complete |
| **4** | **Agentic Design Patterns** | Sequential Pipeline, Tool-Use, Human-in-the-Loop (HITL) Approval Gating, Reflection/Self-Correction, and Dynamic Replanning. | `app/agents/procurement_crew.py`, `app/api/routes/replanning.py` | ✅ Complete |
| **5** | **Task Monitoring & Callbacks** | `MonitoringCallbackHandler` tracks start, intermediate step outputs, execution duration, and errors to console, MySQL, and UI stream. | `app/core/callbacks.py`, `app/api/routes/observability.py` | ✅ Complete |
| **6** | **A2A Protocol (Interoperability)** | Agent-to-Agent HTTP JSON-RPC protocol (`A2AMessageEnvelope`) linking CrewAI orchestrator to independent Google ADK Risk Agent service on port 8001. | `app/a2a/client.py`, `app/a2a/schemas.py`, `app/adk_service/server.py` | ✅ Complete |
| **7** | **CrewAI & Google ADK Exclusivity** | Strictly CrewAI (8 agents) + Google ADK (Autonomous Risk Auditor). Zero LangGraph, zero AutoGen, zero LangChain agents. | `app/agents/crew.py`, `app/adk_service/agent.py` | ✅ Complete |
| **8** | **Security Guardrails & Validation** | 4 security layers: prompt injection defense, toxicity screening, domain constraints, Pydantic V2 type checking with Python `Decimal`. | `app/core/guardrails.py`, `tests/test_guardrails_and_observability.py` | ✅ Complete |
| **9** | **Observability via Langfuse** | Integrated with Langfuse Cloud (`cloud.langfuse.com`) & self-hosted Docker container stack. Traces spans, tokens, latencies, and costs ($/₹). | `app/core/observability.py`, UI Cross Matrix | ✅ Complete |
| **10** | **End-to-End Evaluation & Costs** | Benchmarked across 5 enterprise scenarios. Live Cross Matrix in UI displaying latency, tokens, cost breakdown per agent. | `frontend/js/app.js`, `scripts/evaluate_performance.py` | ✅ Complete |
| **11** | **Cloud & Container Deployment** | 5-container Docker Compose architecture (`dealforge_app`, `dealforge_adk_service`, `dealforge_mysql`, `dealforge_langfuse`, `dealforge_langfuse_db`) + Render PaaS config. | `docker-compose.yml`, `Dockerfile`, `render.yaml` | ✅ Complete |

---

## 🏗️ System Architecture & 5-Container Topology

```
User Browser (Web UI :8000)
       │
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Container 1: dealforge_app (FastAPI Gateway & UI Dashboard)           │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │ 8-Agent CrewAI Sequential Procurement Pipeline               │     │
│   │ Requirement ➔ Vendor ➔ Price ➔ Compliance ➔ Evaluation      │     │
│   │ ➔ Budget ➔ Negotiation ➔ Workflow Coordination & PO          │     │
│   └───────────────┬───────────────────────────────┬──────────────┘     │
│                   │                               │                    │
│   ┌───────────────▼──────────────┐ ┌──────────────▼──────────────┐     │
│   │ Model Context Protocol (MCP) │ │ Agent-to-Agent (A2A) Client │     │
│   │ 10 FastMCP Procurement Tools │ │ Standard Message Envelope   │     │
│   └───────────────┬──────────────┘ └──────────────┬──────────────┘     │
└───────────────────┼───────────────────────────────┼────────────────────┘
                    │                               │ HTTP (:8001)
                    │ SQL (:3306)                   ▼
┌───────────────────▼──────────────┐ ┌───────────────────────────────────┐
│ Container 3: dealforge_mysql     │ │ Container 2: dealforge_adk_service│
│ MySQL 8.0 Relational Database    │ │ Google ADK Autonomous Risk Agent  │
│ 12 Tables (ACID Compliant)       │ │ Risk Audit & Anomaly Assessment   │
└──────────────────────────────────┘ └───────────────────────────────────┘
                    ▲                               ▲
                    │ Traces & Metrics              │ Spans & Cost
┌───────────────────┴───────────────────────────────┴────────────────────┐
│ Container 4 & 5: Langfuse Observability Platform (or Langfuse Cloud)   │
│ - dealforge_langfuse (Langfuse OSS Server & Web UI :3000)              │
│ - dealforge_langfuse_db (PostgreSQL 15 Dedicated Traces DB :5432)      │
│ - Public Cloud Endpoint: https://cloud.langfuse.com                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 👥 8 CrewAI Agents + 1 Google ADK Risk Agent

| # | Agent Name | Framework | Tool / Integration | Primary Responsibility |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Requirement Analysis Agent** | CrewAI | Pydantic Schema Extraction | Extracts category, specs, budget ceiling, delivery SLA from natural text. |
| **2** | **Vendor Research Agent** | CrewAI | FastMCP: `search_vendors` | Queries MySQL catalog to discover matching enterprise suppliers. |
| **3** | **Price Analysis Agent** | CrewAI | FastMCP: `calculate_quote_total` | Deterministically calculates volume discount tiers, 18% GST, and freight. |
| **4** | **Compliance Agent** | CrewAI | FastMCP: `get_compliance_status` | Audits supplier active status, warranty SLA, delivery deadlines, and stock. |
| **5** | **Deal Evaluation Agent** | CrewAI | Multi-Criteria Scoring Algorithm | Ranks compliant suppliers using weighted scoring (35% price, 20% SLA, etc.). |
| **6** | **Budget Validation Agent** | CrewAI | FastMCP: `validate_budget` | Compares Rank 1 total against budget ceiling; detects overruns. |
| **7** | **Negotiation Agent** | CrewAI | FastMCP: `save_negotiation_proposal` | Formulates data-backed counter-offers based on market rate deltas. |
| **8** | **Google ADK Risk Agent** | Google ADK | A2A Protocol (HTTP :8001) | Independent microservice assessing financial, supplier, and delivery risks. |
| **9** | **Workflow Coordination Agent** | CrewAI | FastMCP: `create_purchase_order` | Manages HITL approval pause/resume and commits formal Purchase Orders. |

---

## 🛠️ FastMCP Tools (10 Tools on 1 Server)

| Tool Name | Type | Description |
| :--- | :--- | :--- |
| `search_vendors` | Read | Searches active supplier directory matching product category. |
| `get_vendor_details` | Read | Returns vendor rating, contact info, and operational status. |
| `get_vendor_quotes` | Read | Fetches quote history for a given request. |
| `get_product_inventory` | Read | Checks inventory stock levels and replenishment lead time. |
| `get_compliance_status` | Read | Verifies vendor compliance against organizational procurement policy. |
| `calculate_quote_total` | Compute | Exact Decimal math: unit price $\times$ qty $-$ tier discount $+$ 18% GST $+$ freight. |
| `validate_budget` | Compute | Evaluates proposed quote against authorized budget limit. |
| `save_negotiation_proposal` | Mutate | Persists AI-generated counter-offer and target savings delta. |
| `create_approval_request` | Mutate | Submits approval task to human management queue. |
| `create_purchase_order` | Mutate | Generates formal, idempotent Purchase Order in MySQL. |

---

## 🛡️ Security Guardrails (4 Active Layers)

1. **Layer 1: Prompt Injection & Jailbreak Defense**: Regex and pattern-based blocking of jailbreak prompts, prompt exfiltration attempts (`ignore previous instructions`, `DAN`, `<script>`).
2. **Layer 2: Toxicity & Abuse Filter**: Intercepts toxic or abusive language before LLM ingestion.
3. **Layer 3: Domain Constraint Enforcement**: Validates that budget $> 0$, quantity is between 1 and 10,000, and product category is within supported enterprise catalogs.
4. **Layer 4: Pydantic V2 Strict Typing & Decimal Precision**: Zero floating-point arithmetic. Python `Decimal` is enforced across all financial computations.

---

## 👥 Group Member Contributions (Academic Viva Defense)

| Role | Core Responsibilities & Components Owned | Key Deliverables |
| :--- | :--- | :--- |
| **Multi-Agent Architect** | 8-agent sequential CrewAI orchestration pipeline, sequential state transitions, independent Google ADK Risk Agent service, A2A communication protocol. | `app/agents/crew.py`, `app/adk_service/agent.py`, `app/a2a/` |
| **Backend & MCP Engineer** | FastAPI REST endpoints, FastMCP server with 10 procurement tools, MySQL 8.0 schema and relational persistence, state machine pause/resume. | `app/mcp/server.py`, `app/mcp/client.py`, `app/db/` |
| **Security & Observability** | Multi-layered SecurityGuardrails (prompt injection & domain boundaries), Langfuse Cloud & OSS tracing platform, token accounting & cost cross matrix. | `app/core/guardrails.py`, `app/core/observability.py` |
| **DevOps & Frontend UI** | Modern dark-mode glassmorphic frontend UI, live Cross Matrix visualizer, 5-container Docker Compose architecture, Render cloud deployment config. | `frontend/`, `docker-compose.yml`, `render.yaml` |

---

## 🚀 Execution & Quick Start Guide

### 1. Launch Web Application & Dashboard
```powershell
# In project root with venv activated:
.\venv\Scripts\python.exe run.py
```
- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Observability & Cross Matrix**: [http://localhost:8000](http://localhost:8000) $\rightarrow$ Click *"Cross Matrix & Observability"* in sidebar

### 2. Run Terminal Multi-Agent Demonstration
```powershell
.\venv\Scripts\python.exe scripts/run_demo.py
```
Executes the full 8-agent workflow, FastMCP tools, Google ADK risk audit over A2A, HITL approval gate, and PO issuance directly in your console.

### 3. Run Automated Validation Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest tests
```
*All 20 tests pass with 100% success rate across E2E workflows, guardrails, and business services.*

### 4. 5-Container Docker Deployment
```bash
docker compose up --build -d
```
Starts all 5 containers: `dealforge_app` (:8000), `dealforge_adk_service` (:8001), `dealforge_mysql` (:3306), `dealforge_langfuse` (:3000), and `dealforge_langfuse_db` (:5432).
