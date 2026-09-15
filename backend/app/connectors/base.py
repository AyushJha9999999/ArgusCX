"""
ArgusCX — Base Connector
Abstract base class for all external system connectors.
Each connector can operate in two modes:
  1. Live mode: Real API calls when credentials are provided
  2. Simulation mode: LLM-generated realistic data when no credentials
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger(__name__)


class BaseConnector(ABC):
    """Base class for external system connectors."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self.is_live = bool(api_key)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def mode(self) -> str:
        return "live" if self.is_live else "simulation"

    @abstractmethod
    async def fetch_order(self, order_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        """Fetch order data."""
        pass

    @abstractmethod
    async def fetch_payment(self, payment_id: str = None, order_id: str = None) -> Dict[str, Any]:
        """Fetch payment data."""
        pass

    @abstractmethod
    async def fetch_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """Fetch customer history."""
        pass

    async def health_check(self) -> Dict[str, Any]:
        return {
            "connector": self.name,
            "mode": self.mode,
            "status": "connected" if self.is_live else "simulation",
        }
