"""
ArgusCX — Data Investigation Agent
Uses Groq LLM to cross-reference customer claims against order/payment data.
Fetches data via external connectors (Shopify/Stripe/Razorpay).
"""
import json
from typing import Any, Dict, List, Optional
import structlog
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.models.schemas import AgentState
from app.core.config import settings
from app.core.llm import get_llm
from app.connectors.shopify import ShopifyConnector
from app.connectors.stripe import StripeConnector
from app.connectors.razorpay import RazorpayConnector
from app.services.prompt_manager import get_system_prompt

logger = structlog.get_logger(__name__)


class InvestigationResult(BaseModel):
    claim_verified: bool = Field(description="Whether the customer's claim is consistent with the data")
    anomalies: List[str] = Field(default_factory=list, description="Specific anomalies or red flags found")
    timeline_analysis: str = Field(description="Analysis of whether the timeline of events makes sense")
    risk_indicators: List[str] = Field(default_factory=list, description="Behavioral patterns suggesting fraud or abuse")
    confidence: float = Field(description="Confidence in the analysis (0.0 to 1.0)")
    reasoning: str = Field(description="Detailed reasoning chain explaining findings")


def _get_connectors():
    """Initialize connectors based on config."""
    shopify = ShopifyConnector(
        api_key=getattr(settings, 'SHOPIFY_ACCESS_TOKEN', None),
        shop_domain=getattr(settings, 'SHOPIFY_SHOP_DOMAIN', None),
    )
    stripe = StripeConnector(
        api_key=getattr(settings, 'STRIPE_SECRET_KEY', None),
    )
    razorpay = RazorpayConnector(
        key_id=getattr(settings, 'RAZORPAY_KEY_ID', None),
        key_secret=getattr(settings, 'RAZORPAY_KEY_SECRET', None),
    )
    return shopify, stripe, razorpay


async def run_investigation_agent(state: AgentState) -> Dict[str, Any]:
    """
    Cross-references customer claims with actual order/payment data using Groq LLM.
    Fetches data via connectors and uses LLM to analyze for anomalies.
    """
    logger.info("🔎 Investigation agent running", ticket_id=state.ticket.id)

    customer = state.ticket.customer
    shopify, stripe, razorpay = _get_connectors()

    # ── Step 1: Fetch data from connectors ──────────
    order_data = await shopify.fetch_order(customer_id=customer.id)
    order_id = order_data.get("order_id") if isinstance(order_data, dict) else None
    payment_id = order_data.get("payment_id") if isinstance(order_data, dict) else None
    razorpay_order_id = (
        order_id
        if order_id and not str(order_id).upper().startswith(("ORD-UNKNOWN", "UNKNOWN"))
        else None
    )
    payment_data: Dict[str, Any] = {}

    # Razorpay requires a concrete payment/order identifier. Do not call its
    # endpoint with None when the order connector has no live record.
    if razorpay.is_live:
        try:
            payment_data = await razorpay.fetch_payment(
                payment_id=payment_id,
                order_id=razorpay_order_id,
            )
        except Exception as exc:
            logger.warning("Razorpay lookup failed; trying Stripe", error=str(exc))

    if not payment_data or payment_data.get("error"):
        try:
            payment_data = await stripe.fetch_payment(order_id=order_id)
        except Exception as exc:
            logger.warning("Stripe lookup failed; continuing without payment data", error=str(exc))
            payment_data = {"error": "Payment lookup unavailable"}

    user_history = await shopify.fetch_customer_history(customer_id=customer.id)

    logger.info(
        "Investigation data fetched",
        order_mode="live" if shopify.is_live else "llm_generated",
        payment_mode="live" if (razorpay.is_live or stripe.is_live) else "llm_generated",
        has_order=bool(order_data and not order_data.get("error")),
        has_payment=bool(payment_data and not payment_data.get("error")),
    )

    # ── Step 2: LLM Cross-Reference Analysis ──────────
    llm = get_llm(temperature=0.1)
    if not llm:
        logger.warning("No LLM configured for investigation — returning raw data only")
        return {
            "order_data": order_data,
            "payment_data": payment_data,
            "user_history": user_history,
            "anomalies": [],
            "confidence": 0.5,
            "reasoning": "Investigation data fetched but LLM not available for analysis.",
        }

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt("investigation")),
        ("user", """Customer's Support Ticket:
Subject: {subject}
Message: {message}
Customer Account Age: {account_age} days
Previous Tickets: {prev_tickets}
Previous Fraud Flags: {prev_fraud}

Order Data:
{order_data}

Payment Data:
{payment_data}

Customer History:
{user_history}
"""),
    ])

    structured_llm = llm.with_structured_output(InvestigationResult)
    chain = prompt | structured_llm

    try:
        result: InvestigationResult = await chain.ainvoke({
            "subject": state.ticket.subject,
            "message": state.ticket.message,
            "account_age": customer.account_age_days or "unknown",
            "prev_tickets": customer.previous_tickets,
            "prev_fraud": customer.previous_fraud_flags,
            "order_data": json.dumps(order_data, default=str),
            "payment_data": json.dumps(payment_data, default=str),
            "user_history": json.dumps(user_history, default=str),
        })

        logger.info(
            "Investigation analysis complete",
            claim_verified=result.claim_verified,
            anomalies_count=len(result.anomalies),
            confidence=result.confidence,
        )

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

    except Exception as e:
        logger.error("Investigation LLM analysis failed", error=str(e))
        return {
            "order_data": order_data,
            "payment_data": payment_data,
            "user_history": user_history,
            "anomalies": [],
            "confidence": 0.5,
            "reasoning": f"Investigation data fetched but LLM analysis failed: {str(e)[:80]}",
            "error": str(e),
        }
