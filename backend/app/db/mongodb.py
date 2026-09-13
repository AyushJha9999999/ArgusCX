"""
ArgusCX — MongoDB Connection
Uses Motor async driver; all config from environment variables.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

mongo_client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None


async def init_mongo():
    global mongo_client, mongo_db

    try:
        # Build URI with auth if provided
        uri = settings.MONGO_URI
        if settings.MONGO_USER and settings.MONGO_PASSWORD:
            # Replace protocol with credentials
            proto, rest = uri.split("://", 1)
            uri = f"{proto}://{settings.MONGO_USER}:{settings.MONGO_PASSWORD}@{rest}"
            if settings.MONGO_AUTH_SOURCE:
                sep = "&" if "?" in uri else "?"
                uri = f"{uri}{sep}authSource={settings.MONGO_AUTH_SOURCE}"

        mongo_client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        mongo_db = mongo_client[settings.MONGO_DB]
        # Verify connectivity
        await mongo_client.admin.command("ping")
        logger.info("✅ MongoDB connected", db=settings.MONGO_DB)
    except Exception as exc:
        logger.warning(
            "⚠️  MongoDB not reachable — running without it (demo mode)",
            error=str(exc),
        )
        mongo_client = None
        mongo_db = None


def get_mongo_db() -> AsyncIOMotorDatabase | None:
    """Return the active MongoDB database or None in demo mode."""
    return mongo_db


async def close_mongo():
    if mongo_client:
        mongo_client.close()
        logger.info("🛑 MongoDB connection closed")


# Allow Settings to expose MONGO_AUTH_SOURCE — add it as a fallback attr
try:
    _ = settings.MONGO_AUTH_SOURCE
except AttributeError:
    pass  # handled gracefully above
