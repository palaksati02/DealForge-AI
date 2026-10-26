from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.adk_service.orchestrator import ADKProcurementOrchestrator
from app.schemas.schemas import PurchaseRequestExtract


class ProcurementWorkflowEngine(ADKProcurementOrchestrator):
    """
    Primary Procurement Multi-Agent Orchestration Layer powered by Google Agent Development Kit (ADK).
    Coordinates Google ADK primary agents, MCP tool execution, deterministic business services,
    A2A delegation to CrewAI Procurement Analysis Crew, and human-in-the-loop approval gating.
    """

    def __init__(self, db: Session):
        super().__init__(db=db)

    def run_requirement_agent(self, raw_text: str, overrides: Optional[Dict[str, Any]] = None) -> PurchaseRequestExtract:
        """Alias for backward compatibility."""
        return self.run_requirement_analysis(raw_text=raw_text, overrides=overrides)
