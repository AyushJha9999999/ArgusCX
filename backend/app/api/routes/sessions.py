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

from app.core.config import settings
from app.services.challenge_generator import (
    generate_session_nonce,
    generate_challenge_sequence,
    ChallengeStep,
    DEFAULT_CHALLENGE_COUNT,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/sessions")

SESSION_TTL_MINUTES = 30

# Process-local operational store. The PostgreSQL models are the production
# persistence contract; this store keeps a local development process usable.
from app.db.mongodb import get_sessions_col, get_cases_col


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
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
    challenges: List[ChallengeInfo] = []


class SessionCompleteRequest(BaseModel):
    assurance_level: str = "live_video"
    evidence_ids: List[str] = []
    evidence_urls: List[str] = []


class OutboundEvidenceRequest(BaseModel):
    urls: List[str] = Field(..., min_items=1, max_items=10)


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def _generate_session_token(session_id: str) -> str:
    return f"ses_tok_{secrets.token_hex(24)}"


def _build_capture_url(session_id: str, session_token: str, base_url: str) -> str:
    """Return the customer capture link with its scoped session credential."""
    return f"{base_url}/verify/{session_id}?token={session_token}"


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
    identity = getattr(request.state, "key_id", None) or getattr(request.state, "authenticated_user", {})
    tenant_id = identity if isinstance(identity, str) else identity.get("sub")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="An authenticated platform or dashboard identity is required.")
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
    base = settings.DASHBOARD_BASE_URL or str(request.base_url).rstrip("/")
    capture_url = _build_capture_url(session_id, session_token, base)

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
        "tenant_id": tenant_id,
    }
    
    sessions_col = get_sessions_col()
    if sessions_col is not None:
        await sessions_col.insert_one(session)

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


@router.get("")
async def list_sessions(
    limit: int = 100,
    offset: int = 0,
):
    """List recent verification sessions for the operator dashboard."""
    bounded_limit = max(1, min(limit, 200))
    sessions_col = get_sessions_col()
    if sessions_col is None:
        return {"total": 0, "sessions": [], "limit": bounded_limit, "offset": offset}
        
    total_count = await sessions_col.count_documents({})
    cursor = sessions_col.find({}).sort("created_at", -1).skip(offset).limit(bounded_limit)
    page = await cursor.to_list(length=bounded_limit)
    
    return {
        "total": total_count,
        "sessions": [
            {
                "session_id": session["id"],
                "status": session["status"],
                "order_id": session.get("order_id"),
                "assurance_level": session["assurance_level"],
                "challenges_total": len(session.get("challenge_sequence", [])),
                "challenges_completed": session.get("challenges_completed", 0),
                "created_at": session["created_at"],
                "expires_at": session["expires_at"],
                "completed_at": session.get("completed_at"),
            }
            for session in page
        ],
        "limit": bounded_limit,
        "offset": offset,
    }


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session(session_id: str):
    """Get session status."""
    sessions_col = get_sessions_col()
    session = await sessions_col.find_one({"id": session_id}) if sessions_col is not None else None
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
        challenges=[ChallengeInfo(**challenge) for challenge in session.get("challenge_sequence", [])],
    )


@router.get("/{session_id}/result")
async def get_session_result(session_id: str):
    """Get the full case report for a completed session."""
    sessions_col = get_sessions_col()
    session = await sessions_col.find_one({"id": session_id}) if sessions_col is not None else None
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] not in ("completed", "analysed"):
        raise HTTPException(
            status_code=202,
            detail={"message": "Analysis in progress", "status": session["status"]}
        )
    cases_col = get_cases_col()
    case = await cases_col.find_one({"session_id": session_id}) if cases_col is not None else None
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
    sessions_col = get_sessions_col()
    session = await sessions_col.find_one({"id": session_id}) if sessions_col is not None else None
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
    session["evidence_urls"] = req.evidence_urls
    session["completed_at"] = datetime.utcnow().isoformat()

    await sessions_col.update_one(
        {"id": session_id},
        {"$set": {
            "status": "analysing",
            "assurance_level": req.assurance_level,
            "evidence_ids": req.evidence_ids,
            "evidence_urls": req.evidence_urls,
            "completed_at": session["completed_at"]
        }}
    )

    # Trigger async analysis
    background_tasks.add_task(_run_analysis_pipeline, session_id)

    return {"message": "Analysis started", "session_id": session_id, "status": "analysing"}


