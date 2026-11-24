import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.a2a.schemas import A2AMessageEnvelope, RiskAssessmentPayload, RiskAssessmentResponsePayload
from app.adk_service.agent import adk_risk_agent


class A2AClient:
    """
    A2A (Agent-to-Agent) Protocol Client.
    Connects CrewAI procurement coordination agents with the independent Google ADK Risk Service.
    Enforces correlation IDs, strict timeouts, and fail-safe review states.
    """

    def __init__(self, endpoint_url: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.endpoint_url = endpoint_url or f"{settings.adk_service_url}/a2a/v1/message"
        self.timeout_seconds = timeout_seconds or settings.ADK_TIMEOUT_SECONDS

    def request_risk_assessment(
        self,
        payload: RiskAssessmentPayload,
        sender_agent: str = "CrewAI:ApprovalCoordinator"
    ) -> RiskAssessmentResponsePayload:
        envelope = A2AMessageEnvelope(
            sender_agent=sender_agent,
            target_agent="GoogleADK:ProcurementRiskAgent",
            message_type="RISK_ASSESSMENT_REQUEST",
            payload=payload.model_dump(),
        )

        # Candidate URLs to attempt over HTTP:
        # 1. Configured standalone ADK URL (typically port 8001 or cloud internal service)
        # 2. Mounted FastAPI ADK endpoint on main port (typically port 8000 under /adk-service)
        candidate_urls = [self.endpoint_url]
        mounted_url = f"http://127.0.0.1:{settings.PORT}/adk-service/a2a/v1/message"
        if mounted_url not in candidate_urls:
            candidate_urls.append(mounted_url)

        last_error = None
        for target_url in candidate_urls:
            try:
                logger.info(f"Dispatching A2A request [{envelope.request_id}] to Google ADK Service at {target_url}...")
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    resp = client.post(target_url, json=envelope.model_dump(mode="json"))

                    if resp.status_code == 200:
                        resp_envelope = A2AMessageEnvelope.model_validate(resp.json())
                        if resp_envelope.status == "SUCCESS":
                            logger.info(f"Received valid A2A response [{resp_envelope.request_id}] from Google ADK via {target_url}")
                            return RiskAssessmentResponsePayload.model_validate(resp_envelope.payload)
                        else:
                            raise RuntimeError(f"A2A error from ADK service: {resp_envelope.error_message}")
                    else:
                        raise RuntimeError(f"HTTP {resp.status_code} from ADK service: {resp.text}")
            except Exception as e:
                last_error = e
                logger.warning(f"A2A HTTP dispatch to {target_url} unavailable ({e}). Checking alternate routes...")

        logger.warning(
            f"All A2A HTTP endpoints unavailable ({last_error}). "
            f"Falling back to local in-process Google ADK Agent instance for high availability."
        )
        # In-process direct execution fallback to preserve end-to-end functionality
        try:
            assessment = adk_risk_agent.evaluate_risk(payload)
            return assessment
        except Exception as inner_e:
            logger.error(f"Complete ADK failure: {inner_e}. Transitioning to mandatory human review.")
            # Non-bypassable safety state
            return RiskAssessmentResponsePayload(
                risk_category="HIGH",
                risk_score=95.0,
                risk_factors=["ADK_A2A_COMMUNICATION_FAILURE"],
                explanation=f"A2A communication error with Google ADK service: {last_error}. Strict policy requires manual review.",
                recommended_action="REVIEW",
                human_review_required=True,
                assessed_by="DealForge Fail-Safe System"
            )
