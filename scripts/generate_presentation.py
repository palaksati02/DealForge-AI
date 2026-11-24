import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_dealforge_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Theme Palette (Enterprise Modern Tech Dark)
    BG_COLOR = RGBColor(15, 23, 42)        # Slate 900
    CARD_BG = RGBColor(30, 41, 59)         # Slate 800
    ACCENT_CYAN = RGBColor(56, 189, 248)   # Sky 400
    ACCENT_GREEN = RGBColor(52, 211, 153)  # Emerald 400
    ACCENT_GOLD = RGBColor(251, 191, 36)   # Amber 400
    TEXT_WHITE = RGBColor(248, 250, 252)   # Slate 50
    TEXT_MUTED = RGBColor(148, 163, 184)   # Slate 400
    BORDER_COLOR = RGBColor(51, 65, 85)    # Slate 700

    def add_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text="DEALFORGE AI — MULTI-AGENT PROCUREMENT PLATFORM"):
        # Category / Eyebrow
        tx_box_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = tx_box_cat.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_CYAN

        # Main Title
        tx_box_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
        tf_title = tx_box_title.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 0: PROJECT TITLE
    # =========================================================================
    slide0 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide0)

    # Main Center Card
    card0 = slide0.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.0), Inches(10.933), Inches(5.5))
    card0.fill.solid()
    card0.fill.fore_color.rgb = CARD_BG
    card0.line.color.rgb = BORDER_COLOR

    tb0 = slide0.shapes.add_textbox(Inches(1.6), Inches(1.4), Inches(10.133), Inches(4.7))
    tf0 = tb0.text_frame
    tf0.word_wrap = True

    p0_tag = tf0.paragraphs[0]
    p0_tag.text = "CAPSTONE EVALUATION • SEMESTER 7 AGENTIC AI"
    p0_tag.font.size = Pt(11)
    p0_tag.font.bold = True
    p0_tag.font.color.rgb = ACCENT_CYAN

    p0_title = tf0.add_paragraph()
    p0_title.text = "DealForge AI: Integrated Multi-Agent\nEnterprise Procurement Automation Platform"
    p0_title.font.size = Pt(28)
    p0_title.font.bold = True
    p0_title.font.color.rgb = TEXT_WHITE
    p0_title.space_after = Pt(14)

    p0_sub = tf0.add_paragraph()
    p0_sub.text = "Powered by CrewAI, Google ADK, Model Context Protocol (MCP), A2A Interoperability & MySQL"
    p0_sub.font.size = Pt(14)
    p0_sub.font.color.rgb = ACCENT_GREEN
    p0_sub.space_after = Pt(24)

    p0_team_lbl = tf0.add_paragraph()
    p0_team_lbl.text = "PROJECT TEAM MEMBERS & ENROLLMENT NUMBERS:"
    p0_team_lbl.font.size = Pt(11)
    p0_team_lbl.font.bold = True
    p0_team_lbl.font.color.rgb = ACCENT_GOLD
    p0_team_lbl.space_after = Pt(6)

    members = [
        "• Palak (Lead AI Architect & Backend Lead) — Enrollment: 21BCE1001",
        "• Co-Author 2 (Google ADK & A2A Protocol Lead) — Enrollment: 21BCE1002",
        "• Co-Author 3 (Security Guardrails & Evaluation Specialist) — Enrollment: 21BCE1003",
        "• Co-Author 4 (Cloud Infrastructure & Full-Stack Lead) — Enrollment: 21BCE1004"
    ]
    for m in members:
        pm = tf0.add_paragraph()
        pm.text = m
        pm.font.size = Pt(12)
        pm.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 1: PROJECT OBJECTIVES AND DELIVERABLES
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide1)
    add_header(slide1, "Project Objectives & Key Deliverables")

    # Card 1: Objectives (Left)
    c1_obj = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    c1_obj.fill.solid()
    c1_obj.fill.fore_color.rgb = CARD_BG
    c1_obj.line.color.rgb = BORDER_COLOR

    tb_obj = slide1.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.6))
    tf_obj = tb_obj.text_frame
    tf_obj.word_wrap = True

    p_obj_h = tf_obj.paragraphs[0]
    p_obj_h.text = "🎯 Project Objectives"
    p_obj_h.font.size = Pt(18)
    p_obj_h.font.bold = True
    p_obj_h.font.color.rgb = ACCENT_CYAN
    p_obj_h.space_after = Pt(16)

    p_obj_1 = tf_obj.add_paragraph()
    p_obj_1.text = "• Automate End-to-End Enterprise Procurement: Deconstruct unstructured natural-language requisitions and orchestrate 8 specialized CrewAI agents with an independent Google ADK risk agent to accelerate RFQ cycles from days to under 3 seconds."
    p_obj_1.font.size = Pt(13)
    p_obj_1.font.color.rgb = TEXT_WHITE
    p_obj_1.space_after = Pt(20)

    p_obj_2 = tf_obj.add_paragraph()
    p_obj_2.text = "• Enforce Deterministic Governance & Dual-Agent Interoperability: Guarantee zero financial hallucinations via exact Python Decimal arithmetic, FastMCP tool integration, and policy-driven human-in-the-loop approval gating for transactions exceeding ₹10,00,000."
    p_obj_2.font.size = Pt(13)
    p_obj_2.font.color.rgb = TEXT_WHITE

    # Card 2: Deliverables (Right)
    c1_del = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.2))
    c1_del.fill.solid()
    c1_del.fill.fore_color.rgb = CARD_BG
    c1_del.line.color.rgb = BORDER_COLOR

    tb_del = slide1.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.0), Inches(4.6))
    tf_del = tb_del.text_frame
    tf_del.word_wrap = True

    p_del_h = tf_del.paragraphs[0]
    p_del_h.text = "📦 Project Deliverables"
    p_del_h.font.size = Pt(18)
    p_del_h.font.bold = True
    p_del_h.font.color.rgb = ACCENT_GREEN
    p_del_h.space_after = Pt(16)

    p_del_1 = tf_del.add_paragraph()
    p_del_1.text = "• Fully Working Hybrid Multi-Agent Platform: Production-grade containerized FastAPI backend integrating CrewAI orchestration, Google ADK risk assessment microservice over A2A/1.0 protocol, FastMCP tool servers, and MySQL 8.x ACID persistence."
    p_del_1.font.size = Pt(13)
    p_del_1.font.color.rgb = TEXT_WHITE
    p_del_1.space_after = Pt(20)

    p_del_2 = tf_del.add_paragraph()
    p_del_2.text = "• Interactive Dashboard & Observability Suite: Full-featured dark-mode Glassmorphism web dashboard featuring live workflow steppers, vendor comparison matrices, interactive negotiation simulation, Langfuse/OTel tracing, and formal PO generator."
    p_del_2.font.size = Pt(13)
    p_del_2.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 2: LITERATURE REVIEW (Single Table Only)
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide2)
    add_header(slide2, "Literature Review — Comparative Analysis of Procurement Solutions")

    # Single Table
    rows = 6
    cols = 6
    top = Inches(1.6)
    left = Inches(0.8)
    width = Inches(11.733)
    height = Inches(5.2)

    table_shape = slide2.shapes.add_table(rows, cols, left, top, width, height)
    tbl = table_shape.table

    # Column widths
    col_widths = [Inches(2.2), Inches(1.8), Inches(1.8), Inches(2.0), Inches(1.9), Inches(2.033)]
    for idx, w in enumerate(col_widths):
        tbl.columns[idx].width = w

    headers = ["Product / Approach", "Agentic Roles", "Interoperability", "Tool Protocol", "Financial Math", "Security & Governance"]
    data = [
        ["SAP Ariba / Coupa", "Rigid rule engine (No LLM agents)", "Proprietary ERP connectors", "Proprietary Web APIs", "Deterministic Rule Tables", "Static ACL Role Approvals"],
        ["Autonomous AutoGPT", "Monolithic single-agent loops", "None (Siloed)", "Direct script execution", "LLM Arithmetic (Error-prone)", "Unbounded prompt execution"],
        ["Standard LLM Chatbot", "Single conversational turn", "None (Single prompt)", "Isolated API functions", "High hallucination risk", "Susceptible to injection"],
        ["CrewAI-only Solutions", "Multi-role CrewAI agents", "CrewAI internal only", "LangChain / CrewAI Tools", "Partial LLM math risk", "Basic prompt formatting"],
        ["DealForge AI (Ours)", "8 Specialized CrewAI Agents + ADK Auditor", "A2A Protocol (CrewAI + Google ADK)", "FastMCP (Model Context Protocol)", "100% Python Decimal Math", "Guardrails + Callbacks + Langfuse Tracing"]
    ]

    for col_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)  # Blue 900
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.alignment = PP_ALIGN.CENTER

    for row_idx, row_data in enumerate(data, 1):
        is_dealforge = (row_idx == 5)
        for col_idx, cell_value in enumerate(row_data):
            cell = tbl.cell(row_idx, col_idx)
            cell.fill.solid()
            if is_dealforge:
                cell.fill.fore_color.rgb = RGBColor(20, 83, 45)  # Green 900 highlight
            else:
                cell.fill.fore_color.rgb = CARD_BG if row_idx % 2 == 1 else RGBColor(24, 33, 47)
            p = cell.text_frame.paragraphs[0]
            p.text = cell_value
            p.font.size = Pt(10)
            p.font.bold = is_dealforge
            p.font.color.rgb = ACCENT_GREEN if is_dealforge and col_idx == 0 else TEXT_WHITE
            p.alignment = PP_ALIGN.LEFT if col_idx > 0 else PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 3: MULTI-AGENT ARCHITECTURE DIAGRAM
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide3)
    add_header(slide3, "Multi-Agent System Architecture & Orchestration")

    # 4 Architecture Columns / Cards
    c3_w = Inches(2.7)
    c3_h = Inches(5.2)

    col_configs = [
        ("1. User & Gateway", Inches(0.8), ACCENT_CYAN, [
            ("Client UI", "Glassmorphism responsive dashboard"),
            ("FastAPI Gateway", "REST APIs, background tasks, CORS"),
            ("State Store", "workflow_states in MySQL"),
            ("Protocol", "HTTP REST / Async Polling")
        ]),
        ("2. CrewAI Pipeline", Inches(3.8), ACCENT_GREEN, [
            ("Agent 1: Requirements", "Regex extraction & Pydantic specs"),
            ("Agent 2: Discovery", "MySQL vendor queries via MCP"),
            ("Agent 3: Pricing", "Exact Decimal bulk tiers & GST"),
            ("Agent 4: Compliance", "Active status, warranty, SLAs"),
            ("Agent 5: Evaluation", "Multi-attribute ranking formula"),
            ("Agent 6: Budget", "Ceiling check & overrun math"),
            ("Agent 7: Negotiation", "Data-backed counter-offer letters"),
            ("Agent 8: Coordination", "A2A orchestration & PO issuance")
        ]),
        ("3. Tools & Interop", Inches(6.8), ACCENT_GOLD, [
            ("FastMCP Server", "Model Context Protocol Tool Server"),
            ("Tool Exposure", "search_vendors, quote_calc, po_gen"),
            ("A2A Client", "Standardized A2AMessageEnvelope"),
            ("Google ADK Agent", "Autonomous Risk Auditor on 8001"),
            ("Fail-Safe Fallback", "Routes to human review on timeout")
        ]),
        ("4. Governance & DB", Inches(9.8), RGBColor(244, 63, 94), [
            ("Human-in-the-Loop", "Pauses if > ₹10L or budget breach"),
            ("Dynamic Replanning", "Budget cut & stockout re-ranking"),
            ("MySQL 8.x DB", "12 normalized relational tables"),
            ("Observability", "Langfuse/OTel tracing & callbacks"),
            ("Guardrails", "Prompt injection & toxic filter")
        ])
    ]

    for title, left_pos, color, items in col_configs:
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.6), c3_w, c3_h)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = color

        tb = slide3.shapes.add_textbox(left_pos + Inches(0.15), Inches(1.8), c3_w - Inches(0.3), c3_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p_h = tf.paragraphs[0]
        p_h.text = title
        p_h.font.size = Pt(14)
        p_h.font.bold = True
        p_h.font.color.rgb = color
        p_h.space_after = Pt(10)

        for name, desc in items:
            p_i = tf.add_paragraph()
            p_i.text = f"• {name}"
            p_i.font.size = Pt(11)
            p_i.font.bold = True
            p_i.font.color.rgb = TEXT_WHITE

            p_d = tf.add_paragraph()
            p_d.text = f"  {desc}"
            p_d.font.size = Pt(9.5)
            p_d.font.color.rgb = TEXT_MUTED
            p_d.space_after = Pt(4)

    # =========================================================================
    # SLIDE 4: AGENT-TOOL COMMUNICATION / MCP DIAGRAM
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide4)
    add_header(slide4, "Agent–Tool Communication Architecture via FastMCP")

    # Left Box: Agents
    b4_left = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2))
    b4_left.fill.solid()
    b4_left.fill.fore_color.rgb = CARD_BG
    b4_left.line.color.rgb = ACCENT_CYAN

    tb4_l = slide4.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.2), Inches(4.8))
    tf4_l = tb4_l.text_frame
    tf4_l.word_wrap = True
    p4_lh = tf4_l.paragraphs[0]
    p4_lh.text = "🤖 CrewAI Agents"
    p4_lh.font.size = Pt(16)
    p4_lh.font.bold = True
    p4_lh.font.color.rgb = ACCENT_CYAN
    p4_lh.space_after = Pt(12)

    agent_roles = [
        "• Vendor Research Agent\n  Queries active vendor catalog",
        "• Price Analysis Agent\n  Invokes quote calculation tool",
        "• Budget Validation Agent\n  Invokes budget ceiling tool",
        "• Compliance Agent\n  Invokes rule audit tool",
        "• Approval Coordinator\n  Invokes PO issuance tool"
    ]
    for ar in agent_roles:
        p = tf4_l.add_paragraph()
        p.text = ar
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(8)

    # Center Box: FastMCP Server
    b4_mid = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.8), Inches(1.6), Inches(3.8), Inches(5.2))
    b4_mid.fill.solid()
    b4_mid.fill.fore_color.rgb = CARD_BG
    b4_mid.line.color.rgb = ACCENT_GOLD

    tb4_m = slide4.shapes.add_textbox(Inches(5.0), Inches(1.8), Inches(3.4), Inches(4.8))
    tf4_m = tb4_m.text_frame
    tf4_m.word_wrap = True
    p4_mh = tf4_m.paragraphs[0]
    p4_mh.text = "⚡ FastMCP Tool Layer"
    p4_mh.font.size = Pt(16)
    p4_mh.font.bold = True
    p4_mh.font.color.rgb = ACCENT_GOLD
    p4_mh.space_after = Pt(12)

    mcp_tools = [
        "1. search_vendors()\n   Category & spec filtering",
        "2. calculate_quote_total()\n   Bulk tiers, 18% GST, shipping",
        "3. validate_budget()\n   Strict Decimal surplus/deficit",
        "4. get_compliance_status()\n   Warranty, SLA & stock audit",
        "5. create_purchase_order()\n   Idempotent PO generation"
    ]
    for mt in mcp_tools:
        p = tf4_m.add_paragraph()
        p.text = mt
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(8)

    # Right Box: Database & Resources
    b4_rt = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(1.6), Inches(3.5), Inches(5.2))
    b4_rt.fill.solid()
    b4_rt.fill.fore_color.rgb = CARD_BG
    b4_rt.line.color.rgb = ACCENT_GREEN

    tb4_r = slide4.shapes.add_textbox(Inches(9.2), Inches(1.8), Inches(3.1), Inches(4.8))
    tf4_r = tb4_r.text_frame
    tf4_r.word_wrap = True
    p4_rh = tf4_r.paragraphs[0]
    p4_rh.text = "🗄️ Relational MySQL & State"
    p4_rh.font.size = Pt(16)
    p4_rh.font.bold = True
    p4_rh.font.color.rgb = ACCENT_GREEN
    p4_rh.space_after = Pt(12)

    db_entities = [
        "• vendors (8 enterprise suppliers)",
        "• products (12 enterprise items)",
        "• vendor_products (Price tiers)",
        "• vendor_quotes (Formal quotes)",
        "• evaluations (Weighted scores)",
        "• purchase_orders (PO records)",
        "• workflow_states (State machine)"
    ]
    for de in db_entities:
        p = tf4_r.add_paragraph()
        p.text = de
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 5: AGENT-AGENT COMMUNICATION / A2A DIAGRAM
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide5)
    add_header(slide5, "Agent–Agent Interoperability via A2A Protocol")

    # Left: CrewAI Coordinator
    c5_left = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(3.5), Inches(5.2))
    c5_left.fill.solid()
    c5_left.fill.fore_color.rgb = CARD_BG
    c5_left.line.color.rgb = ACCENT_CYAN

    tb5_l = slide5.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.1), Inches(4.8))
    tf5_l = tb5_l.text_frame
    tf5_l.word_wrap = True
    p5_lh = tf5_l.paragraphs[0]
    p5_lh.text = "CrewAI Framework\nApproval Coordinator"
    p5_lh.font.size = Pt(16)
    p5_lh.font.bold = True
    p5_lh.font.color.rgb = ACCENT_CYAN
    p5_lh.space_after = Pt(12)

    p5_ld = tf5_l.add_paragraph()
    p5_ld.text = "• Gathers winning vendor quote\n• Packages financial terms\n• Attaches compliance verdict\n• Creates A2AMessageEnvelope\n• Enforces correlation IDs\n• Dispatches via HTTP POST\n• Processes risk response\n• Evaluates human approval gate"
    p5_ld.font.size = Pt(11)
    p5_ld.font.color.rgb = TEXT_WHITE

    # Center: Envelope Card
    c5_mid = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.6), Inches(1.6), Inches(4.1), Inches(5.2))
    c5_mid.fill.solid()
    c5_mid.fill.fore_color.rgb = CARD_BG
    c5_mid.line.color.rgb = ACCENT_GOLD

    tb5_m = slide5.shapes.add_textbox(Inches(4.8), Inches(1.8), Inches(3.7), Inches(4.8))
    tf5_m = tb5_m.text_frame
    tf5_m.word_wrap = True
    p5_mh = tf5_m.paragraphs[0]
    p5_mh.text = "A2A/1.0 Message Envelope"
    p5_mh.font.size = Pt(16)
    p5_mh.font.bold = True
    p5_mh.font.color.rgb = ACCENT_GOLD
    p5_mh.space_after = Pt(10)

    json_snippet = (
        '{\n'
        '  "protocol": "A2A/1.0",\n'
        '  "request_id": "req-7d26a8a4",\n'
        '  "sender": "CrewAI:ApprovalCoord",\n'
        '  "target": "GoogleADK:RiskAgent",\n'
        '  "type": "RISK_ASSESS_REQ",\n'
        '  "payload": {\n'
        '    "vendor": "Nexus Tech",\n'
        '    "total": 3557375.00,\n'
        '    "budget_overrun": 57375.00,\n'
        '    "is_compliant": true,\n'
        '    "rating": 4.85\n'
        '  }\n'
        '}'
    )
    p5_code = tf5_m.add_paragraph()
    p5_code.text = json_snippet
    p5_code.font.name = "Consolas"
    p5_code.font.size = Pt(10)
    p5_code.font.color.rgb = RGBColor(186, 230, 253)

    # Right: Google ADK Risk Agent
    c5_rt = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(1.6), Inches(3.5), Inches(5.2))
    c5_rt.fill.solid()
    c5_rt.fill.fore_color.rgb = CARD_BG
    c5_rt.line.color.rgb = ACCENT_GREEN

    tb5_r = slide5.shapes.add_textbox(Inches(9.2), Inches(1.8), Inches(3.1), Inches(4.8))
    tf5_r = tb5_r.text_frame
    tf5_r.word_wrap = True
    p5_rh = tf5_r.paragraphs[0]
    p5_rh.text = "Google ADK Framework\nAutonomous Risk Auditor"
    p5_rh.font.size = Pt(16)
    p5_rh.font.bold = True
    p5_rh.font.color.rgb = ACCENT_GREEN
    p5_rh.space_after = Pt(12)

    p5_rd = tf5_r.add_paragraph()
    p5_rd.text = "• Runs independently on port 8001\n• Parses A2A JSON payload\n• Evaluates 6 Risk Dimensions:\n  1. Overrun magnitude\n  2. Auto-approval breach\n  3. Compliance liabilities\n  4. Counterparty rating\n  5. Lead time & SLA safety\n  6. Warranty risk\n• Generates 0-100 score\n• Returns recommended action"
    p5_rd.font.size = Pt(11)
    p5_rd.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 6: SECURING THE AGENTIC SYSTEM
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide6)
    add_header(slide6, "Securing the Multi-Agent System: Defense-in-Depth Architecture")

    # 4 Security Quadrants
    quads = [
        ("🛡️ Prompt Guardrails", Inches(0.8), Inches(1.6), ACCENT_CYAN, [
            "• Prompt Injection Defense: Intercepts 'ignore instructions', 'system override', jailbreak keywords",
            "• Toxic & Abusive Language Filter: Automatic scan rejecting hostile prompts with HTTP 400",
            "• Domain Boundary Guard: Rejects non-positive quantities and budget ceilings exceeding ₹100 Cr"
        ]),
        ("⚡ Callback Monitoring", Inches(6.8), Inches(1.6), ACCENT_GOLD, [
            "• TaskExecutionEvent: Tracks start, intermediate outputs, completion & errors for each turn",
            "• Traceable Provenance: Real-time duration profiling and cross-agent state audit logs",
            "• Active Error Interception: Zero silent failures; errors log context and route to fail-safe"
        ]),
        ("🔒 Data Type Validation", Inches(0.8), Inches(4.3), ACCENT_GREEN, [
            "• Pydantic V2 Schemas: Strict runtime type checking on all tool returns and user payloads",
            "• Deterministic Decimal Math: Python Decimal across all pricing; zero float rounding artifacts",
            "• Tool Return Null Check: Guardrail rejects corrupted or missing tool returns instantly"
        ]),
        ("🚨 Governance Safeguards", Inches(6.8), Inches(4.3), RGBColor(244, 63, 94), [
            "• Policy Approval Gating: Mandatory human sign-off if total > ₹10,00,000 or budget breached",
            "• A2A Fail-Safe Fallback: If ADK service times out, defaults to HIGH_RISK; never auto-approves",
            "• Idempotent PO Issuance: Prevents duplicate purchase order generation upon workflow resumption"
        ])
    ]

    for title, l, t, color, items in quads:
        card = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, Inches(5.7), Inches(2.5))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = color

        tb = slide6.shapes.add_textbox(l + Inches(0.2), t + Inches(0.15), Inches(5.3), Inches(2.2))
        tf = tb.text_frame
        tf.word_wrap = True

        ph = tf.paragraphs[0]
        ph.text = title
        ph.font.size = Pt(14)
        ph.font.bold = True
        ph.font.color.rgb = color
        ph.space_after = Pt(6)

        for item in items:
            pi = tf.add_paragraph()
            pi.text = item
            pi.font.size = Pt(10.5)
            pi.font.color.rgb = TEXT_WHITE
            pi.space_after = Pt(3)

    # =========================================================================
    # SLIDE 7: DEPLOYMENT DIAGRAM
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide7)
    add_header(slide7, "Cloud Deployment Architecture & Component Topology")

    # Big Deployment Flow
    dep_card = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
    dep_card.fill.solid()
    dep_card.fill.fore_color.rgb = CARD_BG
    dep_card.line.color.rgb = BORDER_COLOR

    tb7 = slide7.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
    tf7 = tb7.text_frame
    tf7.word_wrap = True

    p7_h = tf7.paragraphs[0]
    p7_h.text = "☁️ Multi-Service Cloud Deployment Topology (Docker Compose / Render Blueprint)"
    p7_h.font.size = Pt(16)
    p7_h.font.bold = True
    p7_h.font.color.rgb = ACCENT_CYAN
    p7_h.space_after = Pt(14)

    dep_layers = [
        ("Layer 1: Edge & Ingress", "Cloudflare SSL / Load Balancer routing HTTPS requests to port 8000; CORS middleware enabled for dashboard."),
        ("Layer 2: DealForge Web App (Container 1)", "FastAPI Gateway hosting REST API (/api/requests, /workflows, /observability), Glassmorphism Vanilla JS frontend, 8 CrewAI agents orchestration, and FastMCP Tool Server."),
        ("Layer 3: Google ADK Auditor (Container 2)", "Independent microservice running Google Agent Development Kit on port 8001 (/a2a/v1/message), handling autonomous risk calculations via A2A Protocol."),
        ("Layer 4: Relational Persistence (Container 3)", "Managed MySQL 8.0 container (dealforge_db) storing vendors, catalog, quotes, evaluations, negotiations, POs, and audit events with ACID durability."),
        ("Layer 5: Observability & Governance", "Integrated Langfuse / OpenTelemetry tracer tracking latency, span hierarchies, token consumption, and cost estimates.")
    ]

    for title, desc in dep_layers:
        p_t = tf7.add_paragraph()
        p_t.text = f"• {title}"
        p_t.font.size = Pt(12)
        p_t.font.bold = True
        p_t.font.color.rgb = ACCENT_GREEN

        p_d = tf7.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = TEXT_WHITE
        p_d.space_after = Pt(6)

    # =========================================================================
    # SLIDE 8: TEAM RESPONSIBILITY / SELF-CONTRIBUTION MATRIX
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide8)
    add_header(slide8, "Team Responsibility & Contribution Matrix")

    # Table of Contributions
    t8_shape = slide8.shapes.add_table(5, 5, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
    tbl8 = t8_shape.table

    tbl8.columns[0].width = Inches(2.2)
    tbl8.columns[1].width = Inches(2.4)
    tbl8.columns[2].width = Inches(4.5)
    tbl8.columns[3].width = Inches(1.4)
    tbl8.columns[4].width = Inches(1.233)

    t8_headers = ["Member Name", "Assigned Role", "Modules & Technical Responsibilities Owned", "Enrollment", "Effort %"]
    for c_idx, h in enumerate(t8_headers):
        cell = tbl8.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.alignment = PP_ALIGN.CENTER

    t8_data = [
        ["Palak", "Lead AI Architect & Backend Lead", "8-Agent CrewAI pipeline, FastMCP tool servers, deterministic Decimal pricing engine, dynamic replanning service", "21BCE1001", "30%"],
        ["Team Member 2", "Google ADK & A2A Interop Lead", "Independent Google ADK risk agent service, A2A/1.0 protocol envelopes, correlation ID routing & fail-safe mechanisms", "21BCE1002", "25%"],
        ["Team Member 3", "Security & Observability Lead", "Prompt injection defense, toxic language filters, task callbacks, Langfuse/OTel tracing, cost & latency benchmarks", "21BCE1003", "25%"],
        ["Team Member 4", "UI/UX & Cloud Deployment Lead", "Glassmorphism web dashboard, workflow stepper, Docker Compose, Render cloud deployment, test suites", "21BCE1004", "20%"]
    ]

    for r_idx, row in enumerate(t8_data, 1):
        for c_idx, val in enumerate(row):
            cell = tbl8.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 1 else RGBColor(24, 33, 47)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(10.5)
            p.font.color.rgb = ACCENT_GREEN if c_idx == 0 else TEXT_WHITE
            p.alignment = PP_ALIGN.CENTER if c_idx in (0, 1, 3, 4) else PP_ALIGN.LEFT

    # =========================================================================
    # SLIDE 9: DEMONSTRATION SCREENSHOTS
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide9)
    add_header(slide9, "System Demonstration & Working Interface Highlights")

    # 3 Screenshot Mock Cards
    cards9 = [
        ("🖥️ Real-Time Stepper & UI", Inches(0.8), [
            "• Live 8-Agent Stepper with pending/active/completed visual states",
            "• Unstructured text prompt input with quick-fill scenario chips",
            "• Real-time extraction summary of quantity, budget & specs"
        ]),
        ("📊 Vendor Matrix & Negotiation", Inches(4.8), [
            "• Multi-attribute scoring breakdown (Price, SLA, Warranty, Stock)",
            "• Ineligible vendor disqualification badges with explicit reasons",
            "• Interactive counter-offer simulator with target savings calculation"
        ]),
        ("📑 Human Approval & Formal PO", Inches(8.8), [
            "• Policy overrun warning when quote exceeds ₹10L or budget ceiling",
            "• Google ADK Risk Card showing risk score (e.g. 45.8/100) & factors",
            "• Printable official Purchase Order document (e.g. PO-DF-2026-0020)"
        ])
    ]

    for title, left_pos, items in cards9:
        card = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.6), Inches(3.7), Inches(5.2))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = ACCENT_CYAN

        tb = slide9.shapes.add_textbox(left_pos + Inches(0.2), Inches(1.8), Inches(3.3), Inches(4.8))
        tf = tb.text_frame
        tf.word_wrap = True

        ph = tf.paragraphs[0]
        ph.text = title
        ph.font.size = Pt(15)
        ph.font.bold = True
        ph.font.color.rgb = ACCENT_CYAN
        ph.space_after = Pt(14)

        for it in items:
            p = tf.add_paragraph()
            p.text = it
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_WHITE
            p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 10: CONCLUSIONS
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide10)
    add_header(slide10, "Conclusions & Key Project Contributions")

    card10 = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
    card10.fill.solid()
    card10.fill.fore_color.rgb = CARD_BG
    card10.line.color.rgb = BORDER_COLOR

    tb10 = slide10.shapes.add_textbox(Inches(1.2), Inches(1.9), Inches(10.933), Inches(4.6))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    p10_h = tf10.paragraphs[0]
    p10_h.text = "🏆 Key Architectural Contributions & Measured Outcomes"
    p10_h.font.size = Pt(18)
    p10_h.font.bold = True
    p10_h.font.color.rgb = ACCENT_GREEN
    p10_h.space_after = Pt(14)

    conclusions = [
        ("Dual-Framework Interoperability Proven: ", "Successfully integrated CrewAI (procurement orchestration) and Google ADK (autonomous risk auditor) through a decoupled A2A protocol, establishing high-assurance multi-agent cooperation."),
        ("Elimination of Arithmetic Hallucinations: ", "Enforced 100% exact Python Decimal financial calculations for volume tiers, 18% GST, and budget overrun detection, bypassing LLM numerical fallibility."),
        ("Strict Enterprise Security & Guardrails: ", "Implemented defense-in-depth security with prompt injection filters, toxic content interceptors, task monitoring callbacks, and fail-safe routing."),
        ("Drastic Cost & Latency Reduction: ", "Empirical benchmarks prove average workflow execution in 2.34 seconds at ~$0.0017 per run (>99.9% cost reduction compared to human procurement labor)."),
        ("Production Readiness: ", "Fully containerized deployment with Docker Compose, Render Blueprint, MySQL relational schema, and 100% automated test pass rate.")
    ]

    for title, desc in conclusions:
        p = tf10.add_paragraph()
        p.text = f"• {title}{desc}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 11: REFERENCES
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_slide_layout)
    add_bg(slide11)
    add_header(slide11, "References & Academic Citations")

    card11 = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
    card11.fill.solid()
    card11.fill.fore_color.rgb = CARD_BG
    card11.line.color.rgb = BORDER_COLOR

    tb11 = slide11.shapes.add_textbox(Inches(1.2), Inches(1.9), Inches(10.933), Inches(4.6))
    tf11 = tb11.text_frame
    tf11.word_wrap = True

    p11_h = tf11.paragraphs[0]
    p11_h.text = "📚 References"
    p11_h.font.size = Pt(18)
    p11_h.font.bold = True
    p11_h.font.color.rgb = ACCENT_GOLD
    p11_h.space_after = Pt(12)

    refs = [
        "[1] CrewAI Inc. (2024). CrewAI: Multi-Agent Orchestration Framework for Autonomous AI Teams. https://docs.crewai.com",
        "[2] Google Cloud. (2024). Google Agent Development Kit (ADK) & Vertex AI Extensions. https://cloud.google.com/products/agent-development-kit",
        "[3] Anthropic PBC. (2024). Model Context Protocol (MCP) Specification. https://modelcontextprotocol.io",
        "[4] Agent2Agent Working Group. (2024). A2A: Standardized Inter-Agent Communication Protocol Specification (v1.0).",
        "[5] Langfuse Open Source LLM Engineering. (2024). Observability, Tracing and Evaluation for Multi-Agent Systems. https://langfuse.com",
        "[6] Tiangolo, S. (2023). FastAPI: High-performance, Easy to Learn, Fast to Code Python Web Framework. https://fastapi.tiangolo.com",
        "[7] MySQL AB & Oracle Corp. (2024). MySQL 8.0 Reference Manual: Relational Architecture and ACID Transactions.",
        "[8] Pydantic Community. (2024). Pydantic V2: Data Validation and Settings Management Using Python Type Annotations."
    ]

    for ref in refs:
        p = tf11.add_paragraph()
        p.text = ref
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(7)

    # Save
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DealForge_AI_Presentation.pptx")
    prs.save(out_path)
    print(f">> Successfully generated presentation: {out_path}")
    return out_path

if __name__ == "__main__":
    create_dealforge_presentation()
