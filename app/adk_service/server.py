import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.a2a.schemas import A2AMessageEnvelope, RiskAssessmentPayload, RiskAssessmentResponsePayload
from app.adk_service.agent import adk_risk_agent
from app.core.logging import logger
import uvicorn

adk_app = FastAPI(
    title="DealForge AI - Google ADK Risk Agent Service",
    description="Independent Risk & Policy Agent running on Google ADK and communicating via A2A protocol",
    version="1.0.0"
)

adk_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@adk_app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Google ADK Risk Assessment Agent",
        "protocol": "A2A/1.0",
        "agent_name": adk_risk_agent.adk_agent.name
    }


@adk_app.post("/a2a/v1/message", response_model=A2AMessageEnvelope)
def handle_a2a_message(envelope: A2AMessageEnvelope):
    logger.info(f"Received A2A message [{envelope.message_type}] from [{envelope.sender_agent}] (Req: {envelope.request_id})")

    if envelope.message_type == "RISK_ASSESSMENT_REQUEST":
        try:
            payload = RiskAssessmentPayload.model_validate(envelope.payload)
            assessment = adk_risk_agent.evaluate_risk(payload)

            return A2AMessageEnvelope(
                protocol_version="A2A/1.0",
                request_id=envelope.request_id,
                sender_agent="GoogleADK:ProcurementRiskAgent",
                target_agent=envelope.sender_agent,
                message_type="RISK_ASSESSMENT_RESPONSE",
                payload=assessment.model_dump(),
                status="SUCCESS"
            )
        except Exception as e:
            logger.error(f"Error evaluating risk in Google ADK service: {e}")
            return A2AMessageEnvelope(
                protocol_version="A2A/1.0",
                request_id=envelope.request_id,
                sender_agent="GoogleADK:ProcurementRiskAgent",
                target_agent=envelope.sender_agent,
                message_type="RISK_ASSESSMENT_RESPONSE",
                payload={},
                status="ERROR",
                error_message=str(e)
            )

    raise HTTPException(status_code=400, detail=f"Unsupported message type: {envelope.message_type}")


if __name__ == "__main__":
    from app.core.config import settings
    uvicorn.run("app.adk_service.server:adk_app", host=settings.ADK_SERVICE_HOST, port=settings.ADK_SERVICE_PORT, reload=False)
