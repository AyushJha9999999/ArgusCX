"""Shared contracts for live, server-side provider integrations."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ConnectorConfigurationError(RuntimeError):
    """Raised when a requested provider has not been configured."""


class BaseConnector(ABC):
    """A live data connector. It never substitutes generated provider data."""

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        self.api_key = api_key
        self.config = kwargs

    @property
    def name(self) -> str:
        return self.__class__.__name__.removesuffix("Connector").lower()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def mode(self) -> str:
        return "live" if self.is_configured else "not_configured"

    def require_configuration(self) -> None:
        if not self.is_configured:
            raise ConnectorConfigurationError(
                f"{self.name} is not configured. Add its server-side credentials before requesting live data."
            )

    async def health_check(self) -> Dict[str, str]:
        return {"connector": self.name, "mode": self.mode, "status": "configured" if self.is_configured else "not_configured"}

    @abstractmethod
    async def fetch_order(self, order_id: Optional[str] = None, customer_id: Optional[str] = None) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_payment(self, payment_id: Optional[str] = None, order_id: Optional[str] = None) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]: ...
