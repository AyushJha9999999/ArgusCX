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

    if not settings.MONGO_URI:
        logger.info("MongoDB is not configured; document persistence is disabled")
        return

    try:
        # Build URI with auth if provided
        uri = settings.MONGO_URI
        if settings.MONGO_USER and settings.MONGO_PASSWORD and "@" not in uri.split("://", 1)[-1]:
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
            "MongoDB not reachable; document persistence is unavailable",
            error=str(exc),
        )
        mongo_client = None
        mongo_db = None


def get_mongo_db() -> AsyncIOMotorDatabase | None:
    """Return the configured MongoDB database, when connected."""
    return mongo_db

def get_tickets_col():
    return mongo_db["tickets"] if mongo_db is not None else None

def get_sessions_col():
    return mongo_db["sessions"] if mongo_db is not None else None

def get_cases_col():
    return mongo_db["cases"] if mongo_db is not None else None

def get_users_col():
    """Returns the users/company-profiles collection."""
    return mongo_db["users"] if mongo_db is not None else None


async def setup_indexes():
    """Create indexes for the collections."""
    if mongo_db is None:
        return
    
    # Tickets
    await mongo_db["tickets"].create_index("id", unique=True)
    await mongo_db["tickets"].create_index("created_at")
    
    # Sessions
    await mongo_db["sessions"].create_index("id", unique=True)
    await mongo_db["sessions"].create_index("created_at")
    
    # Cases
    await mongo_db["cases"].create_index("id", unique=True)
    await mongo_db["cases"].create_index("session_id")
    
    # Users / Company Profiles
    await mongo_db["users"].create_index("sub", unique=True)
    await mongo_db["users"].create_index("email")


async def close_mongo():
    if mongo_client:
        mongo_client.close()
        logger.info("🛑 MongoDB connection closed")

# Allow Settings to expose MONGO_AUTH_SOURCE — add it as a fallback attr
try:
    _ = settings.MONGO_AUTH_SOURCE
except AttributeError:
    pass  # handled gracefully above
