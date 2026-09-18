"""
ArgusCX — API Key Management
Allows companies to generate, list, and revoke ArgusCX API keys.
Companies integrate by passing X-ArgusCX-Key header in all requests.
"""
import hashlib
import secrets
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy import select

import structlog
from app.core.config import settings
from app.db.postgres import AsyncSessionLocal
from app.models.db_models import ApiKey, Tenant

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api-keys")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ─────────────────────────────────────────────
#  In-Memory Key Store (production would use DB)
# ─────────────────────────────────────────────

class APIKeyRecord(BaseModel):
    key_id: str
    key_prefix: str  # First 8 chars for display (acx_live_xxxx...)
    hashed_key: str  # Full key stored
    company_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None
    rate_limit_per_minute: int = 60


# Global store
_api_keys: Dict[str, APIKeyRecord] = {}

# API keys are generated only through authenticated platform requests.
_MASTER_KEY = settings.ARGUSCX_MASTER_KEY.get_secret_value() if settings.ARGUSCX_MASTER_KEY else None
for key in filter(None, {_MASTER_KEY}):
    _api_keys[key] = APIKeyRecord(
        key_id=f"master_{key[:8]}",
        key_prefix="acx_mast",
        hashed_key=key,
        company_name="ArgusCX Dashboard",
        rate_limit_per_minute=1000,
    )


class CreateKeyRequest(BaseModel):
    company_name: str
    rate_limit_per_minute: int = 60


class CreateKeyResponse(BaseModel):
    key_id: str
    api_key: str  # Only shown once at creation
    client_id: str
    company_name: str
    created_at: datetime
    rate_limit_per_minute: int
    message: str = "Save this API key — it won't be shown again."


class KeyInfo(BaseModel):
    key_id: str
    key_prefix: str
    company_name: str
    created_at: datetime
    is_active: bool
    usage_count: int
    last_used: Optional[datetime]
    rate_limit_per_minute: int
    client_id: str
    revoked_at: Optional[datetime] = None


def generate_api_key() -> str:
    """Generate a unique ArgusCX API key."""
    token = secrets.token_hex(24)
    return f"acx_live_{token}"


def validate_api_key(key: str) -> Optional[APIKeyRecord]:
    """Validate an API key and return its record if valid."""
    record = _api_keys.get(key)
    if record and record.is_active:
        record.usage_count += 1
        record.last_used = datetime.utcnow()
        return record
    return None


async def validate_api_key_db(key: str) -> Optional[APIKeyRecord]:
    if AsyncSessionLocal is None:
        return None
    prefix = key[:12]
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True)))
        record = result.scalars().first()
        if not record or not pwd_context.verify(key, record.secret_hash):
            return None
        record.usage_count += 1
        record.last_used = datetime.utcnow()
        await session.commit()
        return APIKeyRecord(
            key_id=record.id,
            key_prefix=record.key_prefix,
            hashed_key="",
            company_name=record.company_name,
            rate_limit_per_minute=record.rate_limit_per_minute,
            usage_count=record.usage_count,
            last_used=record.last_used,
        )


@router.post("", response_model=CreateKeyResponse)
async def create_api_key(request: CreateKeyRequest, http_request: Request):
    """Generate a new ArgusCX API key for a company."""
    if getattr(http_request.state, "auth_type", None) != "dashboard_jwt":
        raise HTTPException(status_code=403, detail="Dashboard authentication is required to create API keys")
    api_key = generate_api_key()
    key_id = f"key_{secrets.token_hex(8)}"
    client_id = f"client_{secrets.token_urlsafe(12)}"

    if AsyncSessionLocal is not None:
        async with AsyncSessionLocal() as session:
            tenant = (await session.execute(select(Tenant).where(Tenant.id == "default_tenant"))).scalars().first()
            if not tenant:
                tenant = Tenant(id="default_tenant", name=request.company_name, api_key_hash="managed-by-api-keys")
                session.add(tenant)
            session.add(ApiKey(
                id=key_id,
                tenant_id=tenant.id,
                client_id=client_id,
                key_prefix=api_key[:12],
                secret_hash=pwd_context.hash(api_key),
                company_name=request.company_name,
                rate_limit_per_minute=request.rate_limit_per_minute,
            ))
            await session.commit()
    else:
        client_id = client_id

    record = APIKeyRecord(
        key_id=key_id,
        key_prefix=api_key[:12] + "...",
        hashed_key=api_key,
        company_name=request.company_name,
        rate_limit_per_minute=request.rate_limit_per_minute,
    )
    _api_keys[api_key] = record

    logger.info("API key created", key_id=key_id, company=request.company_name)

    return CreateKeyResponse(
        key_id=key_id,
        api_key=api_key,
        client_id=client_id,
        company_name=request.company_name,
        created_at=record.created_at,
        rate_limit_per_minute=request.rate_limit_per_minute,
    )


@router.get("", response_model=List[KeyInfo])
async def list_api_keys(http_request: Request):
    """List all API keys (without revealing the full key)."""
    if getattr(http_request.state, "auth_type", None) != "dashboard_jwt":
        raise HTTPException(status_code=403, detail="Dashboard authentication is required")
    if AsyncSessionLocal is not None:
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))).scalars().all()
            return [KeyInfo(
                key_id=r.id, key_prefix=r.key_prefix, client_id=r.client_id,
                company_name=r.company_name, created_at=r.created_at, is_active=r.is_active,
                usage_count=r.usage_count, last_used=r.last_used,
                rate_limit_per_minute=r.rate_limit_per_minute, revoked_at=r.revoked_at,
            ) for r in rows]
    return [
        KeyInfo(
            key_id=r.key_id,
            key_prefix=r.key_prefix,
            company_name=r.company_name,
            created_at=r.created_at,
            is_active=r.is_active,
            usage_count=r.usage_count,
            last_used=r.last_used,
            rate_limit_per_minute=r.rate_limit_per_minute,
            client_id=f"legacy_{r.key_id}",
        )
        for r in _api_keys.values()
    ]


@router.delete("/{key_id}")
async def revoke_api_key(key_id: str, http_request: Request):
    """Revoke an API key."""
    if getattr(http_request.state, "auth_type", None) != "dashboard_jwt":
        raise HTTPException(status_code=403, detail="Dashboard authentication is required")
    if AsyncSessionLocal is not None:
        async with AsyncSessionLocal() as session:
            row = (await session.execute(select(ApiKey).where(ApiKey.id == key_id))).scalars().first()
            if row:
                row.is_active = False
                row.revoked_at = datetime.utcnow()
                await session.commit()
                return {"message": f"API key {key_id} revoked", "key_id": key_id}
    for key, record in _api_keys.items():
        if record.key_id == key_id:
            record.is_active = False
            logger.info("API key revoked", key_id=key_id)
            return {"message": f"API key {key_id} revoked", "key_id": key_id}
    raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
