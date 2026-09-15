"""
ArgusCX — Resolution Agent
Applies policy engine and makes final resolution decision using Groq LLM.
Uses centralized prompts and the policy engine service.
"""
from typing import Any, Dict, Optional
import structlog
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.models.schemas import AgentState, ResolutionDecision, FraudRiskLevel, TicketCategory
from app.core.config import settings
from app.core.llm import get_llm
from app.services.prompt_manager import get_system_prompt
from app.services.policy_engine import evaluate_policies
import json

logger = structlog.get_logger(__name__)


class ResolutionOutput(BaseModel):
    decision: ResolutionDecision = Field(description="The final resolution decision")
    message: str = Field(description="The customer-facing message explaining the resolution.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    should_escalate: bool = Field(description="True if human intervention is required, False otherwise.")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation if applicable, else null.")
    reasoning: str = Field(description="Internal reasoning chain for this decision.")


async def run_resolution_agent(state: AgentState) -> Dict[str, Any]:
    """
    Uses Groq LLM + Policy Engine to make a resolution decision.
    No hardcoded logic — everything goes through the LLM.
    """
    logger.info("✅ Resolution agent running", ticket_id=state.ticket.id)

    # ── Step 1: Evaluate policies via LLM ────────────
    policy_result = await evaluate_policies(
        category=state.ticket.category.value if state.ticket.category else "general",
        message=state.ticket.message,
        retrieved_policies=state.retrieved_policies,
        fraud_score=state.fraud_analysis.fraud_score if state.fraud_analysis else 0.0,
        order_data=state.order_data,
    )

    # ── Step 2: Make resolution decision via LLM ─────
    llm = get_llm(temperature=0.1)
    if not llm:
        logger.warning("No LLM configured for resolution — defaulting to escalation")
        return {
            "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
            "message": "Your case has been forwarded to a specialist for review.",
            "confidence": 0.5,
            "should_escalate": True,
            "escalation_reason": "LLM not available for resolution",
            "reasoning": "No LLM configured — escalating to human agent.",
        }

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("resolution")),
        ("user", """Ticket ID: {ticket_id}
Subject: {subject}
Message: {message}

Retrieved Policies:
{policies}

Policy Engine Assessment:
- Applicable Policies: {applicable_policies}
- Permitted Actions: {permitted_actions}
- Constraints: {constraints}
- Auto-Resolve Eligible: {auto_resolve}
- Policy Reasoning: {policy_reasoning}

Fraud Analysis:
{fraud_analysis}

Investigation Data:
- Order: {order_data}
- Payment: {payment_data}
- Anomalies Found: {anomalies}
- Investigation Reasoning: {investigation_reasoning}
"""),
    ])

    structured_llm = llm.with_structured_output(ResolutionOutput)
    chain = prompt | structured_llm

    try:
        fraud_json = state.fraud_analysis.model_dump_json() if state.fraud_analysis else "No evidence provided."
        order_json = json.dumps(state.order_data, default=str) if state.order_data else "No order data found."
        payment_json = json.dumps(state.payment_data, default=str) if state.payment_data else "No payment data."
        policies_text = "\n".join(state.retrieved_policies) if state.retrieved_policies else "No policies retrieved."

        # Get investigation anomalies from agent steps
        investigation_step = next(
            (s for s in state.ticket.agent_steps if s.agent_type.value == "data_investigation"),
            None,
        )
        anomalies = investigation_step.output_data.get("anomalies", []) if investigation_step else []
        inv_reasoning = investigation_step.output_data.get("reasoning", "No investigation data.") if investigation_step else "No investigation data."

        result: ResolutionOutput = await chain.ainvoke({
            "ticket_id": state.ticket.id,
            "subject": state.ticket.subject,
            "message": state.ticket.message,
            "policies": policies_text,
            "applicable_policies": ", ".join(policy_result.applicable_policies),
            "permitted_actions": ", ".join(policy_result.permitted_actions),
            "constraints": ", ".join(policy_result.constraints) if policy_result.constraints else "None",
            "auto_resolve": policy_result.auto_resolve_eligible,
            "policy_reasoning": policy_result.reasoning,
            "fraud_analysis": fraud_json,
            "order_data": order_json,
            "payment_data": payment_json,
            "anomalies": ", ".join(anomalies) if anomalies else "None detected",
            "investigation_reasoning": inv_reasoning,
        })

        logger.info(
            "Resolution decision made",
            decision=result.decision.value,
            confidence=result.confidence,
            should_escalate=result.should_escalate,
        )

        return result.model_dump()
    except Exception as e:
        logger.error("LLM Resolution failed", error=str(e))
        return {
            "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
            "message": "Your case is being reviewed by our team. We'll get back to you shortly.",
            "confidence": 0.5,
            "should_escalate": True,
            "escalation_reason": f"Resolution LLM error: {str(e)[:60]}",
            "reasoning": f"Resolution agent encountered an error: {str(e)[:80]}",
            "error": str(e),
        }
