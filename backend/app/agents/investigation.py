"""Investigation agent that reasons only over provided and live provider data."""
import json
from typing import Any, Awaitable, Callable, Dict, List

import structlog
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.connectors.base import ConnectorConfigurationError
from app.connectors.razorpay import RazorpayConnector
from app.connectors.shopify import ShopifyConnector
from app.connectors.stripe import StripeConnector
from app.core.config import settings
from app.core.llm import get_llm
from app.models.schemas import AgentState
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class InvestigationResult(BaseModel):
    claim_verified: bool = Field(description="Whether the claim is supported by the available evidence")
    anomalies: List[str] = Field(default_factory=list)
    timeline_analysis: str
    risk_indicators: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


def _get_connectors() -> tuple[ShopifyConnector, StripeConnector, RazorpayConnector]:
    return (
        ShopifyConnector(api_key=settings.SHOPIFY_ACCESS_TOKEN, shop_domain=settings.SHOPIFY_SHOP_DOMAIN),
        StripeConnector(api_key=settings.STRIPE_SECRET_KEY),
        RazorpayConnector(key_id=settings.RAZORPAY_KEY_ID, key_secret=settings.RAZORPAY_KEY_SECRET),
    )


async def _fetch_live(provider: str, operation: Callable[[], Awaitable[Dict[str, Any]]]) -> Dict[str, Any]:
    try:
        return await operation()
    except ConnectorConfigurationError as exc:
        return {"status": "not_configured", "provider": provider, "detail": str(exc)}
    except Exception as exc:
        logger.warning("Provider lookup failed", provider=provider, error=str(exc))
        return {"status": "unavailable", "provider": provider, "detail": "Provider lookup failed."}


async def run_investigation_agent(state: AgentState) -> Dict[str, Any]:
    """Cross-reference a claim with explicitly configured provider records."""
    customer = state.ticket.customer
    metadata = state.ticket.metadata or {}
    order_id = metadata.get("order_id")
    payment_id = metadata.get("payment_id")
    shopify, stripe, razorpay = _get_connectors()

    order_data = await _fetch_live(
        "shopify", lambda: shopify.fetch_order(order_id=order_id, customer_id=customer.id)
    )
    user_history = await _fetch_live("shopify", lambda: shopify.fetch_customer_history(customer.id))

    if payment_id and razorpay.is_configured:
        payment_data = await _fetch_live("razorpay", lambda: razorpay.fetch_payment(payment_id=payment_id))
    elif payment_id and stripe.is_configured:
        payment_data = await _fetch_live("stripe", lambda: stripe.fetch_payment(payment_id=payment_id))
    else:
        payment_data = {
            "status": "not_requested",
            "detail": "Provide payment_id and configure its provider to request live payment data.",
        }

    if not get_llm():
        return {
            "order_data": order_data,
            "payment_data": payment_data,
            "user_history": user_history,
            "anomalies": [],
            "confidence": 0.0,
            "reasoning": "No LLM is configured. Live provider records are attached for operator review.",
        }

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("investigation") + "\nNever infer missing provider records. State data gaps plainly."),
        ("user", """Customer support ticket:
Subject: {subject}
Message: {message}

Live order data: {order_data}
Live payment data: {payment_data}
Live customer history: {user_history}"""),
    ])

    try:
        result: InvestigationResult = await (prompt | get_llm(temperature=0.1).with_structured_output(InvestigationResult)).ainvoke({
            "subject": state.ticket.subject,
            "message": state.ticket.message,
            "order_data": json.dumps(order_data, default=str),
            "payment_data": json.dumps(payment_data, default=str),
            "user_history": json.dumps(user_history, default=str),
        })
        return {
            "order_data": order_data,
            "payment_data": payment_data,
            "user_history": user_history,
            "anomalies": result.anomalies,
            "claim_verified": result.claim_verified,
            "timeline_analysis": result.timeline_analysis,
            "risk_indicators": result.risk_indicators,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }
    except Exception as exc:
        logger.error("Investigation analysis failed", error=str(exc))
        return {
            "order_data": order_data,
            "payment_data": payment_data,
            "user_history": user_history,
            "anomalies": [],
            "confidence": 0.0,
            "reasoning": "Live provider records are attached, but AI analysis did not complete. Route to operator review.",
            "error": "analysis_unavailable",
        }
