import re
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from app.core.config import settings
from app.core.logging import logger
from app.core.callbacks import workflow_monitor
from app.mcp.client import (
    search_vendors_mcp,
    get_vendor_details_mcp,
    get_product_inventory_mcp,
    calculate_quote_total_mcp,
    validate_budget_mcp,
    create_purchase_order_mcp,
)


def get_configured_llm() -> LLM:
    """Instantiate configured LLM provider for CrewAI agents."""
    model_name = settings.GEMINI_MODEL
    if not model_name.startswith("gemini/"):
        model_name = f"gemini/{model_name}"
    
    api_key = settings.GEMINI_API_KEY or "demo-api-key"
    return LLM(model=model_name, api_key=api_key)


def build_procurement_crew(
    workflow_id: Optional[str] = None,
    request_id: Optional[str] = None,
    tools: Optional[List[Any]] = None
) -> Crew:
    """
    Constructs the specialised 8-Agent CrewAI Procurement Team with
    meaningful tasks, context dependencies, MCP tools, and monitoring callbacks.
    """
    # Initialize LLM driver
    llm = get_configured_llm()

    # -------------------------------------------------------------------------
    # 1. Specialized CrewAI Agents
    # -------------------------------------------------------------------------

    # Agent 1: Requirement Analysis Agent
    requirement_agent = Agent(
        role="Senior Requirement Analysis Specialist",
        goal="Deconstruct natural-language procurement requests into validated technical schemas without hallucinating parameters.",
        backstory=(
            "Expert enterprise requirements engineer with 15 years in IT procurement. "
            "You meticulously extract item category, specifications, quantities, budget constraints, "
            "and delivery deadlines, never inventing missing data."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 2: Vendor Research Agent (Equipped with FastMCP search tools)
    vendor_research_agent = Agent(
        role="Strategic Vendor Discovery Lead",
        goal="Discover eligible enterprise vendors and catalog listings from persistent MySQL database via FastMCP tools.",
        backstory=(
            "Procurement researcher specializing in corporate vendor directories and hardware catalogs. "
            "You query database systems via authorized FastMCP tools to find active vendors and stock availability."
        ),
        tools=[search_vendors_mcp, get_product_inventory_mcp, get_vendor_details_mcp],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 3: Price Analysis Agent (Equipped with FastMCP pricing tool)
    price_analysis_agent = Agent(
        role="Financial Pricing Analyst",
        goal="Deterministically compute pricing structures including tiered volume discounts, 18% GST, and logistics fees via FastMCP.",
        backstory=(
            "Certified enterprise cost accountant. You never trust probabilistic arithmetic; "
            "you rely strictly on deterministic algorithms and exact Decimal calculations for financial integrity."
        ),
        tools=[calculate_quote_total_mcp],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 4: Compliance Agent (Equipped with FastMCP vendor details tool)
    compliance_agent = Agent(
        role="Procurement Governance and Compliance Officer",
        goal="Enforce non-negotiable compliance rules including active vendor status, minimum warranty SLAs, and inventory thresholds.",
        backstory=(
            "Veteran corporate auditor who safeguards legal and operational policies. "
            "You verify supplier active status, delivery timelines, and warranty terms against corporate benchmarks."
        ),
        tools=[get_vendor_details_mcp],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 5: Deal Evaluation Agent
    deal_evaluation_agent = Agent(
        role="Multi-Criteria Deal Scoring Specialist",
        goal="Score and rank eligible supplier proposals using an explainable, weighted multi-attribute decision model.",
        backstory=(
            "Operations research expert focused on vendor selection. You combine price, delivery speed, "
            "warranty length, and compliance scores into a normalized ranking, rejecting ineligible vendors first."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 6: Budget Validation Agent (Equipped with FastMCP budget tool)
    budget_validation_agent = Agent(
        role="Corporate Budget Controller",
        goal="Audit proposed quotation costs against approved department budget ceilings and flag financial overruns via FastMCP.",
        backstory=(
            "Strict fiscal comptroller protecting corporate reserves. You verify financial caps "
            "and ensure no budget overrun escapes detection."
        ),
        tools=[validate_budget_mcp],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 7: Negotiation Agent
    negotiation_agent = Agent(
        role="Strategic Procurement Negotiator",
        goal="Draft data-backed counter-offers and persuasive justification letters to achieve target corporate savings.",
        backstory=(
            "Master B2B contract negotiator. You formulate strategic counter-offers based on market benchmarks, "
            "order volume, and prompt payment terms, logging all proposals in the database."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # Agent 8: Approval and Workflow Coordination Agent (Equipped with FastMCP PO tool)
    approval_coordination_agent = Agent(
        role="Procurement Orchestrator & Approval Officer",
        goal="Coordinate workflow progression, integrate Google ADK risk assessment via A2A protocol, and enforce human approval gates.",
        backstory=(
            "Enterprise workflow director who unifies the procurement pipeline, invokes independent risk audits, "
            "and pauses execution for human managers whenever governance limits require approval."
        ),
        tools=[create_purchase_order_mcp],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    # -------------------------------------------------------------------------
    # 2. Meaningful CrewAI Tasks with Dependencies and Expected Outputs
    # -------------------------------------------------------------------------

    task_requirements = Task(
        description=(
            "Deconstruct the user purchase request: '{raw_request_text}'. "
            "Extract: category, quantity, budget_limit, delivery_deadline_days, and warranty_requirement_months."
        ),
        expected_output="Structured requirements dictionary with validated category, quantity, budget limit, and deadlines.",
        agent=requirement_agent,
    )

    task_discovery = Task(
        description=(
            "Using the FastMCP tool 'search_vendors_mcp', search the database catalog for active vendors and "
            "matching products for the identified category. Return candidate supplier options and on-hand inventory."
        ),
        expected_output="List of discovered vendors and catalog products retrieved via FastMCP.",
        agent=vendor_research_agent,
        context=[task_requirements],
    )

    task_pricing = Task(
        description=(
            "Using FastMCP tool 'calculate_quote_total_mcp', deterministically calculate base subtotals, "
            "bulk tiered discounts, 18% statutory GST, and shipping fees for all candidate vendor quotes."
        ),
        expected_output="Itemized financial quotations with gross subtotals, discounts, tax, and final totals.",
        agent=price_analysis_agent,
        context=[task_discovery],
    )

    task_compliance = Task(
        description=(
            "Audit candidate vendor proposals against corporate procurement governance policies: "
            "1. Active ERP directory status. 2. Warranty >= required months. 3. Delivery timeline <= required SLA. "
            "4. Sufficient on-hand inventory. Flag any violations."
        ),
        expected_output="Compliance verification report with pass/fail status and violation reasons per vendor.",
        agent=compliance_agent,
        context=[task_pricing],
    )

    task_evaluation = Task(
        description=(
            "Score and rank eligible supplier proposals using the 5-attribute weighted formula: "
            "Price (35%), Delivery (20%), Warranty (15%), Compliance (15%), Specifications (15%). "
            "Disqualify any non-compliant vendor before ranking."
        ),
        expected_output="Ranked evaluation table with scores between 0.0 and 100.0 and top-ranked vendor identification.",
        agent=deal_evaluation_agent,
        context=[task_compliance],
    )

    task_budget = Task(
        description=(
            "Using FastMCP tool 'validate_budget_mcp', audit the top-ranked vendor quotation against "
            "the approved department budget ceiling. Calculate exact budget surplus or deficit."
        ),
        expected_output="Budget audit result indicating pass/fail status, difference, and overrun amount.",
        agent=budget_validation_agent,
        context=[task_evaluation],
    )

    task_negotiation = Task(
        description=(
            "Synthesize a strategic data-backed counter-offer proposal for the top-ranked vendor. "
            "Calculate projected cost savings and draft a professional negotiation justification letter."
        ),
        expected_output="Formal negotiation proposal with target price, counter-offer amount, and letter draft.",
        agent=negotiation_agent,
        context=[task_budget],
    )

    task_coordination = Task(
        description=(
            "Finalize procurement governance: dispatch A2A risk assessment request to Google ADK service, "
            "evaluate human-in-the-loop approval thresholds, and issue Purchase Order via 'create_purchase_order_mcp' if authorized."
        ),
        expected_output="Final coordination report with A2A risk findings and approval/PO action status.",
        agent=approval_coordination_agent,
        context=[task_negotiation],
    )

    # -------------------------------------------------------------------------
    # 3. Callbacks & Crew Assembly
    # -------------------------------------------------------------------------

    def on_task_finish(task_output):
        logger.info(f"[CrewAI Callback] Task finished: {str(task_output)[:120]}")
        if workflow_id and request_id:
            workflow_monitor.on_step_complete(
                workflow_id=workflow_id,
                request_id=request_id,
                agent_name="CrewAI Task Pipeline",
                step_name="CREW_TASK_FINISH",
                final_summary=str(task_output)[:150]
            )

    crew = Crew(
        agents=[
            requirement_agent,
            vendor_research_agent,
            price_analysis_agent,
            compliance_agent,
            deal_evaluation_agent,
            budget_validation_agent,
            negotiation_agent,
            approval_coordination_agent,
        ],
        tasks=[
            task_requirements,
            task_discovery,
            task_pricing,
            task_compliance,
            task_evaluation,
            task_budget,
            task_negotiation,
            task_coordination,
        ],
        process=Process.sequential,
        verbose=False,
        task_callback=on_task_finish,
    )

    return crew
