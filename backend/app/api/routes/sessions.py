"""
ArgusCX -- Verification Session API

POST /api/v1/sessions                  Create a verification session
GET  /api/v1/sessions/{id}             Session status
GET  /api/v1/sessions/{id}/result      Full case report
POST /api/v1/sessions/{id}/complete    Mark session completed (from capture UI)
POST /api/v1/sessions/{id}/outbound-evidence  Upload warehouse photos
GET  /api/v1/sessions/{id}/qr          QR code for mobile redirect
"""
import secrets
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from app.services.challenge_generator import (
    generate_session_nonce,
    generate_challenge_sequence,
    ChallengeStep,
    DEFAULT_CHALLENGE_COUNT,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/sessions")

SESSION_TTL_MINUTES = 30

# ---- In-memory store (upgrade to DB when PostgreSQL connected) ----
_sessions: Dict[str, dict] = {}
_cases: Dict[str, dict] = {}


# ──────────────────────────────────────────────
#  REQUEST / RESPONSE SCHEMAS
# ──────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    order_id: Optional[str] = None
    customer_ref: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    expected_serial: Optional[str] = None
    claim_text: Optional[str] = None
    return_reason: Optional[str] = None
    challenge_count: int = Field(DEFAULT_CHALLENGE_COUNT, ge=3, le=10)
    require_serial_challenge: bool = True
    require_packaging_challenge: bool = False
    metadata: Dict[str, Any] = {}


class ChallengeInfo(BaseModel):
    step_index: int
    challenge_type: str
    instruction_text: str
    required_action: str


class SessionCreateResponse(BaseModel):
    session_id: str
    capture_url: str
    session_token: str
    expires_at: str
    challenge_count: int
    challenges: List[ChallengeInfo]
    qr_code_url: str
    status: str


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    order_id: Optional[str]
    assurance_level: str
    challenges_total: int
    challenges_completed: int
    created_at: str
    expires_at: str
    completed_at: Optional[str]


class SessionCompleteRequest(BaseModel):
    assurance_level: str = "live_video"
    evidence_ids: List[str] = []


class OutboundEvidenceRequest(BaseModel):
    urls: List[str] = Field(..., min_items=1, max_items=10)


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def _generate_session_token(session_id: str) -> str:
    return f"ses_tok_{secrets.token_hex(24)}"


def _build_capture_url(session_id: str, base_url: str = "http://localhost:3000") -> str:
    return f"{base_url}/verify/{session_id}"


def _generate_qr_b64(url: str) -> str:
    try:
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


# ──────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────

@router.post("", response_model=SessionCreateResponse, status_code=201)
async def create_session(req: SessionCreateRequest, request: Request):
    """Create a verification session and return the capture URL + QR code."""
    nonce = generate_session_nonce()
    session_id = f"ses_{secrets.token_hex(10)}"
    session_token = _generate_session_token(session_id)
    expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)

    challenges = generate_challenge_sequence(
        nonce=nonce,
        count=req.challenge_count,
        require_serial=req.require_serial_challenge,
        require_packaging=req.require_packaging_challenge,
    )

    # Determine base URL from request
    base = str(request.base_url).rstrip("/").replace(":8000", ":3000")
    capture_url = _build_capture_url(session_id, base)

    session = {
        "id": session_id,
        "order_id": req.order_id,
        "customer_ref": req.customer_ref,
        "sku": req.sku,
        "category": req.category,
        "expected_serial": req.expected_serial,
        "claim_text": req.claim_text,
        "return_reason": req.return_reason,
        "status": "pending",
        "assurance_level": "unknown",
        "nonce": nonce,
        "session_token": session_token,
        "challenge_sequence": [c.dict() for c in challenges],
        "challenges_completed": 0,
        "evidence_ids": [],
        "outbound_evidence_urls": [],
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "metadata": req.metadata,
    }
    _sessions[session_id] = session

    logger.info("Session created", session_id=session_id, order_id=req.order_id)

    return SessionCreateResponse(
        session_id=session_id,
        capture_url=capture_url,
        session_token=session_token,
        expires_at=expires_at.isoformat(),
        challenge_count=len(challenges),
        challenges=[ChallengeInfo(**c.dict()) for c in challenges],
        qr_code_url=f"/api/v1/sessions/{session_id}/qr",
        status="pending",
    )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session(session_id: str):
    """Get session status."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionStatusResponse(
        session_id=session_id,
        status=session["status"],
        order_id=session.get("order_id"),
        assurance_level=session["assurance_level"],
        challenges_total=len(session.get("challenge_sequence", [])),
        challenges_completed=session.get("challenges_completed", 0),
        created_at=session["created_at"],
        expires_at=session["expires_at"],
        completed_at=session.get("completed_at"),
    )


@router.get("/{session_id}/result")
async def get_session_result(session_id: str):
    """Get the full case report for a completed session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] not in ("completed", "analysed"):
        raise HTTPException(
            status_code=202,
            detail={"message": "Analysis in progress", "status": session["status"]}
        )
    case = _cases.get(session_id)
    return {
        "session_id": session_id,
        "status": session["status"],
        "case": case,
        "challenges": session.get("challenge_sequence", []),
        "evidence_ids": session.get("evidence_ids", []),
    }


