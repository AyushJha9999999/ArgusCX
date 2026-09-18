"""Read-only Razorpay connector for payment and order investigation."""
from typing import Any, Dict, Optional
import httpx

from app.connectors.base import BaseConnector, ConnectorConfigurationError


class RazorpayConnector(BaseConnector):
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None, **kwargs: Any):
        super().__init__(api_key=key_id, **kwargs)
        self.key_secret = key_secret

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.key_secret)

    def require_configuration(self) -> None:
        if not self.is_configured:
            raise ConnectorConfigurationError("Razorpay requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")

    async def fetch_order(self, order_id: Optional[str] = None, customer_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_configuration()
        if not order_id:
            raise ConnectorConfigurationError("A Razorpay order ID is required for an order lookup.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://api.razorpay.com/v1/orders/{order_id}", auth=(self.api_key, self.key_secret))
            response.raise_for_status()
            return response.json()

    async def fetch_payment(self, payment_id: Optional[str] = None, order_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_configuration()
        if not payment_id:
            raise ConnectorConfigurationError("A Razorpay payment ID is required for a precise payment lookup.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://api.razorpay.com/v1/payments/{payment_id}", auth=(self.api_key, self.key_secret))
            response.raise_for_status()
            return response.json()

    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        return {"status": "not_supported", "provider": "razorpay", "detail": "Razorpay does not provide CRM history."}
