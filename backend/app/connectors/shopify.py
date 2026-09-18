"""Read-only Shopify Admin API connector."""
from typing import Any, Dict, Optional
import httpx

from app.connectors.base import BaseConnector, ConnectorConfigurationError


class ShopifyConnector(BaseConnector):
    def __init__(self, api_key: Optional[str] = None, shop_domain: Optional[str] = None, **kwargs: Any):
        super().__init__(api_key=api_key, **kwargs)
        self.shop_domain = (shop_domain or "").removeprefix("https://").removeprefix("http://").rstrip("/")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.shop_domain)

    def require_configuration(self) -> None:
        if not self.is_configured:
            raise ConnectorConfigurationError("Shopify requires SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN.")

    def _headers(self) -> Dict[str, str]:
        return {"X-Shopify-Access-Token": str(self.api_key)}

    async def fetch_order(self, order_id: Optional[str] = None, customer_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_configuration()
        if not order_id and not customer_id:
            raise ConnectorConfigurationError("An order ID or customer ID is required for a Shopify lookup.")
        url = f"https://{self.shop_domain}/admin/api/2025-01/orders/{order_id}.json" if order_id else f"https://{self.shop_domain}/admin/api/2025-01/orders.json"
        params = {"customer_id": customer_id, "status": "any", "limit": 1} if customer_id and not order_id else None
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            return response.json()

    async def fetch_payment(self, payment_id: Optional[str] = None, order_id: Optional[str] = None) -> Dict[str, Any]:
        return {"status": "not_supported", "provider": "shopify", "detail": "Use your payment provider connector for payment data."}

    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        self.require_configuration()
        if not customer_id:
            raise ConnectorConfigurationError("A Shopify customer ID is required for customer history.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://{self.shop_domain}/admin/api/2025-01/customers/{customer_id}.json",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