@router.post("/{session_id}/outbound-evidence")
async def upload_outbound_evidence(session_id: str, req: OutboundEvidenceRequest):
    """Merchant uploads warehouse/outbound photos for comparison."""
    sessions_col = get_sessions_col()
    session = await sessions_col.find_one({"id": session_id}) if sessions_col is not None else None
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await sessions_col.update_one(
        {"id": session_id},
        {"$set": {"outbound_evidence_urls": req.urls}}
    )
    return {"message": "Outbound evidence recorded", "count": len(req.urls)}


@router.get("/{session_id}/qr")
async def get_session_qr(session_id: str, request: Request):
    """Return a QR code image (base64 PNG) linking to the capture URL."""
    sessions_col = get_sessions_col()
    session = await sessions_col.find_one({"id": session_id}) if sessions_col is not None else None
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    base = settings.DASHBOARD_BASE_URL or str(request.base_url).rstrip("/")
    capture_url = _build_capture_url(session_id, session["session_token"], base)
    qr_b64 = _generate_qr_b64(capture_url)
    return {
        "session_id": session_id,
        "capture_url": capture_url,
        "qr_code_data_uri": qr_b64,
    }


# ──────────────────────────────────────────────
#  ANALYSIS PIPELINE
# ──────────────────────────────────────────────

async def _run_analysis_pipeline(session_id: str):
    """
    Orchestrate the full analysis pipeline for a session.
    The local runtime executes the configured analysis stages sequentially.
    A non-assessed evidence set is always routed to human review.
    """
    sessions_col = get_sessions_col()
    cases_col = get_cases_col()
    session = await sessions_col.find_one({"id": session_id}) if sessions_col is not None else None
    if not session:
        return

    logger.info("Analysis pipeline started", session_id=session_id)

    try:
        from app.services.risk_engine import (
            compute_risk_signals, determine_case_state, build_case,
        )
        from app.services.manifest_service import build_manifest

        # Evidence workers populate these collections when their output is
        # available. Empty values mean "not assessed", never "passed".
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
        if not session.get("evidence_ids"):
            state = "REVIEW_REQUIRED"
            routing = "REVIEW_REQUIRED"
            reasoning_prefix = "No evidence was submitted; operator review is required."

        case = build_case(
            session_id=session_id,
            tenant_id=session["tenant_id"],
            signals=signals,
            state=state,
            routing=routing,
            reasoning_prefix=reasoning_prefix,
            llm_narrative=None,
            claim_assertions=[],
            contradictions=[],
        )
        case["id"] = f"cas_{secrets.token_hex(8)}"
        await cases_col.insert_one(case)

        # Build manifest
        evidence_hashes = session.get("evidence_ids", [])
        manifest = build_manifest(session_id, evidence_hashes, {"signals": signals})
        case["manifest_hash"] = manifest["manifest_hash"]

        await sessions_col.update_one(
            {"id": session_id},
            {"$set": {"status": "completed"}}
        )
        logger.info("Analysis complete", session_id=session_id, state=state, routing=routing)

    except Exception as exc:
        logger.error("Analysis pipeline failed", session_id=session_id, error=str(exc))
        await sessions_col.update_one(
            {"id": session_id},
            {"$set": {"status": "review_required"}}
        )
        await cases_col.insert_one({
            "id": f"cas_{secrets.token_hex(8)}",
            "session_id": session_id,
            "state": "REVIEW_REQUIRED",
            "routing": "REVIEW_REQUIRED",
            "risk_signals_json": {},
            "reasoning_narrative": "Analysis could not complete; operator review is required.",
            "claim_assertions_json": [],
            "contradictions_json": [],
        })
