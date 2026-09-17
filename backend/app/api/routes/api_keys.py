"""
ArgusCX — API Key Management
Allows companies to generate, list, and revoke ArgusCX API keys.
Companies integrate by passing X-ArgusCX-Key header in all requests.
"""
import secrets
import time
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import structlog
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api-keys")

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

# Pre-seed a master key and demo keys for dashboard/testing
_MASTER_KEY = settings.ARGUSCX_MASTER_KEY
for key in set([_MASTER_KEY, "acx_live_demo_key_2026", "acx_master_2026_hackathon"]):
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


@router.post("", response_model=CreateKeyResponse)
async def create_api_key(request: CreateKeyRequest):
    """Generate a new ArgusCX API key for a company."""
    api_key = generate_api_key()
    key_id = f"key_{secrets.token_hex(8)}"

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
        company_name=request.company_name,
        created_at=record.created_at,
        rate_limit_per_minute=request.rate_limit_per_minute,
    )


@router.get("", response_model=List[KeyInfo])
async def list_api_keys():
    """List all API keys (without revealing the full key)."""
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
        )
        for r in _api_keys.values()
    ]


@router.delete("/{key_id}")
async def revoke_api_key(key_id: str):
    """Revoke an API key."""
    for key, record in _api_keys.items():
        if record.key_id == key_id:
            record.is_active = False
            logger.info("API key revoked", key_id=key_id)
            return {"message": f"API key {key_id} revoked", "key_id": key_id}
    raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
