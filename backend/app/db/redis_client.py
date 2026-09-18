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

    if not settings.REDIS_URL:
        logger.info("Redis is not configured; cache and task queue features are disabled")
        return

    try:
        redis_url = settings.REDIS_URL.get_secret_value()
        redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await redis_client.ping()
        logger.info("✅ Redis connected", url=redis_url.split("@")[-1] if "@" in redis_url else redis_url)
    except Exception as exc:
        logger.warning(
            "Redis not reachable; cache and task queue features are unavailable",
            error=str(exc),
        )
        redis_client = None


def get_redis() -> aioredis.Redis | None:
    """Return the active Redis client when available."""
    return redis_client


async def close_redis():
    if redis_client:
        await redis_client.aclose()
        logger.info("🛑 Redis connection closed")
