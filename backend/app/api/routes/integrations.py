"""Read-only integration readiness API.

Secrets stay in the deployment environment.  The dashboard consumes this
endpoint to show what is actually connected at runtime; a configured value is
never represented as a successful connection.
"""
from fastapi import APIRouter

from app.connectors.razorpay import RazorpayConnector
from app.connectors.shopify import ShopifyConnector
from app.connectors.stripe import StripeConnector
from app.core.config import settings
from app.db.mongodb import get_mongo_db
from app.db.redis_client import get_redis
from app.db import postgres

router = APIRouter(prefix="/integrations")


@router.get("")
async def list_integrations():
    shopify = ShopifyConnector(settings.SHOPIFY_ACCESS_TOKEN, settings.SHOPIFY_SHOP_DOMAIN)
    stripe = StripeConnector(settings.STRIPE_SECRET_KEY)
    razorpay = RazorpayConnector(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)

    def service_state(*, configured: bool, connected: bool) -> str:
        if connected:
            return "connected"
        return "unreachable" if configured else "not_configured"

    object_storage_configured = bool(
        settings.OBJECT_STORAGE_BUCKET
        and settings.OBJECT_STORAGE_ACCESS_KEY
        and settings.OBJECT_STORAGE_SECRET_KEY
    )

    return {
        "integrations": [
            {
                "connector": "mongodb",
                "category": "data",
                "mode": service_state(
                    configured=bool(settings.MONGO_URI),
                    connected=get_mongo_db() is not None,
                ),
                "status": service_state(
                    configured=bool(settings.MONGO_URI),
                    connected=get_mongo_db() is not None,
                ),
                "description": "Case records, evidence metadata, and investigation history.",
            },
            {
                "connector": "postgresql",
                "category": "data",
                "mode": service_state(
                    configured=bool(settings.DATABASE_URL),
                    connected=postgres.AsyncSessionLocal is not None,
                ),
                "status": service_state(
                    configured=bool(settings.DATABASE_URL),
                    connected=postgres.AsyncSessionLocal is not None,
                ),
                "description": "Tenant, credential, and operational data.",
            },
            {
                "connector": "redis",
                "category": "data",
                "mode": service_state(
                    configured=bool(settings.REDIS_URL),
                    connected=get_redis() is not None,
                ),
                "status": service_state(
                    configured=bool(settings.REDIS_URL),
                    connected=get_redis() is not None,
                ),
                "description": "Live cache, rate limits, and background work coordination.",
            },
            {
                "connector": "object_storage",
                "category": "cloud",
                "mode": "configured" if object_storage_configured else "not_configured",
                "status": "configured" if object_storage_configured else "not_configured",
                "description": "S3-compatible evidence storage. Runtime upload checks happen when evidence is submitted.",
            },
            await shopify.health_check(),
            await stripe.health_check(),
            await razorpay.health_check(),
            {
                "connector": "smtp_handoffs",
                "category": "delivery",
                "mode": "live" if settings.smtp_configured else "not_configured",
                "status": "configured" if settings.smtp_configured else "not_configured",
                "description": "Escalation notices delivered through the configured mail provider.",
            },
            {
                "connector": "human_handoff_webhook",
                "category": "delivery",
                "mode": "live" if settings.human_handoff_webhook_configured else "not_configured",
                "status": "configured" if settings.human_handoff_webhook_configured else "not_configured",
                "description": "Signed handoff payloads to the support system of record.",
            },
            {
                "connector": "ai_reasoning",
                "category": "ai",
                "mode": "live" if settings.llm_enabled else "not_configured",
                "status": "configured" if settings.llm_enabled else "not_configured",
                "description": "Server-side reasoning for triage, evidence analysis, and recommendations.",
            },
        ],
        "rules": [
            "Provider credentials remain server-side.",
            "Unconfigured providers never return generated records.",
            "All money-moving decisions require an explicit review policy.",
        ],
    }
