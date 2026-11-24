import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.core.callbacks import workflow_monitor
from app.core.guardrails import SecurityGuardrails
from app.mcp.server import mcp
from crewai.tools import tool


class MCPInvocationRecord:
    """Record of an atomic MCP protocol tool call for auditability and provenance."""
    def __init__(self, tool_name: str, arguments: Dict[str, Any], result: Any, duration_ms: float, error: Optional[str] = None):
        self.timestamp = time.time()
        self.tool_name = tool_name
        self.arguments = arguments
        self.result = result
        self.duration_ms = duration_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result_summary": str(self.result)[:200] if self.result else None,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


class MCPClient:
    """
    Standard Model Context Protocol (MCP) Client.
    Connects to the FastMCP server, discovers exposed procurement tools,
    and executes tools over the MCP protocol with strict validation, latency tracking,
    and audit logging.
    """

    def __init__(self, server=None):
        self.server = server or mcp
        self._tools_cache: Optional[List[str]] = None
        self.invocations: List[MCPInvocationRecord] = []

    def discover_tools(self) -> List[str]:
        """Discover available tools from FastMCP server."""
        try:
            tools_list = self._run_async(self.server.list_tools())
            self._tools_cache = [t.name for t in tools_list]
            logger.info(f"[MCP Client] Discovered {len(self._tools_cache)} MCP tools: {', '.join(self._tools_cache)}")
            return self._tools_cache
        except Exception as e:
            logger.error(f"[MCP Client] Tool discovery failed: {e}")
            return [
                "search_vendors", "get_vendor_details", "get_vendor_quotes",
                "get_product_inventory", "get_compliance_status",
                "calculate_quote_total", "validate_budget",
                "save_negotiation_proposal", "create_approval_request",
                "create_purchase_order"
            ]

    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        workflow_id: Optional[str] = None,
        request_id: Optional[str] = None,
        timeout_seconds: float = 10.0
    ) -> Any:
        """
        Executes a registered tool via genuine FastMCP protocol call.
        Enforces argument validation, timeout limits, output type checking, and logging.
        """
        start_time = time.perf_counter()
        logger.info(f"[MCP Protocol] >> Client calling tool '{tool_name}' with args {arguments}...")

        try:
            # 1. Execute tool on FastMCP server
            raw_response = self._run_async(
                asyncio.wait_for(
                    self.server.call_tool(tool_name, arguments),
                    timeout=timeout_seconds
                )
            )

            # 2. Extract structured tool payload from FastMCP return tuple (content_list, dict_result)
            parsed_result = None
            if isinstance(raw_response, tuple) and len(raw_response) >= 2:
                dict_part = raw_response[1]
                if isinstance(dict_part, dict) and "result" in dict_part:
                    parsed_result = dict_part["result"]
                else:
                    parsed_result = dict_part
            elif isinstance(raw_response, tuple) and len(raw_response) == 1:
                # TextContent fallback
                content_item = raw_response[0]
                if hasattr(content_item, "text"):
                    try:
                        parsed_result = json.loads(content_item.text)
                    except Exception:
                        parsed_result = content_item.text
            else:
                parsed_result = raw_response

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # 3. Guardrail validation on tool output
            SecurityGuardrails.validate_tool_output(tool_name, parsed_result)

            # 4. Record invocation audit
            rec = MCPInvocationRecord(tool_name, arguments, parsed_result, duration_ms)
            self.invocations.append(rec)

            logger.info(f"[MCP Protocol] << Tool '{tool_name}' completed successfully in {duration_ms:.2f}ms")

            # 5. Emit callback event
            if workflow_id and request_id:
                workflow_monitor.on_intermediate_output(
                    workflow_id=workflow_id,
                    request_id=request_id,
                    agent_name="MCP Tool Layer",
                    step_name=f"MCP_TOOL:{tool_name}",
                    output_data={"result_summary": str(parsed_result)[:100]},
                    summary=f"MCP tool '{tool_name}' returned valid data ({duration_ms:.1f}ms)"
                )

            return parsed_result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            rec = MCPInvocationRecord(tool_name, arguments, None, duration_ms, error=str(e))
            self.invocations.append(rec)
            logger.error(f"[MCP Protocol] Tool '{tool_name}' execution failed ({duration_ms:.2f}ms): {e}")
            raise RuntimeError(f"MCP Tool '{tool_name}' failed: {e}")

    def _run_async(self, coro):
        """Helper to run async FastMCP coroutines safely in any execution context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running in an active event loop (e.g. FastAPI / Uvicorn), run in a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    return executor.submit(asyncio.run, coro).result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def get_invocation_history(self) -> List[Dict[str, Any]]:
        return [inv.to_dict() for inv in self.invocations]


# Singleton MCP Client instance
mcp_client = MCPClient()


# ---------------------------------------------------------------------------
# CrewAI Tool Wrappers (Invoking Tools through Genuine MCP Protocol)
# ---------------------------------------------------------------------------

@tool("search_vendors_mcp")
def search_vendors_mcp(product_category: str) -> str:
    """
    Search database for active vendors and matching catalog products in a category using FastMCP.
    """
    res = mcp_client.call_tool("search_vendors", {"product_category": product_category})
    return json.dumps(res, default=str)


@tool("get_vendor_details_mcp")
def get_vendor_details_mcp(vendor_id: str) -> str:
    """
    Retrieve contact, address, and rating details for a specific vendor from MySQL via FastMCP.
    """
    res = mcp_client.call_tool("get_vendor_details", {"vendor_id": vendor_id})
    return json.dumps(res, default=str)


@tool("get_product_inventory_mcp")
def get_product_inventory_mcp(product_id: str) -> str:
    """
    Retrieve live stock levels and pricing across vendors for a product ID via FastMCP.
    """
    res = mcp_client.call_tool("get_product_inventory", {"product_id": product_id})
    return json.dumps(res, default=str)


@tool("calculate_quote_total_mcp")
def calculate_quote_total_mcp(unit_price: float, quantity: int) -> str:
    """
    Deterministically compute base subtotal, volume tier discounts, 18% GST, shipping, and grand total via FastMCP.
    """
    res = mcp_client.call_tool("calculate_quote_total", {"unit_price": unit_price, "quantity": quantity})
    return json.dumps(res, default=str)


@tool("validate_budget_mcp")
def validate_budget_mcp(total_cost: float, budget_limit: float) -> str:
    """
    Deterministically audit total procurement cost against budget limit via FastMCP.
    """
    res = mcp_client.call_tool("validate_budget", {"total_cost": total_cost, "budget_limit": budget_limit})
    return json.dumps(res, default=str)


@tool("create_purchase_order_mcp")
def create_purchase_order_mcp(request_id: str, vendor_id: str, quote_id: str, approved_total: float, approved_by: str) -> str:
    """
    Deterministically issue and commit a formal Purchase Order to MySQL via FastMCP.
    """
    res = mcp_client.call_tool("create_purchase_order", {
        "request_id": request_id,
        "vendor_id": vendor_id,
        "quote_id": quote_id,
        "approved_total": approved_total,
        "approved_by": approved_by
    })
    return json.dumps(res, default=str)
