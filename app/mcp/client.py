import asyncio
from typing import Dict, Any, List, Optional
from app.mcp.server import mcp
from app.core.logging import logger


class MCPProcurementClient:
    """
    Standard Model Context Protocol (MCP) Client Adapter.
    Connects ADK agents, CrewAI crews, and backend services to the DealForge MCP Server.
    Invokes validated MCP tools with structured serialization and error handling.
    """

    def __init__(self):
        self.server = mcp

    async def call_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        logger.info(f"Invoking MCP tool '{tool_name}' with arguments: {list(arguments.keys())}")
        try:
            result = await self.server.call_tool(tool_name, arguments)
            # FastMCP call_tool returns a tuple (contents, raw_dict/data)
            if isinstance(result, tuple) and len(result) >= 2:
                payload = result[1]
                if isinstance(payload, dict) and "result" in payload:
                    return payload["result"]
                return payload
            elif isinstance(result, tuple) and len(result) == 1:
                return result[0]
            return result
        except Exception as e:
            logger.error(f"Error executing MCP tool '{tool_name}': {e}")
            raise RuntimeError(f"MCP tool '{tool_name}' failed: {e}")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Synchronous wrapper for agent and service contexts."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running inside an existing loop (e.g. FastAPI / AnyIO)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, self.call_tool_async(tool_name, arguments)).result()
            else:
                return loop.run_until_complete(self.call_tool_async(tool_name, arguments))
        except RuntimeError:
            return asyncio.run(self.call_tool_async(tool_name, arguments))

    # --- Typed Helper Methods ---
    def search_vendors(self, category: str, specifications: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.call_tool("search_vendors", {"product_category": category, "specifications": specifications})

    def get_vendor_details(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        return self.call_tool("get_vendor_details", {"vendor_id": vendor_id})

    def calculate_quote_total(
        self,
        unit_price: float,
        quantity: int,
        discount_rules: Optional[Dict[str, Any]] = None,
        budget_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        return self.call_tool(
            "calculate_quote_total",
            {"unit_price": unit_price, "quantity": quantity, "discount_rules": discount_rules, "budget_limit": budget_limit}
        )

    def validate_budget(self, total_cost: float, budget_limit: float) -> Dict[str, Any]:
        return self.call_tool("validate_budget", {"total_cost": total_cost, "budget_limit": budget_limit})

    def check_compliance(self, vendor_id: str, request_id: str) -> Dict[str, Any]:
        return self.call_tool("get_compliance_status", {"vendor_id": vendor_id, "request_id": request_id})

    def get_procurement_policies(self) -> List[Dict[str, Any]]:
        return self.call_tool("get_procurement_policies", {})

    def save_negotiation(
        self,
        request_id: str,
        quote_id: str,
        original_amount: float,
        target_amount: float,
        counter_offer_amount: float,
        justification: str,
        draft_message: str
    ) -> Dict[str, Any]:
        return self.call_tool("save_negotiation_proposal", {
            "request_id": request_id,
            "quote_id": quote_id,
            "original_amount": original_amount,
            "target_amount": target_amount,
            "counter_offer_amount": counter_offer_amount,
            "justification": justification,
            "draft_message": draft_message
        })

    def create_purchase_order(
        self,
        request_id: str,
        vendor_id: str,
        quote_id: str,
        approved_total: float,
        approved_by: str
    ) -> Dict[str, Any]:
        return self.call_tool("create_purchase_order", {
            "request_id": request_id,
            "vendor_id": vendor_id,
            "quote_id": quote_id,
            "approved_total": approved_total,
            "approved_by": approved_by
        })


mcp_client = MCPProcurementClient()
