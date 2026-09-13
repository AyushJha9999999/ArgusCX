"""
ArgusCX — Escalation Agent
Packages full case file for human handoff and notifies via Slack.
"""
from datetime import datetime
from typing import Any, Dict
import structlog
from app.models.schemas import AgentState, AgentType, TicketStatus
from app.core.config import settings

logger = structlog.get_logger(__name__)


async def run_escalation_agent(state: AgentState) -> Dict[str, Any]:
    """
    Builds a comprehensive case file and routes to the right human team.
    Optionally sends Slack notification.
    """
    logger.info("🚨 Escalation agent packaging case", ticket_id=state.ticket.id)

    ticket = state.ticket
    fraud = state.fraud_analysis

    # Build full case file for human agent
    case_file = {
        "case_id": ticket.id,
        "generated_at": datetime.utcnow().isoformat(),
        "priority": _determine_priority(state),
        "summary": _build_summary(state),
        "customer_profile": {
            "id": ticket.customer.id,
            "name": ticket.customer.name,
            "email": ticket.customer.email,
            "channel": ticket.channel.value,
            "account_age_days": ticket.customer.account_age_days,
            "previous_tickets": ticket.customer.previous_tickets,
            "previous_fraud_flags": ticket.customer.previous_fraud_flags,
        },
        "ticket_details": {
            "subject": ticket.subject,
            "message": ticket.message,
            "category": ticket.category.value if ticket.category else "general",
            "created_at": ticket.created_at.isoformat(),
        },
        "investigation": {
            "order_data": state.order_data,
            "payment_data": state.payment_data,
            "user_history": state.user_history,
        },
        "evidence_analysis": fraud.model_dump() if fraud else None,
        "retrieved_context": {
            "policies": state.retrieved_policies,
            "faqs": state.retrieved_faqs,
            "similar_tickets": state.retrieved_past_tickets,
        },
        "agent_reasoning_chain": [
            {
                "agent": step.agent_type.value,
                "confidence": step.confidence,
                "duration_ms": step.duration_ms,
                "reasoning": step.reasoning,
                "status": step.status.value,
            }
            for step in ticket.agent_steps
        ],
        "scores": {
            "confidence": state.confidence_score,
            "risk": state.risk_score,
            "fraud": fraud.fraud_score if fraud else 0.0,
        },
        "escalation_reason": state.escalation_reason,
        "recommended_action": _recommend_action(state),
    }

    # Update ticket with case file
    state.ticket.case_file = case_file
    state.ticket.status = TicketStatus.ESCALATED

    # Send Slack notification (if configured)
    if settings.SLACK_WEBHOOK_URL and not settings.is_demo_mode:
        await _notify_slack(case_file)
    else:
        logger.info("📩 [DEMO] Slack notification would be sent", case_id=case_file["case_id"])

    return {
        "case_file": case_file,
        "assigned_team": _determine_team(state),
        "confidence": 1.0,
        "reasoning": (
            f"Case packaged for human review. "
            f"Priority: {case_file['priority']}. "
            f"Reason: {state.escalation_reason}. "
            f"Assigned to: {_determine_team(state)} team."
        ),
    }


def _build_summary(state: AgentState) -> str:
    fraud = state.fraud_analysis
    fraud_str = ""
    if fraud and fraud.is_suspicious:
        fraud_str = f" FRAUD RISK: {fraud.fraud_risk_level.value.upper()} (score: {fraud.fraud_score:.2f})."

    return (
        f"Customer {state.ticket.customer.name} submitted a {state.ticket.category.value if state.ticket.category else 'general'} ticket. "
        f"Confidence score: {state.confidence_score:.2f}. Risk score: {state.risk_score:.2f}.{fraud_str} "
        f"Escalation reason: {state.escalation_reason}."
    )


def _determine_priority(state: AgentState) -> str:
    if state.risk_score >= 0.8:
        return "CRITICAL"
    if state.risk_score >= 0.65:
        return "HIGH"
    if state.confidence_score < 0.6:
        return "MEDIUM"
    return "LOW"


def _determine_team(state: AgentState) -> str:
    fraud = state.fraud_analysis
    if fraud and fraud.is_suspicious:
        return "Trust & Safety"
    category = state.ticket.category
    if category and "payment" in category.value:
        return "Billing"
    if category and "account" in category.value:
        return "Account Security"
    return "Level-2 Support"


def _recommend_action(state: AgentState) -> str:
    fraud = state.fraud_analysis
    if fraud and fraud.fraud_risk_level.value in ["high", "critical"]:
        return "Review evidence for fraud. Cross-check with Trust & Safety database before any refund."
    if state.confidence_score < 0.6:
        return "Review retrieved policies and contact customer for additional information."
    return "Standard escalation review. Customer context and policies are attached."


async def _notify_slack(case_file: Dict[str, Any]):
    """Send escalation alert to Slack."""
    try:
        import httpx
        message = {
            "text": f"🚨 *ArgusCX Escalation Alert*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*New Escalation — Case #{case_file['case_id'][:8].upper()}*\n"
                            f"*Priority:* {case_file['priority']}\n"
                            f"*Customer:* {case_file['customer_profile']['name']}\n"
                            f"*Team:* {case_file.get('assigned_team', 'Support')}\n"
                            f"*Reason:* {case_file['escalation_reason']}"
                        ),
                    },
                }
            ],
        }
        async with httpx.AsyncClient() as client:
            await client.post(settings.SLACK_WEBHOOK_URL, json=message, timeout=5.0)
    except Exception as e:
        logger.error("Failed to send Slack notification", error=str(e))
