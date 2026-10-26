import datetime
import uuid
from typing import Dict, Any, Optional
from app.a2a.models import AgentCard, AgentCapability, A2ATaskStatus, A2ATaskResponse
from app.mcp.client import mcp_client
from app.core.logging import logger


class VendorResearchA2AService:
    SERVICE_ID = "vendor-research"
    ENDPOINT_BASE = "/a2a/vendor-research"

    def __init__(self):
        self.tasks: Dict[str, A2ATaskResponse] = {}

    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="DealForge Vendor Research Service",
            description="Autonomous A2A agent service for supplier catalog discovery, profile retrieval, and stock checking.",
            version="1.0.0",
            protocol="A2A/1.0",
            service_id=self.SERVICE_ID,
            endpoint_base=self.ENDPOINT_BASE,
            capabilities=[
                AgentCapability(
                    name="DISCOVER_VENDORS",
                    description="Search active suppliers and products matching category and technical specifications via MCP.",
                ),
                AgentCapability(
                    name="CHECK_STOCK_DELIVERY",
                    description="Verify live stock inventory levels and lead times for a given vendor product.",
                ),
                AgentCapability(
                    name="GET_VENDOR_PROFILE",
                    description="Retrieve verified vendor profile, historical rating, and active certifications.",
                ),
            ],
            supported_actions=["DISCOVER_VENDORS", "CHECK_STOCK_DELIVERY", "GET_VENDOR_PROFILE"],
        )

    def execute_task(
        self,
        task_id: str,
        request_id: str,
        action: str,
        input_data: Dict[str, Any]
    ) -> A2ATaskResponse:
        logger.info(f"VendorResearchA2AService executing task [{task_id}] (Action: {action}, Req: {request_id})")
        started_at = datetime.datetime.now(datetime.timezone.utc)

        try:
            if action == "DISCOVER_VENDORS":
                category = input_data.get("category", "Laptops")
                specs = input_data.get("specifications", {})
                vendors = mcp_client.search_vendors(category=category, specifications=specs)
                output_data = {"vendors": vendors, "vendor_count": len(vendors), "category": category}

            elif action == "CHECK_STOCK_DELIVERY":
                vendor_id = input_data["vendor_id"]
                product_id = input_data["product_id"]
                required_qty = input_data.get("required_quantity", 1)
                res = mcp_client.call_tool("check_stock_delivery", {
                    "vendor_id": vendor_id,
                    "product_id": product_id,
                    "required_quantity": required_qty
                })
                output_data = res

            elif action == "GET_VENDOR_PROFILE":
                vendor_id = input_data["vendor_id"]
                profile = mcp_client.get_vendor_details(vendor_id)
                output_data = {"profile": profile}

            else:
                raise ValueError(f"Unsupported action '{action}' for VendorResearchA2AService")

            completed_at = datetime.datetime.now(datetime.timezone.utc)
            response = A2ATaskResponse(
                task_id=task_id,
                request_id=request_id,
                service_id=self.SERVICE_ID,
                status=A2ATaskStatus.COMPLETED,
                output_data=output_data,
                started_at=started_at,
                completed_at=completed_at
            )
            self.tasks[task_id] = response
            return response

        except Exception as e:
            logger.error(f"VendorResearchA2AService task [{task_id}] failed: {e}")
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


vendor_research_service = VendorResearchA2AService()
