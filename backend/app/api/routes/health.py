"""ArgusCX — Health Check Routes"""
from fastapi import APIRouter
from app.core.config import settings
from app.db.mongodb import get_mongo_db
from app.db import postgres

router = APIRouter()

@router.get("/health")
async def health():
    services = {
        "mongodb": "connected" if get_mongo_db() is not None else "not_connected",
        "postgres": "connected" if postgres.AsyncSessionLocal is not None else "not_connected",
        "llm": "configured" if settings.llm_enabled else "not_configured",
    }
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.APP_ENV, "services": services}

@router.get("/health/ready")
async def readiness():
    return {"status": "ready"}

@router.get("/health/live")
async def liveness():
    return {"status": "alive"}
