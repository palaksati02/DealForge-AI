import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.models.entities import (
    PurchaseRequest,
    VendorQuote,
    Evaluation,
    Negotiation,
    Approval,
    PurchaseOrder,
    AgentLog,
    WorkflowState,
    ProcurementAuditLog,
)
from app.db.repositories.procurement_repo import ProcurementRepository


class ReportService:
    @staticmethod
    def generate_procurement_report(db: Session, request_id: str) -> Dict[str, Any]:
        """Compile a fully auditable end-to-end procurement report from MySQL."""
        repo = ProcurementRepository(db)
        req = repo.get_purchase_request(request_id)
        if not req:
            raise ValueError(f"Purchase request '{request_id}' not found.")

        quotes = repo.get_quotes_by_request(request_id)
        evaluations = repo.get_evaluations_by_request(request_id)
        negotiations = repo.get_negotiations_by_request(request_id)
        po = repo.get_purchase_order_by_request(request_id)
        wf_state = repo.get_workflow_state_by_request(request_id)
        workflow_id = wf_state.workflow_id if wf_state else None
        agent_logs = repo.get_workflow_logs(workflow_id) if workflow_id else []
        audit_logs = repo.get_audit_logs(request_id)

        # Get approval records
        approvals = list(
            db.scalars(
                select(Approval).where(Approval.request_id == request_id).order_by(desc(Approval.created_at))
            ).all()
        )

        # Compile Vendor Matrix
        vendor_matrix = []
        for q in quotes:
            matching_eval = next((e for e in evaluations if e.quote_id == q.quote_id), None)
            vendor_matrix.append({
                "quote_id": q.quote_id,
                "vendor_id": q.vendor_id,
                "vendor_name": q.vendor.vendor_name if q.vendor else "Unknown",
                "unit_price": float(q.unit_price),
                "quantity": q.quantity,
                "discount": float(q.discount),
                "shipping_cost": float(q.shipping_cost),
                "total_amount": float(q.total_amount),
                "delivery_days": q.delivery_days,
                "warranty_months": q.warranty_months,
                "vendor_rating": float(q.vendor.vendor_rating) if q.vendor else 0.0,
                "eligibility_status": matching_eval.eligibility_status if matching_eval else "UNKNOWN",
                "exclusion_reason": matching_eval.exclusion_reason if matching_eval else None,
                "final_score": float(matching_eval.final_score) if matching_eval else 0.0,
                "rank": matching_eval.rank if matching_eval else None,
            })
        vendor_matrix.sort(key=lambda x: (x["rank"] is None, x["rank"] or 999))

        # Compile Negotiation Summary
        neg_summary = []
        for n in negotiations:
            neg_summary.append({
                "negotiation_id": n.negotiation_id,
                "original_amount": float(n.original_amount),
                "target_amount": float(n.target_amount),
                "counter_offer_amount": float(n.counter_offer_amount),
                "savings": float(n.original_amount - n.counter_offer_amount),
                "justification": n.justification,
                "status": n.negotiation_status,
                "vendor_response": n.vendor_response,
            })

        # Compile Governance & Approvals
        appr_summary = []
        for a in approvals:
            appr_summary.append({
                "approval_id": a.approval_id,
                "reason": a.approval_reason,
                "decision": a.decision,
                "decided_by": a.decided_by,
                "approver_role": a.approver_role,
                "comments": a.comments,
                "risk_assessment": a.risk_assessment,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "decided_at": a.decided_at.isoformat() if a.decided_at else None,
            })

        # Compile Final Decision
        final_decision = None
        if po:
            final_decision = {
                "awarded_vendor_id": po.vendor_id,
                "awarded_vendor_name": po.vendor.vendor_name if po.vendor else "Unknown",
                "order_number": po.order_number,
                "approved_total": float(po.approved_total),
                "currency": po.currency,
                "approved_by": po.approved_by,
                "status": po.status,
                "created_at": po.created_at.isoformat() if po.created_at else None,
            }

        # Build Markdown Document
        md_lines = [
            f"# DEALFORGE AI — EXECUTIVE PROCUREMENT REPORT",
            f"**Report Generated:** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Request ID:** `{req.request_id}`",
            f"**Workflow ID:** `{workflow_id or 'N/A'}`",
            f"**Status:** `{req.status}`",
            "",
            "---",
            "## 1. Purchase Request Details",
            f"- **Requester:** {req.requester}",
            f"- **Description:** {req.raw_request_text}",
            f"- **Quantity Required:** {req.quantity}",
            f"- **Budget Ceiling:** ₹{float(req.budget_limit):,.2f}",
            f"- **Delivery Deadline:** <= {req.delivery_deadline_days} days",
            f"- **Minimum Warranty:** >= {req.warranty_requirement_months} months",
            "",
            "## 2. Multi-Vendor Evaluation & Ranking",
            "| Rank | Vendor | Total Quote | Score | Status | Notes |",
            "|---|---|---|---|---|---|",
        ]

        for vm in vendor_matrix:
            rank_str = f"#{vm['rank']}" if vm['rank'] else "—"
            md_lines.append(
                f"| {rank_str} | {vm['vendor_name']} | ₹{vm['total_amount']:,.2f} | {vm['final_score']:.1f}/100 | {vm['eligibility_status']} | {vm['exclusion_reason'] or 'Qualified'} |"
            )

        md_lines.extend([
            "",
            "## 3. Negotiation Strategy & Commercial Terms",
        ])
        if neg_summary:
            for ns in neg_summary:
                md_lines.extend([
                    f"- **Original Quote:** ₹{ns['original_amount']:,.2f}",
                    f"- **Target Target Price:** ₹{ns['target_amount']:,.2f}",
                    f"- **Counter Offer Submitted:** ₹{ns['counter_offer_amount']:,.2f}",
                    f"- **Projected Savings:** ₹{ns['savings']:,.2f} (Status: {ns['status']})",
                    f"- **Commercial Rationale:** {ns['justification']}",
                ])
        else:
            md_lines.append("No active price negotiations conducted.")

        md_lines.extend([
            "",
            "## 4. Governance, Risk & Approvals",
        ])
        if appr_summary:
            for aps in appr_summary:
                md_lines.extend([
                    f"- **Decision:** `{aps['decision']}` by **{aps['decided_by'] or 'Pending'}** ({aps['approver_role'] or 'N/A'})",
                    f"- **Approval Trigger:** {aps['reason']}",
                    f"- **Comments:** {aps['comments'] or 'None'}",
                ])
        else:
            md_lines.append("Auto-approved under standard delegation of authority.")

        md_lines.extend([
            "",
            "## 5. Award & Purchase Commitment",
        ])
        if final_decision:
            md_lines.extend([
                f"- **Awarded Vendor:** **{final_decision['awarded_vendor_name']}**",
                f"- **Purchase Order Number:** `{final_decision['order_number']}`",
                f"- **Total Committed Value:** ₹{final_decision['approved_total']:,.2f} {final_decision['currency']}",
                f"- **Authorized By:** {final_decision['approved_by']}",
                f"- **Order Status:** `{final_decision['status']}`",
            ])
        else:
            md_lines.append(f"No Purchase Order issued yet. Current state: {req.status}")

        md_lines.extend([
            "",
            "## 6. Multi-Agent Audit Trail",
            f"Total agent actions logged: {len(agent_logs)}",
            "",
            "| Timestamp (UTC) | Agent Service | Event Type | Status | Summary |",
            "|---|---|---|---|---|",
        ])
        for al in agent_logs:
            time_str = al.started_at.strftime('%H:%M:%S') if al.started_at else ""
            summary_clean = (al.output_summary or al.input_summary or al.event_type or "").replace("|", "-")[:80]
            md_lines.append(f"| {time_str} | {al.agent_name} | {al.event_type} | {al.status} | {summary_clean} |")

        return {
            "request_id": req.request_id,
            "workflow_id": workflow_id,
            "status": req.status,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "request_details": {
                "requester": req.requester,
                "raw_request_text": req.raw_request_text,
                "product_requirements": req.product_requirements,
                "quantity": req.quantity,
                "budget_limit": float(req.budget_limit),
                "currency": req.currency,
                "delivery_deadline_days": req.delivery_deadline_days,
                "warranty_requirement_months": req.warranty_requirement_months,
                "created_at": req.created_at.isoformat() if req.created_at else None,
            },
            "vendor_matrix": vendor_matrix,
            "negotiations": neg_summary,
            "approvals": appr_summary,
            "purchase_order": final_decision,
            "agent_execution_logs": [
                {
                    "log_id": l.log_id,
                    "agent_name": l.agent_name,
                    "event_type": l.event_type,
                    "status": l.status,
                    "started_at": l.started_at.isoformat() if l.started_at else None,
                    "completed_at": l.completed_at.isoformat() if l.completed_at else None,
                    "output_summary": l.output_summary,
                }
                for l in agent_logs
            ],
            "audit_trail": [
                {
                    "audit_id": a.audit_id,
                    "action": a.action,
                    "actor": a.actor,
                    "actor_role": a.actor_role,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                    "details": a.details,
                }
                for a in audit_logs
            ],
            "markdown_report": "\n".join(md_lines)
        }
