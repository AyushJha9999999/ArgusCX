"""
ArgusCX — Razorpay Connector
Fetches real payment data from Razorpay when API key is configured.
Uses LLM-generated realistic simulation data when no key is available.
"""
from typing import Any, Dict, Optional
import structlog
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.connectors.base import BaseConnector
from app.core.llm import get_llm

logger = structlog.get_logger(__name__)


class RazorpayPaymentData(BaseModel):
    payment_id: str = Field(description="Razorpay payment identifier (pay_xxxxx)")
    order_id: str = Field(description="Associated order identifier")
    status: str = Field(description="Payment status: authorized, captured, failed, refunded")
    method: str = Field(description="Payment method: upi, card, netbanking, wallet, emi")
    amount: float = Field(description="Payment amount in INR")
    currency: str = Field(default="INR", description="Currency code")
    gateway: str = Field(default="Razorpay", description="Payment gateway")
    paid_at: str = Field(description="ISO timestamp of payment")
    upi_id: Optional[str] = Field(default=None, description="UPI VPA if UPI payment")
    bank: Optional[str] = Field(default=None, description="Bank name if net banking")
    refund_status: Optional[str] = Field(default=None, description="Refund status")


class RazorpayConnector(BaseConnector):
    """Razorpay Payment Gateway connector (India-focused)."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None, **kwargs):
        super().__init__(api_key=key_id, **kwargs)
        self.key_secret = key_secret

    async def fetch_order(self, order_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        if self.is_live and order_id:
            return await self._live_fetch_order(order_id)
        return {}

    async def fetch_payment(self, payment_id: str = None, order_id: str = None) -> Dict[str, Any]:
        if self.is_live:
            if payment_id:
                return await self._live_fetch_payment(payment_id)
            return await self._live_list_payments(order_id)
        return await self._llm_generate_payment(payment_id, order_id)

    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        return {}

    async def _live_fetch_order(self, order_id: str) -> Dict[str, Any]:
        """Real Razorpay order fetch."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.razorpay.com/v1/orders/{order_id}",
                auth=(self.api_key, self.key_secret),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def _live_fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Real Razorpay payment fetch."""
        if not payment_id:
            return {"error": "A Razorpay payment_id is required for a specific lookup."}
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.razorpay.com/v1/payments/{payment_id}",
                auth=(self.api_key, self.key_secret),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def _live_list_payments(self, order_id: str = None) -> Dict[str, Any]:
        """Read-only payment discovery for test-mode and unmapped orders."""
        import httpx

        params = {"count": 1}
        if order_id:
            params["order_id"] = order_id
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.razorpay.com/v1/payments",
                auth=(self.api_key, self.key_secret),
                params=params,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def _llm_generate_payment(self, payment_id: str, order_id: str) -> Dict[str, Any]:
        """Use Groq LLM to generate realistic Razorpay payment data."""
        llm = get_llm(temperature=0.3)
        if not llm:
            return {"error": "No LLM available"}

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data simulator for the Razorpay payment gateway (India).
Generate a realistic Razorpay payment record for an Indian e-commerce transaction.
Use realistic Indian payment methods: UPI (with realistic VPA like name@upi), credit/debit card, net banking (with real Indian bank names like HDFC, SBI, ICICI).
Use Razorpay-style IDs like pay_XXXXXXXXX. Amounts should be in INR."""),
            ("user", "Generate Razorpay payment data for order_id: {order_id}, payment_id: {payment_id}"),
        ])

        structured_llm = llm.with_structured_output(RazorpayPaymentData)
        chain = prompt | structured_llm

        try:
            result: RazorpayPaymentData = await chain.ainvoke({
                "order_id": order_id or "ORD-UNKNOWN",
                "payment_id": payment_id or "pay_unknown",
            })
            return result.model_dump()
        except Exception as e:
            logger.error("Razorpay LLM generation failed", error=str(e))
            return {"error": str(e)}
