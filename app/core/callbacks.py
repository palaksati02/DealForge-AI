import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from app.core.logging import logger


class TaskExecutionEvent:
    """Represents an atomic monitored agent or tool step event."""
    def __init__(
        self,
        event_type: str,
        agent_name: str,
        step_name: str,
        workflow_id: str,
        request_id: str,
        status: str = "PENDING",
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ):
        self.timestamp = datetime.utcnow().isoformat()
        self.event_type = event_type
        self.agent_name = agent_name
        self.step_name = step_name
        self.workflow_id = workflow_id
        self.request_id = request_id
        self.status = status
        self.data = data or {}
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "step_name": self.step_name,
            "workflow_id": self.workflow_id,
            "request_id": self.request_id,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


class MonitoringCallbackHandler:
    """
    Enterprise callback function handler for task monitoring,
    intermediate output capture, execution flow tracking, and error telemetry.
    """

    def __init__(self):
        self.events: List[TaskExecutionEvent] = []
        self._start_times: Dict[str, float] = {}
        self._listeners: List[Callable[[TaskExecutionEvent], None]] = []

    def register_listener(self, listener: Callable[[TaskExecutionEvent], None]):
        """Register a callback observer (e.g. database recorder, websocket streamer, or Langfuse exporter)."""
        self._listeners.append(listener)

    def on_step_start(self, workflow_id: str, request_id: str, agent_name: str, step_name: str, input_summary: str = ""):
        """Callback triggered when an agent begins a sub-task."""
        key = f"{workflow_id}:{agent_name}:{step_name}"
        self._start_times[key] = time.perf_counter()

        event = TaskExecutionEvent(
            event_type="STEP_START",
            agent_name=agent_name,
            step_name=step_name,
            workflow_id=workflow_id,
            request_id=request_id,
            status="RUNNING",
            data={"input_summary": input_summary}
        )
        self.events.append(event)
        logger.info(f"[Callback: Start] {agent_name} -> {step_name} | {input_summary}")
        self._notify(event)

    def on_intermediate_output(
        self,
        workflow_id: str,
        request_id: str,
        agent_name: str,
        step_name: str,
        output_data: Dict[str, Any],
        summary: str = ""
    ):
        """Callback capturing intermediate outputs for cross-agent state feeding and provenance."""
        key = f"{workflow_id}:{agent_name}:{step_name}"
        start_time = self._start_times.get(key, time.perf_counter())
        duration = (time.perf_counter() - start_time) * 1000.0

        event = TaskExecutionEvent(
            event_type="INTERMEDIATE_OUTPUT",
            agent_name=agent_name,
            step_name=step_name,
            workflow_id=workflow_id,
            request_id=request_id,
            status="SUCCESS",
            data={"summary": summary, "output": output_data},
            duration_ms=duration
        )
        self.events.append(event)
        logger.info(f"[Callback: Output] {agent_name} -> {step_name} ({duration:.1f}ms) | {summary}")
        self._notify(event)

    def on_step_complete(
        self,
        workflow_id: str,
        request_id: str,
        agent_name: str,
        step_name: str,
        final_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Callback triggered upon successful agent task termination."""
        key = f"{workflow_id}:{agent_name}:{step_name}"
        start_time = self._start_times.pop(key, time.perf_counter())
        duration = (time.perf_counter() - start_time) * 1000.0

        event = TaskExecutionEvent(
            event_type="STEP_COMPLETE",
            agent_name=agent_name,
            step_name=step_name,
            workflow_id=workflow_id,
            request_id=request_id,
            status="COMPLETED",
            data={"summary": final_summary, "metadata": metadata or {}},
            duration_ms=duration
        )
        self.events.append(event)
        logger.info(f"[Callback: Complete] {agent_name} -> {step_name} completed in {duration:.1f}ms")
        self._notify(event)

    def on_error(
        self,
        workflow_id: str,
        request_id: str,
        agent_name: str,
        step_name: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Callback tracking execution errors for transparency, fail-safe routing, and debugging."""
        key = f"{workflow_id}:{agent_name}:{step_name}"
        start_time = self._start_times.pop(key, time.perf_counter())
        duration = (time.perf_counter() - start_time) * 1000.0

        event = TaskExecutionEvent(
            event_type="STEP_ERROR",
            agent_name=agent_name,
            step_name=step_name,
            workflow_id=workflow_id,
            request_id=request_id,
            status="ERROR",
            error=error_message,
            data=context or {},
            duration_ms=duration
        )
        self.events.append(event)
        logger.error(f"[Callback: Error] {agent_name} -> {step_name} FAILED: {error_message}")
        self._notify(event)

    def _notify(self, event: TaskExecutionEvent):
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.warning(f"Callback listener execution exception: {e}")

    def get_events(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if workflow_id:
            return [e.to_dict() for e in self.events if e.workflow_id == workflow_id]
        return [e.to_dict() for e in self.events]


# Singleton global monitoring callback instance
workflow_monitor = MonitoringCallbackHandler()
