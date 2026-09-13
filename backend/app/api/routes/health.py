"""ArgusCX — Health Check Routes"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.APP_ENV, "demo_mode": settings.is_demo_mode}

@router.get("/health/ready")
async def readiness():
    return {"status": "ready"}

@router.get("/health/live")
async def liveness():
    return {"status": "alive"}
