import datetime
from typing import Dict, Any, Optional
from app.a2a.models import AgentCard, AgentCapability, A2ATaskStatus, A2ATaskResponse
from app.agents.crew import procurement_analysis_crew
from app.core.logging import logger


class ProcurementAnalysisA2AService:
    SERVICE_ID = "procurement-analysis"
    ENDPOINT_BASE = "/a2a/procurement-analysis"

    def __init__(self):
        self.tasks: Dict[str, A2ATaskResponse] = {}

    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="DealForge Procurement Analysis Service",
            description="Specialized A2A procurement analysis service housing the 4-agent CrewAI procurement analysis crew.",
            version="1.0.0",
            protocol="A2A/1.0",
            service_id=self.SERVICE_ID,
            endpoint_base=self.ENDPOINT_BASE,
            capabilities=[
                AgentCapability(
                    name="ANALYZE_PROPOSALS",
                    description="Execute CrewAI specialized analysis across price breakdowns, compliance audits, trade-off explanations, and negotiation strategy.",
                ),
            ],
            supported_actions=["ANALYZE_PROPOSALS"],
        )

    def execute_task(
        self,
        task_id: str,
        request_id: str,
        action: str,
        input_data: Dict[str, Any]
    ) -> A2ATaskResponse:
        logger.info(f"ProcurementAnalysisA2AService executing task [{task_id}] (Action: {action}, Req: {request_id})")
        started_at = datetime.datetime.now(datetime.timezone.utc)

        try:
            if action == "ANALYZE_PROPOSALS":
                quotes = input_data.get("quotes", [])
                request_data = input_data.get("request_data", {})
                compliance_results = input_data.get("compliance_results", {})
                evaluations = input_data.get("evaluations", [])
                negotiation_bounds = input_data.get("negotiation_bounds", {})

                # Execute specialized CrewAI crew
                analysis_result = procurement_analysis_crew.analyze(
                    quotes=quotes,
                    request_data=request_data,
                    compliance_results=compliance_results,
                    evaluations=evaluations,
                    negotiation_bounds=negotiation_bounds
                )

                completed_at = datetime.datetime.now(datetime.timezone.utc)
                response = A2ATaskResponse(
                    task_id=task_id,
                    request_id=request_id,
                    service_id=self.SERVICE_ID,
                    status=A2ATaskStatus.COMPLETED,
                    output_data=analysis_result,
                    started_at=started_at,
                    completed_at=completed_at
                )
                self.tasks[task_id] = response
                return response
            else:
                raise ValueError(f"Unsupported action '{action}' for ProcurementAnalysisA2AService")

        except Exception as e:
            logger.error(f"ProcurementAnalysisA2AService task [{task_id}] failed: {e}")
            completed_at = datetime.datetime.now(datetime.timezone.utc)
            response = A2ATaskResponse(
                task_id=task_id,
                request_id=request_id,
                service_id=self.SERVICE_ID,
                status=A2ATaskStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=completed_at
            )
            self.tasks[task_id] = response
            return response

    def get_task_status(self, task_id: str) -> Optional[A2ATaskResponse]:
        return self.tasks.get(task_id)


procurement_analysis_service = ProcurementAnalysisA2AService()
