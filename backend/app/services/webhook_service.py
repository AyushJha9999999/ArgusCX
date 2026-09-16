"""
ArgusCX -- Webhook Service
HMAC-SHA256 signed webhook delivery (Shopify-style pattern).
"""
import hashlib
import hmac
import json
import secrets
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)
TIMEOUT_SECONDS = 15


def generate_webhook_secret() -> str:
    return secrets.token_hex(32)


def sign_payload(secret: str, payload: str) -> str:
    """Returns sha256=<hex> HMAC signature over payload body."""
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={sig}"


def verify_signature(secret: str, payload: str, provided_sig: str) -> bool:
    return hmac.compare_digest(sign_payload(secret, payload), provided_sig)


async def deliver_webhook(
    url: str,
    secret: str,
    event: str,
    payload: Dict[str, Any],
    attempt: int = 1,
) -> bool:
    body = json.dumps(payload, default=str)
    signature = sign_payload(secret, body)
    headers = {
        "Content-Type": "application/json",
        "X-ArgusCX-Signature": signature,
        "X-ArgusCX-Event": event,
        "X-ArgusCX-Delivery-Id": secrets.token_hex(16),
        "X-ArgusCX-Attempt": str(attempt),
        "User-Agent": "ArgusCX-Webhook/1.0",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(url, content=body, headers=headers)
            ok = 200 <= resp.status_code < 300
            if ok:
                logger.info("Webhook delivered", url=url, event=event, status=resp.status_code)
            else:
                logger.warning("Webhook failed", url=url, event=event, status=resp.status_code)
            return ok
    except Exception as exc:
        logger.error("Webhook exception", url=url, error=str(exc), attempt=attempt)
        return False


def build_verification_completed_payload(
    session_id: str,
    order_id: Optional[str],
    case_state: str,
    routing: str,
    risk_signals: Dict[str, Any],
    reasoning_narrative: Optional[str],
    evidence_manifest_hash: Optional[str],
    case_url: str,
) -> Dict[str, Any]:
    return {
        "event": "verification.completed",
        "api_version": "2024-09",
        "session_id": session_id,
        "order_id": order_id,
        "case_state": case_state,
        "routing": routing,
        "risk_signals": risk_signals,
        "reasoning_narrative": reasoning_narrative,
        "evidence_manifest_hash": evidence_manifest_hash,
        "case_url": case_url,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
