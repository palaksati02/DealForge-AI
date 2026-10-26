# DealForge AI — Dependency Compatibility & Runtime Environment

## 1. Runtime Environment Specification

- **Python Version**: 3.11.9 (Verified)
- **Operating System**: Windows 11 (x86_64)
- **Node.js**: v22.23.2
- **npm**: 10.9.1
- **Primary Database**: MySQL Server 8.4.9 Community Edition (Listening on `127.0.0.1:3306`)

---

## 2. Core Framework Compatibility Matrix

| Technology | Selected Version | Compatibility Analysis | Status |
| :--- | :--- | :--- | :--- |
| **Google Agent Development Kit (ADK)** | `google-adk>=2.11.0` | Official Google Agent Development Kit for multi-agent lifecycle orchestration and session state management. Fully compatible with Python 3.11 and Pydantic V2. | Verified Compatible |
| **CrewAI** | `crewai>=0.80.0, <2.0.0` | Specialized agent team for deep domain analysis, multi-criteria trade-offs, and compliance evaluation. Integrates with Pydantic V2 and LangChain Core. | Verified Compatible |
| **Model Context Protocol (MCP)** | `mcp>=1.2.0, <2.0.0` (`fastmcp>=1.0`) | Official Anthropic Model Context Protocol SDK for Python. Provides typed tool registration, schema generation, and stdio/HTTP transport. | Installed (1.26.0) |
| **Agent-to-Agent (A2A)** | Custom Protocol Spec `A2A/1.0` | Standardized agent card discovery (`/.well-known/agent.json`), asynchronous task lifecycles, correlation tracking, and message envelopes. | Verified Compatible |
| **FastAPI** | `fastapi>=0.115.0` | Asynchronous REST API framework, Pydantic V2 native integration, OpenAPI documentation generation. | Installed (0.115.12) |
| **SQLAlchemy** | `sqlalchemy>=2.0.30` | 2.0-style mapped columns, typed queries, connection pooling, and transactional isolation. | Installed (2.0.35) |
| **Alembic** | `alembic>=1.13.0` | Relational schema migration management for MySQL 8.x. | Installed (1.13.1) |
| **Pydantic & Pydantic-Settings** | `pydantic>=2.10.0`, `pydantic-settings>=2.6.0` | Data contracts, settings management, and runtime schema validation. | Installed (2.11.3) |
| **PyMySQL & Cryptography** | `pymysql>=1.1.0`, `cryptography>=43.0.0` | Pure-Python MySQL 8.x database driver with `caching_sha2_password` authentication support. | Installed |
| **Pytest & Pytest-Asyncio** | `pytest>=8.0.0`, `pytest-asyncio>=0.24.0` | Automated testing framework for unit, integration, and end-to-end scenarios. | Installed (8.3.5) |

---

## 3. Strict LangGraph Prohibition

DealForge AI strictly prohibits the use of LangGraph, including any indirect dependencies used for workflow orchestration, state management, routing, or dynamic replanning.

- **Orchestration**: Exclusively handled by Google ADK (`google.adk.Agent` and ADK coordination facilities).
- **Specialized Analysis**: Exclusively handled by CrewAI (`crewai.Crew`).
- **Tool Protocol**: Exclusively handled by the official Python MCP SDK.
- **Inter-Service Protocol**: Exclusively handled by the A2A protocol.
- **Verification**: Complete repository audit confirmed zero occurrences of `langgraph` in source code or dependency definitions.

---

## 4. Transitive Dependency Resolution & Conflict Mitigation

1. **Pydantic V2 Alignment**:
   - Both `google-adk`, `crewai`, and `mcp` require Pydantic V2.
   - Pydantic 2.11+ provides stable compatibility with all three ecosystems.
2. **OpenTelemetry Semantics**:
   - Both `google-adk` and `crewai` utilize OpenTelemetry for agent tracing.
   - Pinned `opentelemetry-api` and `opentelemetry-sdk` to compatible releases (1.44+).
3. **HTTP Client & Asyncio**:
   - `httpx>=0.27.0` is shared across FastAPI test client, MCP HTTP transport, and A2A service clients.
   - All async tasks use standard `asyncio` event loops managed by Uvicorn.
