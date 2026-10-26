import datetime
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class A2ATaskStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    WORKING = "WORKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentCapability(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    returns_schema: Dict[str, Any] = Field(default_factory=dict)


class AgentCard(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    protocol: str = "A2A/1.0"
    service_id: str
    endpoint_base: str
    capabilities: List[AgentCapability]
    supported_actions: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class A2ATaskSubmission(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    sender_agent: str
    target_service: str
    action: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class A2ATaskResponse(BaseModel):
    task_id: str
    request_id: str
    service_id: str
    status: A2ATaskStatus
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