@router.post("/{session_id}/complete")
async def complete_session(
    session_id: str,
    req: SessionCompleteRequest,
    background_tasks: BackgroundTasks,
):
    """
    Called by the capture UI when all challenges are done.
    Triggers async analysis pipeline.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] not in ("pending", "in_progress"):
        raise HTTPException(status_code=409, detail=f"Session already {session['status']}")

    # Check expiry
    if datetime.utcnow().isoformat() > session["expires_at"]:
        session["status"] = "expired"
        raise HTTPException(status_code=410, detail="Session has expired")

    session["status"] = "analysing"
    session["assurance_level"] = req.assurance_level
    session["evidence_ids"] = req.evidence_ids
    session["completed_at"] = datetime.utcnow().isoformat()

    # Trigger async analysis
    background_tasks.add_task(_run_analysis_pipeline, session_id)

    return {"message": "Analysis started", "session_id": session_id, "status": "analysing"}


@router.post("/{session_id}/outbound-evidence")
async def upload_outbound_evidence(session_id: str, req: OutboundEvidenceRequest):
    """Merchant uploads warehouse/outbound photos for comparison."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["outbound_evidence_urls"] = req.urls
    return {"message": "Outbound evidence recorded", "count": len(req.urls)}


@router.get("/{session_id}/qr")
async def get_session_qr(session_id: str, request: Request):
    """Return a QR code image (base64 PNG) linking to the capture URL."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    base = str(request.base_url).rstrip("/").replace(":8000", ":3000")
    capture_url = _build_capture_url(session_id, base)
    qr_b64 = _generate_qr_b64(capture_url)
    return {
        "session_id": session_id,
        "capture_url": capture_url,
        "qr_code_data_uri": qr_b64,
    }


# ──────────────────────────────────────────────
#  ANALYSIS PIPELINE (stub -- workers plug in here)
# ──────────────────────────────────────────────

async def _run_analysis_pipeline(session_id: str):
    """
    Orchestrate the full analysis pipeline for a session.
    In production: Celery chord/group coordinates parallel workers.
    For demo: runs sequentially in background task.
    """
    session = _sessions.get(session_id)
    if not session:
        return

    logger.info("Analysis pipeline started", session_id=session_id)

    try:
        from app.services.risk_engine import (
            compute_risk_signals, determine_case_state, build_case,
        )
        from app.services.manifest_service import build_manifest

        # === Stub signal data (workers fill real data in production) ===
        forensic_findings = []
        screen_replay_findings = []
        challenge_completion_ratio = (
            session.get("challenges_completed", 0) /
            max(len(session.get("challenge_sequence", [])), 1)
        )
        product_identity = None
        damage_finding = None
        evidence_reuse = None
        llm_reasoning = None
        outbound_comparison = None

        # === Run risk engine ===
        signals = compute_risk_signals(
            forensic_findings=forensic_findings,
            screen_replay_findings=screen_replay_findings,
            challenge_completion_ratio=challenge_completion_ratio,
            product_identity=product_identity,
            damage_finding=damage_finding,
            evidence_reuse=evidence_reuse,
            llm_reasoning=llm_reasoning,
            outbound_comparison=outbound_comparison,
            assurance_level=session["assurance_level"],
            policy=session.get("policy_json", {}),
        )

        state, routing, reasoning_prefix = determine_case_state(signals, session.get("policy_json", {}))

        case = build_case(
            session_id=session_id,
            tenant_id="demo_tenant",
            signals=signals,
            state=state,
            routing=routing,
            reasoning_prefix=reasoning_prefix,
            llm_narrative=None,
            claim_assertions=[],
            contradictions=[],
        )
        case["id"] = f"cas_{secrets.token_hex(8)}"
        _cases[session_id] = case

        # Build manifest
        evidence_hashes = session.get("evidence_ids", [])
        manifest = build_manifest(session_id, evidence_hashes, {"signals": signals})
        case["manifest_hash"] = manifest["manifest_hash"]

        session["status"] = "completed"
        logger.info("Analysis complete", session_id=session_id, state=state, routing=routing)

    except Exception as exc:
        logger.error("Analysis pipeline failed", session_id=session_id, error=str(exc))
        session["status"] = "completed"
        _cases[session_id] = {
            "id": f"cas_{secrets.token_hex(8)}",
            "session_id": session_id,
            "state": "REVIEW_REQUIRED",
            "routing": "REVIEW_REQUIRED",
            "risk_signals_json": {},
            "reasoning_narrative": f"Analysis pipeline error: {exc}",
            "claim_assertions_json": [],
            "contradictions_json": [],
        }
