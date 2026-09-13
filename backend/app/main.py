"""
ArgusCX Backend — FastAPI Entry Point
Autonomous AI Customer Support System
"""
import os
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import tickets, agents, analytics, knowledge, evidence, health, auth
from app.api.websockets import ticket_ws
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.postgres import init_db, close_db
from app.db.mongodb import init_mongo, close_mongo
from app.db.redis_client import init_redis, close_redis
from app.rag.indexer import init_rag_index

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 ArgusCX starting up...", version=settings.APP_VERSION)

    # Initialize databases (graceful — won't crash if DB is unavailable in demo mode)
    await init_db()
    await init_mongo()
    await init_redis()

    # Initialize RAG index with sample knowledge base
    await init_rag_index()

    logger.info("✅ ArgusCX ready", env=settings.APP_ENV)
    yield

    # Graceful shutdown
    logger.info("🛑 ArgusCX shutting down...")
    await close_db()
    await close_mongo()
    await close_redis()


# ─────────────────────────────────────────────
#  Sentry (Error Tracking)
# ─────────────────────────────────────────────
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    )

# ─────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────
setup_logging()

# ─────────────────────────────────────────────
#  FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(
    title="ArgusCX API",
    description="Autonomous AI Customer Support System — Multi-Agent Investigation Engine",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────
#  Middleware
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─────────────────────────────────────────────
#  Prometheus Metrics
# ─────────────────────────────────────────────
if settings.METRICS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ─────────────────────────────────────────────
#  Routers
# ─────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(auth.router, prefix=API_PREFIX, tags=["Auth"])
app.include_router(tickets.router, prefix=API_PREFIX, tags=["Tickets"])
app.include_router(agents.router, prefix=API_PREFIX, tags=["Agents"])
app.include_router(analytics.router, prefix=API_PREFIX, tags=["Analytics"])
app.include_router(knowledge.router, prefix=API_PREFIX, tags=["Knowledge Base"])
app.include_router(evidence.router, prefix=API_PREFIX, tags=["Evidence & Fraud"])

# WebSocket
app.include_router(ticket_ws.router, tags=["WebSocket"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "ArgusCX API",
        "version": settings.APP_VERSION,
        "tagline": "The Support System That Investigates, Not Just Answers",
        "docs": "/docs",
        "status": "operational",
    }
