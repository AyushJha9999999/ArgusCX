"""Resolution agent with a human-safe failure mode."""
import json
from typing import Any, Dict, Optional

import structlog
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.models.schemas import AgentState, ResolutionDecision
from app.services.policy_engine import evaluate_policies
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class ResolutionOutput(BaseModel):
    decision: ResolutionDecision
    message: str
    confidence: float = Field(ge=0.0, le=1.0)
    should_escalate: bool
    escalation_reason: Optional[str] = None
    reasoning: str


def _human_review(reason: str) -> Dict[str, Any]:
    return {
        "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
        "message": "Your case is being reviewed by a support specialist.",
        "confidence": 0.0,
        "should_escalate": True,
        "escalation_reason": reason,
        "reasoning": "No automated resolution was issued; a human decision is required.",
    }


async def run_resolution_agent(state: AgentState) -> Dict[str, Any]:
    """Make a governed decision only when policy context and AI are available."""
    policy_result = await evaluate_policies(
        category=state.ticket.category.value if state.ticket.category else "general",
        message=state.ticket.message,
        retrieved_policies=state.retrieved_policies,
        fraud_score=state.fraud_analysis.fraud_score if state.fraud_analysis else 0.0,
        order_data=state.order_data,
    )
    llm = get_llm(temperature=0.1)
    if not llm:
        return _human_review("AI reasoning is not configured for this workspace.")
    if not state.retrieved_policies:
        return _human_review("No organisation policy has been ingested for this case type.")

    investigation_step = next(
        (step for step in state.ticket.agent_steps if step.agent_type.value == "data_investigation"),
        None,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("resolution") + "\nNever approve, deny, refund, or punish a customer when evidence or policy is missing; route to human review."),
        ("user", """Ticket ID: {ticket_id}
Subject: {subject}
Message: {message}

Organisation policies: {policies}
Policy assessment: {policy_result}
Fraud analysis: {fraud_analysis}
Order data: {order_data}
Payment data: {payment_data}
Investigation: {investigation}"""),
    ])
    try:
        output: ResolutionOutput = await (prompt | llm.with_structured_output(ResolutionOutput)).ainvoke({
            "ticket_id": state.ticket.id,
            "subject": state.ticket.subject,
            "message": state.ticket.message,
            "policies": "\n".join(state.retrieved_policies),
            "policy_result": policy_result.model_dump_json(),
            "fraud_analysis": state.fraud_analysis.model_dump_json() if state.fraud_analysis else "not assessed",
            "order_data": json.dumps(state.order_data, default=str),
            "payment_data": json.dumps(state.payment_data, default=str),
            "investigation": json.dumps(investigation_step.output_data if investigation_step else {}, default=str),
        })
        if output.decision != ResolutionDecision.ESCALATE_TO_HUMAN and not policy_result.auto_resolve_eligible:
            return _human_review("The applicable policy does not permit an automated outcome.")
        return output.model_dump()
    except Exception as exc:
        logger.error("Resolution reasoning failed", error=str(exc))
        return _human_review("AI reasoning did not complete; a human review is required.")
