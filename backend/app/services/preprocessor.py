"""
ArgusCX — Request Preprocessor (Shared Services)
Uses Groq LLM to analyze incoming messages for:
  - Language detection
  - PII redaction
  - Intent classification
  - Sentiment analysis
  - Urgency scoring
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
import structlog

from app.core.llm import get_llm
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class PreprocessorResult(BaseModel):
    language: str = Field(description="ISO 639-1 language code")
    intent: str = Field(description="Primary customer intent")
    sentiment: str = Field(description="Customer sentiment")
    urgency: str = Field(description="Urgency level")
    pii_detected: List[str] = Field(default_factory=list, description="Types of PII found")
    sanitized_message: str = Field(description="Message with PII replaced by placeholders")
    summary: str = Field(description="One-line summary of the request")


async def preprocess_request(message: str, subject: str = "") -> PreprocessorResult:
    """
    Preprocess a customer message using Groq LLM.
    Detects language, intent, sentiment, urgency, and redacts PII.
    """
    llm = get_llm(temperature=0.0)
    if not llm:
        logger.warning("No LLM configured for preprocessor")
        return PreprocessorResult(
            language="en",
            intent="general_inquiry",
            sentiment="neutral",
            urgency="medium",
            pii_detected=[],
            sanitized_message=message,
            summary=subject or message[:100],
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("preprocessor")),
        ("user", "Subject: {subject}\nMessage: {message}"),
    ])

    structured_llm = llm.with_structured_output(PreprocessorResult)
    chain = prompt | structured_llm

    try:
        result: PreprocessorResult = await chain.ainvoke({
            "subject": subject,
            "message": message,
        })
        logger.info(
            "Preprocessor complete",
            language=result.language,
            intent=result.intent,
            sentiment=result.sentiment,
            urgency=result.urgency,
            pii_count=len(result.pii_detected),
        )
        return result
    except Exception as e:
        logger.error("Preprocessor failed", error=str(e))
        return PreprocessorResult(
            language="en",
            intent="general_inquiry",
            sentiment="neutral",
            urgency="medium",
            pii_detected=[],
            sanitized_message=message,
            summary=subject or message[:100],
        )
