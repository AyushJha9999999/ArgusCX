"""
ArgusCX — Redis Connection
Uses redis-py async client; all config from environment variables.
"""
import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

redis_client: aioredis.Redis | None = None


async def init_redis():
    global redis_client

    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await redis_client.ping()
        logger.info("✅ Redis connected", url=settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL)
    except Exception as exc:
        logger.warning(
            "⚠️  Redis not reachable — running without cache (demo mode)",
            error=str(exc),
        )
        redis_client = None


def get_redis() -> aioredis.Redis | None:
    """Return the active Redis client or None in demo mode."""
    return redis_client


async def close_redis():
    if redis_client:
        await redis_client.aclose()
        logger.info("🛑 Redis connection closed")
