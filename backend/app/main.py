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
from fastapi.openapi.utils import get_openapi
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import tickets, agents, analytics, knowledge, evidence, health, auth, api_keys, sessions, cases, onboarding, integrations, handoffs, channels
from app.api.websockets import ticket_ws
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.api_key_middleware import APIKeyMiddleware
from app.db.postgres import init_db, close_db
from app.db.mongodb import init_mongo, close_mongo
from app.rag.indexer import init_rag_index

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 ArgusCX starting up...", version=settings.APP_VERSION)

    # Initialize databases (graceful — won't crash if DB is unavailable)
    await init_db()
    await init_mongo()

    # Initialize RAG index with knowledge base
    await init_rag_index()

    logger.info(
        "✅ ArgusCX ready",
        env=settings.APP_ENV,
        llm_provider=settings.active_llm_provider,
        configured_connectors=settings.active_connectors,
    )
    yield

    # Graceful shutdown
    logger.info("🛑 ArgusCX shutting down...")
    await close_db()
    await close_mongo()


# ─────────────────────────────────────────────
#  Sentry (Error Tracking)
# ─────────────────────────────────────────────
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
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
    summary="Investigate support cases before resolving them",
    description="""
ArgusCX is an investigation-first customer support platform.

Use this API to submit support cases, attach evidence, inspect agent reasoning,
resolve cases with a human override, and consume analytics. All protected
endpoints require the `X-ArgusCX-Key` header. The OpenAPI Authorize button
accepts an ArgusCX platform key.

**Integration model:** ArgusCX receives your customer case and uses provider
credentials configured on the server to read order, payment, and customer data.
Provider secrets are never sent from a browser or included in ticket payloads.
""",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={"name": "ArgusCX Platform", "email": "platform@arguscx.local"},
    license_info={"name": "Proprietary - ArgusCX Platform"},
    openapi_tags=[
        {"name": "Root", "description": "Service metadata and capability discovery."},
        {"name": "Health", "description": "Unauthenticated liveness and readiness checks."},
        {"name": "Tickets", "description": "Submit, search, inspect, and human-resolve support cases."},
        {"name": "Evidence & Fraud", "description": "Upload and inspect customer evidence."},
        {"name": "Agents", "description": "Inspect the specialist agent roster."},
        {"name": "Analytics", "description": "Operational, resolution, and fraud metrics."},
        {"name": "Knowledge Base", "description": "Search policy and support knowledge."},
        {"name": "API Keys", "description": "Create and revoke platform keys for integrations."},
        {"name": "Auth", "description": "Dashboard authentication endpoints."},
        {"name": "WebSocket", "description": "Real-time ticket lifecycle events."},
    ],
)

# ─────────────────────────────────────────────
#  Middleware (order matters — last added = first executed)
# ─────────────────────────────────────────────
app.add_middleware(APIKeyMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Prometheus Metrics
# ─────────────────────────────────────────────
if settings.METRICS_ENABLED:
    pass

# ─────────────────────────────────────────────
#  Routers
# ─────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(auth.router, prefix=API_PREFIX, tags=["Auth"])
app.include_router(api_keys.router, prefix=API_PREFIX, tags=["API Keys"])
app.include_router(tickets.router, prefix=API_PREFIX, tags=["Tickets"])
app.include_router(agents.router, prefix=API_PREFIX, tags=["Agents"])
app.include_router(analytics.router, prefix=API_PREFIX, tags=["Analytics"])
app.include_router(knowledge.router, prefix=API_PREFIX, tags=["Knowledge Base"])
app.include_router(evidence.router, prefix=API_PREFIX, tags=["Evidence & Fraud"])
app.include_router(sessions.router, prefix=API_PREFIX, tags=["Sessions"])
app.include_router(cases.router, prefix=API_PREFIX, tags=["Cases"])
app.include_router(onboarding.router, prefix=API_PREFIX, tags=["Onboarding"])
app.include_router(integrations.router, prefix=API_PREFIX, tags=["Integrations"])
app.include_router(handoffs.router, prefix=API_PREFIX, tags=["Human Handoffs"])
app.include_router(channels.router, prefix=API_PREFIX, tags=["Support Channels"])

# WebSocket
app.include_router(ticket_ws.router, tags=["WebSocket"])


def custom_openapi():
    """Expose the middleware authentication contract in generated API docs."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        summary=app.summary,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        contact=app.contact,
        license_info=app.license_info,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["ArgusCXKey"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-ArgusCX-Key",
        "description": "Platform key generated by POST /api/v1/api-keys. Keep it server-side.",
    }
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Dashboard/session token. Provider API keys are not bearer tokens.",
    }
    for path, operations in schema.get("paths", {}).items():
        if path.startswith("/api/v1/") and path not in {
            "/api/v1/health", "/api/v1/health/live", "/api/v1/health/ready",
            "/api/v1/auth/login", "/api/v1/auth/logout",
        }:
            for operation in operations.values():
                if isinstance(operation, dict):
                    operation["security"] = [{"ArgusCXKey": []}, {"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "ArgusCX API",
        "version": settings.APP_VERSION,
        "tagline": "The Support System That Investigates, Not Just Answers",
        "docs": "/docs",
        "status": "operational",
        "llm_provider": settings.active_llm_provider,
        "features": {
            "multi_agent_orchestration": True,
            "local_forensics": True,
            "semantic_rag": True,
            "guardrails": True,
            "preprocessor": True,
            "api_key_auth": True,
        },
    }
