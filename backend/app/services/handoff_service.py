"""Creates traceable AI-to-human support handoffs with delivery outcomes."""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.config import settings
from app.models.schemas import Ticket, TicketStatus
from app.services.notification_service import send_handoff_email
from app.services.webhook_service import deliver_webhook

_handoffs: Dict[str, Dict[str, Any]] = {}


def _priority_for(ticket: Ticket) -> str:
    if ticket.case_file and ticket.case_file.get("priority"):
        return str(ticket.case_file["priority"]).upper()
    if ticket.risk_score >= 0.8:
        return "CRITICAL"
    if ticket.risk_score >= 0.6:
        return "HIGH"
    if ticket.confidence_score < 0.75:
        return "MEDIUM"
    return "LOW"


def build_context_packet(ticket: Ticket, reason: str, queue: str, priority: Optional[str] = None) -> Dict[str, Any]:
    """Build a concise packet that lets a human continue without re-triage."""
    return {
        "event": "support.handoff.created",
        "handoff_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "ticket_id": ticket.id,
        "queue": queue,
        "priority": priority or _priority_for(ticket),
        "reason": reason,
        "customer": ticket.customer.model_dump(mode="json"),
        "ticket": {
            "subject": ticket.subject,
            "message": ticket.message,
            "category": ticket.category.value if ticket.category else "general",
            "channel": ticket.channel.value,
            "created_at": ticket.created_at.isoformat(),
        },
        "ai_context": {
            "confidence": ticket.confidence_score,
            "risk_score": ticket.risk_score,
            "recommendation": ticket.resolution_decision.value if ticket.resolution_decision else None,
            "customer_message": ticket.resolution_message,
            "fraud_analysis": ticket.fraud_analysis.model_dump(mode="json") if ticket.fraud_analysis else None,
            "policy_context": ticket.retrieved_context,
            "case_file": ticket.case_file,
            "evidence": [
                {"id": item.id, "filename": item.filename, "file_type": item.file_type, "size_bytes": item.size_bytes}
                for item in ticket.evidence_files
            ],
            "agent_steps": [step.model_dump(mode="json") for step in ticket.agent_steps],
        },
    }


def _email_body(packet: Dict[str, Any]) -> str:
    customer = packet["customer"]
    ticket = packet["ticket"]
    context = packet["ai_context"]
    return "\n".join([
        "ArgusCX human-support handoff",
        f"Handoff: {packet['handoff_id']}",
        f"Priority: {packet['priority']}",
        f"Queue: {packet['queue']}",
        f"Reason: {packet['reason']}",
        "",
        f"Customer: {customer['name']} ({customer.get('email') or 'no email supplied'})",
        f"Ticket: {packet['ticket_id']} — {ticket['subject']}",
        f"Channel: {ticket['channel']}; category: {ticket['category']}",
        f"AI confidence: {context['confidence']:.2f}; risk: {context['risk_score']:.2f}",
        f"Recommendation: {context['recommendation'] or 'human review required'}",
        "",
        "The full signed context packet is available in ArgusCX and, when configured, your support webhook.",
    ])


async def create_handoff(
    ticket: Ticket,
    reason: str,
    queue: str = "support",
    priority: Optional[str] = None,
    requested_by: str = "arguscx",
) -> Dict[str, Any]:
    """Persist a handoff record and deliver it to configured human channels."""
    existing = ticket.metadata.get("human_handoff") if ticket.metadata else None
    if existing and existing.get("status") == "open":
        return existing

    packet = build_context_packet(ticket, reason=reason, queue=queue, priority=priority)
    email_status = await send_handoff_email(
        subject=f"[{packet['priority']}] ArgusCX handoff: {ticket.subject}",
        body=_email_body(packet),
    )
    webhook_status = "not_configured"
    if settings.human_handoff_webhook_configured:
        delivered = await deliver_webhook(
            settings.HUMAN_HANDOFF_WEBHOOK_URL,
            settings.HUMAN_HANDOFF_WEBHOOK_SECRET.get_secret_value(),
            packet["event"],
            packet,
        )
        webhook_status = "sent" if delivered else "failed"

    record = {
        "handoff_id": packet["handoff_id"],
        "ticket_id": ticket.id,
        "status": "open",
        "requested_by": requested_by,
        "queue": packet["queue"],
        "priority": packet["priority"],
        "reason": packet["reason"],
        "created_at": packet["created_at"],
        "deliveries": {"email": email_status, "webhook": webhook_status},
        "context_packet": packet,
    }
    _handoffs[ticket.id] = record
    ticket.metadata["human_handoff"] = {key: value for key, value in record.items() if key != "context_packet"}
    ticket.status = TicketStatus.HUMAN_REVIEW
    return record


def get_handoff(ticket_id: str) -> Optional[Dict[str, Any]]:
    return _handoffs.get(ticket_id)
