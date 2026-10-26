import sys
import os
import time

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from app.db.base import Base
from app.db.session import engine, SessionLocal, check_db_connection
from app.db.seed import seed_database
from app.db.repositories.procurement_repo import ProcurementRepository
from app.agents.procurement_crew import ProcurementWorkflowEngine


def run_demo():
    print("=" * 70)
    print(">> DEALFORGE AI: MULTI-AGENT PROCUREMENT DEMONSTRATION")
    print("=" * 70)

    # Ensure tables exist
    try:
        Base.metadata.create_all(bind=engine)
        seed_database()
    except Exception as e:
        print(f"Warning on DB init: {e}")

    db = SessionLocal()
    try:
        repo = ProcurementRepository(db)
        engine_runner = ProcurementWorkflowEngine(db)

        prompt = (
            "Purchase 50 laptops with at least 16 GB RAM and 512 GB SSD, "
            "a maximum budget of Rs.35,00,000, delivery within 14 days, and a minimum two-year warranty."
        )

        print(f"\n[USER INPUT]:\n\"{prompt}\"")
        print("\n[STEP 1]: Creating Purchase Request...")
        req = repo.create_purchase_request(
            requester="Academic Project Evaluator",
            raw_request_text=prompt,
            product_requirements={"category": "Laptops"},
            quantity=50,
            budget_limit=Decimal("3500000.00"),
            delivery_deadline_days=14,
            warranty_requirement_months=24,
        )
        print(f"  -> Created Request ID: {req.request_id}")

        print("\n[STEP 2]: Executing 8-Agent CrewAI Workflow with MCP Tools...")
        result = engine_runner.execute_workflow(req.request_id)

        print(f"  -> Workflow Status: {result['status']}")
        print(f"  -> Current Step: {result['current_step']}")

        if result.get("requires_approval"):
            print("\n[STEP 3]: Human-in-the-Loop Approval Gate Triggered!")
            print(f"  -> Trigger Reason: {result['approval_reason']}")
            print(f"  -> Google ADK Risk Category: {result['risk_assessment']['risk_category']}")
            print(f"  -> Winning Vendor: {result['top_deal']['vendor_name']}")
            print(f"  -> Total Amount: Rs. {result['top_deal']['total_amount']:,.2f}")

            print("\n[STEP 4]: Simulating Human Manager Approval...")
            time.sleep(1)
            approval_res = engine_runner.resume_workflow(
                approval_id=result["approval_id"],
                decision="APPROVED",
                decided_by="Chief Procurement Officer",
                comments="Approved following successful multi-agent review and Google ADK risk assessment."
            )

            print(f"  -> Approval Decision: {approval_res['decision']}")
            print(f"  -> Issued Formal Purchase Order Number: {approval_res['order_number']}")

        print("\n" + "=" * 70)
        print(">> DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
