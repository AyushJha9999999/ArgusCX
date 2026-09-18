"""Read-only Stripe connector for server-side payment investigation."""
from typing import Any, Dict, Optional
import httpx

from app.connectors.base import BaseConnector, ConnectorConfigurationError


class StripeConnector(BaseConnector):
    async def fetch_order(self, order_id: Optional[str] = None, customer_id: Optional[str] = None) -> Dict[str, Any]:
        return {"status": "not_supported", "provider": "stripe", "detail": "Stripe does not own order records."}

    async def fetch_payment(self, payment_id: Optional[str] = None, order_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_configuration()
        if not payment_id:
            raise ConnectorConfigurationError("A Stripe PaymentIntent ID is required for a precise payment lookup.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.stripe.com/v1/payment_intents/{payment_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()

    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        self.require_configuration()
        if not customer_id:
            raise ConnectorConfigurationError("A Stripe customer ID is required for customer history.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.stripe.com/v1/customers/{customer_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()
