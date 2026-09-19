"""
ArgusCX — API Key Authentication Middleware
Validates X-ArgusCX-Key header on all /api/v1/ routes.
Skips auth for health, docs, and the root endpoint.
"""
from datetime import datetime
from typing import Dict
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import structlog
import time

logger = structlog.get_logger(__name__)

# Simple in-memory rate limiter
_rate_limiter: Dict[str, list] = {}  # key -> list of timestamps


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that validates API keys on protected routes."""

    # Routes that don't require authentication
    EXEMPT_PATHS = {
        "/", "/docs", "/redoc", "/openapi.json", "/metrics",
        "/api/v1/health", "/api/v1/health/",
        "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/firebase",
        "/api/v1/onboarding/assessment",
    }
    EXEMPT_PREFIXES = ("/ws/", "/docs", "/redoc")
    # Email action links are self-contained (HMAC-signed tokens) — no API key needed
    EXEMPT_SUFFIXES = ("/email-action",)

    @staticmethod
    async def _has_valid_session_token(request: Request) -> bool:
        """Allow a customer to access only their own verification session."""
        if request.method not in {"GET", "POST"}:
            return False
        parts = request.url.path.strip("/").split("/")
        # /api/v1/sessions/{session_id}[/complete]
        if len(parts) not in {4, 5} or parts[:3] != ["api", "v1", "sessions"]:
            return False
        if len(parts) == 5 and parts[4] != "complete":
            return False

        token = request.headers.get("X-Session-Token") or request.query_params.get("token")
        if not token:
            return False
            
        from app.db.mongodb import get_sessions_col
        sessions_col = get_sessions_col()
        if sessions_col is None:
            return False
            
        session = await sessions_col.find_one({"id": parts[3]})
        expected = session.get("session_token") if session else None
        return bool(expected and secrets.compare_digest(token, expected))

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Let CORSMiddleware handle browser preflight requests before auth.
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for exempt routes
        if path in self.EXEMPT_PATHS:
            return await call_next(request)
        for prefix in self.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)
        for suffix in self.EXEMPT_SUFFIXES:
            if path.endswith(suffix):
                return await call_next(request)

        if await self._has_valid_session_token(request):
            request.state.auth_type = "verification_session"
            return await call_next(request)

        # Skip auth for non-API routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # Check for API key
        api_key = request.headers.get("X-ArgusCX-Key") or request.headers.get("x-arguscx-key")

        # Also accept Bearer token
        if not api_key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]

                from app.api.routes.auth import decode_access_token
                identity = decode_access_token(api_key)
                if identity:
                    request.state.authenticated_user = identity
                    request.state.auth_type = "dashboard_jwt"
                    return await call_next(request)

        # Also accept query parameter for easy testing
        if not api_key:
            api_key = request.query_params.get("api_key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Missing API key",
                    "detail": "Include your ArgusCX API key in the X-ArgusCX-Key header.",
                    "docs": "/docs",
                },
            )

        # Validate the key
        from app.api.routes.api_keys import validate_api_key, validate_api_key_db
        record = await validate_api_key_db(api_key)
        if not record:
            record = validate_api_key(api_key)

        if not record:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid API key",
                    "detail": "The provided API key is invalid or has been revoked.",
                },
            )

        # Rate limiting
        now = time.time()
        key_id = record.key_id
        if key_id not in _rate_limiter:
            _rate_limiter[key_id] = []

        # Clean old entries (older than 60 seconds)
        _rate_limiter[key_id] = [t for t in _rate_limiter[key_id] if now - t < 60]

        if len(_rate_limiter[key_id]) >= record.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {record.rate_limit_per_minute} requests per minute.",
                    "retry_after_seconds": 60,
                },
            )

        _rate_limiter[key_id].append(now)

        # Attach company info to request state
        request.state.company_name = record.company_name
        request.state.key_id = record.key_id
        request.state.auth_type = "api_key"

        return await call_next(request)
