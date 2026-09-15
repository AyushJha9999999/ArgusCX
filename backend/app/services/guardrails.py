"""
ArgusCX — Safety & Compliance Guardrails (Shared Services)
Uses Groq LLM to check for toxicity, jailbreak attempts, and compliance violations.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
import structlog

from app.core.llm import get_llm
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class GuardrailResult(BaseModel):
    is_toxic: bool = Field(description="Whether the message contains toxic content")
    is_jailbreak: bool = Field(description="Whether the message is a jailbreak attempt")
    is_compliant: bool = Field(description="Whether the message is compliant with support practices")
    risk_flags: List[str] = Field(default_factory=list, description="Specific risk flags detected")
    recommendation: str = Field(description="One of: allow, flag_for_review, block")
    explanation: str = Field(description="Brief explanation of the decision")


async def check_guardrails(message: str, context: str = "customer_input") -> GuardrailResult:
    """
    Run safety and compliance checks on a message using Groq LLM.
    Context can be 'customer_input' or 'agent_response'.
    """
    llm = get_llm(temperature=0.0)
    if not llm:
        logger.warning("No LLM configured for guardrails — allowing by default")
        return GuardrailResult(
            is_toxic=False,
            is_jailbreak=False,
            is_compliant=True,
            risk_flags=[],
            recommendation="allow",
            explanation="Guardrails unavailable — LLM not configured.",
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("guardrails")),
        ("user", "Context: {context}\nMessage to analyze:\n{message}"),
    ])

    structured_llm = llm.with_structured_output(GuardrailResult)
    chain = prompt | structured_llm

    try:
        result: GuardrailResult = await chain.ainvoke({
            "context": context,
            "message": message,
        })
        logger.info(
            "Guardrails check complete",
            recommendation=result.recommendation,
            is_toxic=result.is_toxic,
            is_jailbreak=result.is_jailbreak,
            flags=result.risk_flags,
        )
        return result
    except Exception as e:
        logger.error("Guardrails check failed", error=str(e))
        return GuardrailResult(
            is_toxic=False,
            is_jailbreak=False,
            is_compliant=True,
            risk_flags=[],
            recommendation="allow",
            explanation=f"Guardrails error: {str(e)[:80]}",
        )
