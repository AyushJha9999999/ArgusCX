"""
ArgusCX — Shopify Connector
Fetches real order/customer data from Shopify when API key is configured.
Uses LLM-generated realistic simulation data when no key is available.
"""
from typing import Any, Dict, Optional
import structlog
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.connectors.base import BaseConnector
from app.core.llm import get_llm

logger = structlog.get_logger(__name__)


class OrderData(BaseModel):
    order_id: str = Field(description="Order identifier")
    customer_id: str = Field(description="Customer identifier")
    status: str = Field(description="Order status: pending, confirmed, shipped, delivered, cancelled, returned")
    items: list = Field(description="List of items with name, sku, qty, price")
    total_amount: float = Field(description="Total order amount")
    currency: str = Field(description="Currency code")
    ordered_at: str = Field(description="ISO timestamp when order was placed")
    delivered_at: Optional[str] = Field(default=None, description="ISO timestamp when delivered")
    delivery_address: str = Field(description="Delivery city/state")
    delivery_partner: str = Field(description="Logistics partner name")
    tracking_id: str = Field(description="Tracking identifier")


class CustomerHistory(BaseModel):
    customer_id: str = Field(description="Customer identifier")
    account_created: str = Field(description="ISO timestamp of account creation")
    total_orders: int = Field(description="Total number of orders")
    total_spent: float = Field(description="Total amount spent")
    currency: str = Field(description="Currency code")
    previous_refunds: int = Field(description="Number of previous refunds")
    previous_fraud_flags: int = Field(description="Number of previous fraud flags")
    support_tickets: int = Field(description="Number of previous support tickets")
    loyalty_tier: str = Field(description="Customer loyalty tier")


class ShopifyConnector(BaseConnector):
    """Shopify Order Management connector."""

    def __init__(self, api_key: Optional[str] = None, shop_domain: Optional[str] = None, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.shop_domain = shop_domain

    async def fetch_order(self, order_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        if self.is_live:
            return await self._live_fetch_order(order_id, customer_id)
        return await self._llm_generate_order(order_id, customer_id)

    async def fetch_payment(self, payment_id: str = None, order_id: str = None) -> Dict[str, Any]:
        # Shopify payment data is part of the order — delegate to payment connector
        return {}

    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        if self.is_live:
            return await self._live_fetch_history(customer_id)
        return await self._llm_generate_history(customer_id)

    async def _live_fetch_order(self, order_id: str, customer_id: str) -> Dict[str, Any]:
        """Real Shopify API call."""
        import httpx
        headers = {"X-Shopify-Access-Token": self.api_key}
        url = f"https://{self.shop_domain}/admin/api/2024-01/orders.json"
        params = {}
        if order_id:
            url = f"https://{self.shop_domain}/admin/api/2024-01/orders/{order_id}.json"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    async def _live_fetch_history(self, customer_id: str) -> Dict[str, Any]:
        """Real Shopify customer API call."""
        import httpx
        headers = {"X-Shopify-Access-Token": self.api_key}
        url = f"https://{self.shop_domain}/admin/api/2024-01/customers/{customer_id}.json"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    async def _llm_generate_order(self, order_id: str, customer_id: str) -> Dict[str, Any]:
        """Use Groq LLM to generate realistic order data for the simulation."""
        llm = get_llm(temperature=0.3)
        if not llm:
            return {"error": "No LLM available", "order_id": order_id or "unknown"}

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data simulator for an e-commerce order management system.
Generate a realistic order record for an Indian e-commerce customer. 
Use realistic product names, prices in INR, Indian cities, and real logistics partners like Delhivery, BlueDart, or DTDC.
The order should be a recently delivered order (within the last week)."""),
            ("user", "Generate an order for customer_id: {customer_id}, order_id: {order_id}"),
        ])

        structured_llm = llm.with_structured_output(OrderData)
        chain = prompt | structured_llm

        try:
            result: OrderData = await chain.ainvoke({
                "customer_id": customer_id or "CUST-001",
                "order_id": order_id or "ORD-UNKNOWN",
            })
            return result.model_dump()
        except Exception as e:
            logger.error("Shopify LLM generation failed", error=str(e))
            return {"error": str(e)}

    async def _llm_generate_history(self, customer_id: str) -> Dict[str, Any]:
        """Use Groq LLM to generate realistic customer history."""
        llm = get_llm(temperature=0.3)
        if not llm:
            return {"error": "No LLM available", "customer_id": customer_id}

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data simulator for an e-commerce CRM system.
Generate a realistic customer profile and history for an Indian e-commerce customer.
Include realistic order counts, spending in INR, and loyalty tiers."""),
            ("user", "Generate customer history for customer_id: {customer_id}"),
        ])

        structured_llm = llm.with_structured_output(CustomerHistory)
        chain = prompt | structured_llm

        try:
            result: CustomerHistory = await chain.ainvoke({"customer_id": customer_id})
            return result.model_dump()
        except Exception as e:
            logger.error("Shopify history LLM generation failed", error=str(e))
            return {"error": str(e)}
