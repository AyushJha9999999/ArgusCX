"""
ArgusCX — Policy Engine (Shared Services)
Uses Groq LLM to dynamically determine applicable policies and permitted actions.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
import structlog

from app.core.llm import get_llm
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class PolicyResult(BaseModel):
    applicable_policies: List[str] = Field(description="List of policy names that apply")
    permitted_actions: List[str] = Field(description="Actions allowed under these policies")
    constraints: List[str] = Field(default_factory=list, description="Constraints on permitted actions")
    auto_resolve_eligible: bool = Field(description="Whether ticket can be auto-resolved")
    reasoning: str = Field(description="Why these policies apply")


async def evaluate_policies(
    category: str,
    message: str,
    retrieved_policies: List[str],
    fraud_score: float = 0.0,
    order_data: dict = None,
) -> PolicyResult:
    """
    Use Groq LLM to evaluate which business policies apply to this ticket
    and determine what actions are permitted.
    """
    llm = get_llm(temperature=0.0)
    if not llm:
        logger.warning("No LLM configured for policy engine")
        return PolicyResult(
            applicable_policies=["Default Support Policy"],
            permitted_actions=["escalate"],
            constraints=["LLM not available — escalating to human"],
            auto_resolve_eligible=False,
            reasoning="Policy engine unavailable — defaulting to human escalation.",
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("policy_engine")),
        ("user", """Ticket Category: {category}
Customer Message: {message}

Retrieved Knowledge Base Policies:
{policies}

Fraud Risk Score: {fraud_score}
Order Data: {order_data}
"""),
    ])

    structured_llm = llm.with_structured_output(PolicyResult)
    chain = prompt | structured_llm

    try:
        import json
        result: PolicyResult = await chain.ainvoke({
            "category": category or "general",
            "message": message,
            "policies": "\n".join(retrieved_policies) if retrieved_policies else "No policies retrieved.",
            "fraud_score": fraud_score,
            "order_data": json.dumps(order_data) if order_data else "No order data.",
        })
        logger.info(
            "Policy evaluation complete",
            policies=result.applicable_policies,
            actions=result.permitted_actions,
            auto_resolve=result.auto_resolve_eligible,
        )
        return result
    except Exception as e:
        logger.error("Policy engine failed", error=str(e))
        return PolicyResult(
            applicable_policies=["Default Support Policy"],
            permitted_actions=["escalate"],
            constraints=[f"Policy engine error: {str(e)[:60]}"],
            auto_resolve_eligible=False,
            reasoning="Policy engine error — defaulting to human escalation.",
        )
