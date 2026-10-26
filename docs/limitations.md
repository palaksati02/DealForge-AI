# DealForge AI — System Limitations & Future Roadmap

## 1. Scope & System Boundaries

DealForge AI was architected as an enterprise-grade agentic procurement automation platform fulfilling the **Senior Software Engineering Implementation Playbook**. To achieve strict determinism, reproducible verification, and zero hallucination in financial transactions, certain pragmatic boundaries were established for the current release.

---

## 2. Current Architectural Limitations

### 2.1 Currency & Taxation Modeling
- **Current State**: The platform standardizes on Indian Rupees (INR, ₹) and applies an 18% Goods and Services Tax (GST) bracket with fixed freight tier calculation models.
- **Limitation**: Cross-border foreign exchange conversion, dynamic Harmonized System (HS) tariff classification, and multi-jurisdictional VAT/sales taxes are not modeled.
- **Production Recommendation**: Integrate a live FX rate service (e.g., OpenExchangeRates) and a tax calculation engine (e.g., Vertex or Avalara) parameterized by vendor shipping origin and corporate receiving warehouse.

### 2.2 Vendor Integration & Catalog Access
- **Current State**: Vendor catalogs, stock quantities, and certifications are managed in MySQL 8.x and accessed via 16 FastMCP tools.
- **Limitation**: Real-time supplier inventory is queried from the local relational repository rather than through live B2B EDI (Electronic Data Interchange), cXML punchout, or external ERP connectors (SAP Ariba, Coupa, Oracle Fusion).
- **Production Recommendation**: Develop external MCP adapter bridges that connect FastMCP to standard SAP cXML PunchOut catalogs and Coupa REST APIs.

### 2.3 Task Queue & Concurrency Model
- **Current State**: Google ADK orchestrator workflows run asynchronously using Python `asyncio` and stream real-time updates via Server-Sent Events (SSE). Database connections are managed via SQLAlchemy connection pooling.
- **Limitation**: In high-load corporate deployments processing thousands of concurrent procurement runs, in-process Python tasks could saturate single-node worker threads.
- **Production Recommendation**: Transition the ADK agent execution dispatch to a distributed task broker (such as Celery with Redis or RabbitMQ, or Temporal workflow engine), retaining the A2A HTTP contracts as service boundaries.

### 2.4 Multi-Tenancy Architecture
- **Current State**: DealForge AI operates on a single-organization model with role-based access control (`PROCUREMENT_MANAGER`, `FINANCE_APPROVER`, `SYSTEM_ADMIN`).
- **Limitation**: Multiple independent enterprises cannot currently share a single database instance without schema partitioning.
- **Production Recommendation**: Implement row-level `tenant_id` scoping or schema-per-tenant isolation using SQLAlchemy multi-tenant mixins, combined with OAuth2/OIDC identity provider mapping.

### 2.5 Dynamic LLM vs. Deterministic Demo Mode
- **Current State**: All 10 Playbook business scenarios, financial calculations, compliance audits, and negotiation boundaries execute with 100% deterministic Python code in `DEMO_MODE=True`. External LLMs are optional.
- **Limitation**: While deterministic mode guarantees zero arithmetic errors and instant test execution, the counter-offer draft emails follow structured templates rather than open-ended conversational generation.
- **Production Recommendation**: When `DEMO_MODE=False` and a valid `GEMINI_API_KEY` is provided, enable hybrid execution where Google Gemini 1.5 Pro generates context-aware persuasive negotiation text while strictly bounded by the deterministic pricing limits.

---

## 3. Production Hardening Roadmap

### Phase A: Enterprise Identity & Single Sign-On (SSO)
- [ ] Implement SAML 2.0 / OIDC integrations for Okta, Azure Active Directory, and PingFederate.
- [ ] Enforce Two-Factor Authentication (2FA / MFA) for financial approval gates exceeding ₹25,00,000.
- [ ] Implement session revocation and refresh token rotation.

### Phase B: External Vendor Portal & Interactive Bidding
- [ ] Expose an authenticated external supplier portal where invited vendors can inspect counter-offers and submit binding counter-bids directly.
- [ ] Automated email dispatch (SendGrid / AWS SES) with cryptographic one-time action links for vendor quotation submission.
- [ ] Cryptographic digital signatures (e-Sign / DocuSign) for generated Purchase Orders.

### Phase C: Advanced Analytics & Spend Intelligence
- [ ] Predictive spend forecasting using historical procurement patterns.
- [ ] Supplier performance scorecard tracking delivery SLA adherence and warranty claim rates over time.
- [ ] Anomaly detection for invoice fraud, duplicate billing, and split-order threshold evasion.

### Phase D: Enterprise ERP & Document Output
- [ ] Bi-directional sync with SAP S/4HANA, NetSuite, and Microsoft Dynamics 365.
- [ ] High-fidelity PDF Purchase Order generation with embedded company watermarks and barcodes using headless Chromium or WeasyPrint.
- [ ] Integration with corporate contract management systems (Ironclad, Agiloft).
