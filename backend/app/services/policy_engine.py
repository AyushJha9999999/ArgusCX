"""Policy evaluation that fails closed when policies or reasoning are absent."""
import json
from typing import List, Optional

import structlog
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class PolicyResult(BaseModel):
    applicable_policies: List[str]
    permitted_actions: List[str]
    constraints: List[str] = Field(default_factory=list)
    auto_resolve_eligible: bool
    reasoning: str


def _review_only(reason: str) -> PolicyResult:
    return PolicyResult(
        applicable_policies=[],
        permitted_actions=["escalate"],
        constraints=[reason],
        auto_resolve_eligible=False,
        reasoning="No automated policy decision was issued.",
    )


async def evaluate_policies(
    category: str,
    message: str,
    retrieved_policies: List[str],
    fraud_score: float = 0.0,
    order_data: Optional[dict] = None,
) -> PolicyResult:
    if not retrieved_policies:
        return _review_only("No organisation policy has been ingested for this case type.")
    llm = get_llm(temperature=0.0)
    if not llm:
        return _review_only("AI policy reasoning is not configured.")

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("policy_engine") + "\nNever permit automatic action when the supplied policies do not explicitly allow it."),
        ("user", """Ticket category: {category}
Customer message: {message}
Organisation policies: {policies}
Fraud score: {fraud_score}
Order data: {order_data}"""),
    ])
    try:
        result: PolicyResult = await (prompt | llm.with_structured_output(PolicyResult)).ainvoke({
            "category": category or "general",
            "message": message,
            "policies": "\n".join(retrieved_policies),
            "fraud_score": fraud_score,
            "order_data": json.dumps(order_data, default=str),
        })
        return result
    except Exception as exc:
        logger.error("Policy reasoning failed", error=str(exc))
        return _review_only("AI policy reasoning did not complete.")
