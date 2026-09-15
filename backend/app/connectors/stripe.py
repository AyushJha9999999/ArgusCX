"""
ArgusCX — Stripe Connector
Fetches real payment data from Stripe when API key is configured.
Uses LLM-generated realistic simulation data when no key is available.
"""
from typing import Any, Dict, Optional
import structlog
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.connectors.base import BaseConnector
from app.core.llm import get_llm

logger = structlog.get_logger(__name__)


class PaymentData(BaseModel):
    payment_id: str = Field(description="Payment identifier")
    order_id: str = Field(description="Associated order identifier")
    status: str = Field(description="Payment status: pending, captured, failed, refunded, disputed")
    method: str = Field(description="Payment method: credit_card, debit_card, UPI, net_banking, wallet")
    amount: float = Field(description="Payment amount")
    currency: str = Field(description="Currency code")
    gateway: str = Field(description="Payment gateway name")
    paid_at: str = Field(description="ISO timestamp of payment")
    refund_status: Optional[str] = Field(default=None, description="Refund status if applicable")
    card_last4: Optional[str] = Field(default=None, description="Last 4 digits of card if applicable")


class StripeConnector(BaseConnector):
    """Stripe Payment Gateway connector."""

    async def fetch_order(self, order_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        return {}  # Stripe doesn't have orders — use Shopify connector

    async def fetch_payment(self, payment_id: str = None, order_id: str = None) -> Dict[str, Any]:
        if self.is_live:
            return await self._live_fetch_payment(payment_id, order_id)
        return await self._llm_generate_payment(payment_id, order_id)

    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        if self.is_live:
            return await self._live_fetch_customer(customer_id)
        return {}

    async def _live_fetch_payment(self, payment_id: str, order_id: str) -> Dict[str, Any]:
        """Real Stripe API call."""
        import httpx
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient() as client:
            if payment_id:
                resp = await client.get(
                    f"https://api.stripe.com/v1/payment_intents/{payment_id}",
                    headers=headers, timeout=10.0,
                )
            else:
                resp = await client.get(
                    "https://api.stripe.com/v1/payment_intents",
                    headers=headers, params={"limit": 1}, timeout=10.0,
                )
            resp.raise_for_status()
            return resp.json()

    async def _live_fetch_customer(self, customer_id: str) -> Dict[str, Any]:
        """Real Stripe customer fetch."""
        import httpx
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.stripe.com/v1/customers/{customer_id}",
                headers=headers, timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def _llm_generate_payment(self, payment_id: str, order_id: str) -> Dict[str, Any]:
        """Use Groq LLM to generate realistic payment data."""
        llm = get_llm(temperature=0.3)
        if not llm:
            return {"error": "No LLM available"}

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data simulator for a payment gateway system.
Generate a realistic payment record for an Indian e-commerce transaction.
Use realistic payment methods popular in India (UPI, credit card, net banking).
Use real payment gateway names like Razorpay, Stripe, PayU."""),
            ("user", "Generate payment data for order_id: {order_id}, payment_id: {payment_id}"),
        ])

        structured_llm = llm.with_structured_output(PaymentData)
        chain = prompt | structured_llm

        try:
            result: PaymentData = await chain.ainvoke({
                "order_id": order_id or "ORD-UNKNOWN",
                "payment_id": payment_id or "PAY-UNKNOWN",
            })
            return result.model_dump()
        except Exception as e:
            logger.error("Stripe LLM generation failed", error=str(e))
            return {"error": str(e)}
