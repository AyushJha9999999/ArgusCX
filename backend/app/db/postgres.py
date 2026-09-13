"""
ArgusCX — PostgreSQL Database Connection
Uses SQLAlchemy async engine; all config from environment variables.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

engine = None
AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass


async def init_db():
    global engine, AsyncSessionLocal

    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.APP_DEBUG,
            future=True,
        )
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        # Verify connectivity
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute(__import__("sqlalchemy").text("SELECT 1")))
        logger.info("✅ PostgreSQL connected", url=settings.DATABASE_URL.split("@")[-1])
    except Exception as exc:
        logger.warning(
            "⚠️  PostgreSQL not reachable — running without DB (demo mode)",
            error=str(exc),
        )
        engine = None
        AsyncSessionLocal = None


async def get_db():
    """Dependency — yields an async DB session."""
    if AsyncSessionLocal is None:
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    if engine:
        await engine.dispose()
        logger.info("🛑 PostgreSQL connection closed")
