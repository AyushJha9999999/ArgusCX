"""
ArgusCX — Escalation Agent
Packages full case file for human handoff and notifies via Slack using Groq LLM.
"""
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.models.schemas import AgentState, AgentType, TicketStatus
from app.core.config import settings
from app.core.llm import get_llm
import json

logger = structlog.get_logger(__name__)


class EscalationOutput(BaseModel):
    summary: str = Field(description="A comprehensive summary of the case for the human agent.")
    priority: str = Field(description="The priority level of the case: LOW, MEDIUM, HIGH, CRITICAL.")
    assigned_team: str = Field(description="The recommended team to handle the case: Trust & Safety, Billing, Account Security, or Level-2 Support.")
    recommended_action: str = Field(description="Specific actionable recommendations for the human agent based on policies and fraud analysis.")


def _get_demo_escalation(state: AgentState) -> Dict[str, Any]:
    fraud = state.fraud_analysis
    risk_score = state.risk_score
    confidence = state.confidence_score

    priority = "LOW"
    if risk_score >= 0.8: priority = "CRITICAL"
    elif risk_score >= 0.65: priority = "HIGH"
    elif confidence < 0.6: priority = "MEDIUM"

    team = "Level-2 Support"
    if fraud and fraud.is_suspicious: team = "Trust & Safety"
    elif state.ticket.category and "payment" in state.ticket.category.value: team = "Billing"
    elif state.ticket.category and "account" in state.ticket.category.value: team = "Account Security"

    recommendation = "Standard escalation review. Customer context and policies are attached."
    if fraud and fraud.fraud_risk_level.value in ["high", "critical"]:
        recommendation = "Review evidence for fraud. Cross-check with Trust & Safety database before any refund."
    elif confidence < 0.6:
        recommendation = "Review retrieved policies and contact customer for additional information."

    summary = f"Customer submitted a ticket. Confidence: {confidence:.2f}. Risk: {risk_score:.2f}. Escalation reason: {state.escalation_reason}."
    
    return {
        "summary": summary,
        "priority": priority,
        "assigned_team": team,
        "recommended_action": recommendation
    }


async def run_escalation_agent(state: AgentState) -> Dict[str, Any]:
    """
    Builds a comprehensive case file and routes to the right human team using Groq LLM.
    Optionally sends Slack notification.
    """
    logger.info("🚨 Escalation agent packaging case", ticket_id=state.ticket.id)

    llm = get_llm(temperature=0.2)
    
    if not llm:
        logger.warning("No LLM provider configured, using heuristic escalation packaging.")
        escalation_data = _get_demo_escalation(state)
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Escalation Handoff Agent for ArgusCX.
Your job is to review a ticket that the AI failed to resolve or flagged for fraud, and package a concise but comprehensive briefing for the human support agent who will take over.

Determine the priority, the best team to assign to, write a summary, and give a recommended action based on the AI's reasoning, fraud analysis, and policies."""),
            ("user", """Ticket Subject: {subject}
Ticket Message: {message}
AI Escalation Reason: {escalation_reason}
AI Confidence Score: {confidence}
AI Risk Score: {risk_score}

Fraud Analysis: {fraud}
Order/Payment Data: {data}
Retrieved Policies: {policies}""")
        ])
        
        structured_llm = llm.with_structured_output(EscalationOutput)
        chain = prompt | structured_llm
        
        try:
            fraud_json = state.fraud_analysis.model_dump_json() if state.fraud_analysis else "None"
            data_json = json.dumps({"order": state.order_data, "payment": state.payment_data})
            policies_text = "\\n".join(state.retrieved_policies) if state.retrieved_policies else "None"
            
            result: EscalationOutput = await chain.ainvoke({
                "subject": state.ticket.subject,
                "message": state.ticket.message,
                "escalation_reason": state.escalation_reason or "Unknown",
                "confidence": state.confidence_score,
                "risk_score": state.risk_score,
                "fraud": fraud_json,
                "data": data_json,
                "policies": policies_text
            })
            escalation_data = result.model_dump()
        except Exception as e:
            logger.error("LLM Escalation failed, falling back to heuristic.", error=str(e))
            escalation_data = _get_demo_escalation(state)

    ticket = state.ticket
    fraud = state.fraud_analysis

    case_file = {
        "case_id": ticket.id,
        "generated_at": datetime.utcnow().isoformat(),
        "priority": escalation_data["priority"],
        "summary": escalation_data["summary"],
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
        "recommended_action": escalation_data["recommended_action"],
    }

    state.ticket.case_file = case_file
    state.ticket.status = TicketStatus.ESCALATED

    if settings.SLACK_WEBHOOK_URL and not settings.is_demo_mode:
        await _notify_slack(case_file)
    else:
        logger.info("📩 [DEMO] Slack notification would be sent", case_id=case_file["case_id"])

    return {
        "case_file": case_file,
        "assigned_team": escalation_data["assigned_team"],
        "confidence": 1.0,
        "reasoning": (
            f"Case packaged for human review. "
            f"Priority: {case_file['priority']}. "
            f"Reason: {state.escalation_reason}. "
            f"Assigned to: {escalation_data['assigned_team']} team."
        ),
    }


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
