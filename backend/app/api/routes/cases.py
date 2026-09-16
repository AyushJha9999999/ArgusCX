"""
ArgusCX -- Cases API

GET  /api/v1/cases           List cases
GET  /api/v1/cases/{id}      Full case detail
POST /api/v1/cases/{id}/review       Reviewer decision
POST /api/v1/cases/{id}/escalate     Force escalation
"""
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from app.api.routes.sessions import _cases, _sessions

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/cases")


class ReviewRequest(BaseModel):
    reviewer_id: str
    decision: str           # APPROVED | REJECTED | ESCALATED
    notes: Optional[str] = None


@router.get("")
async def list_cases(
    state: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all cases, optionally filtered by state."""
    all_cases = list(_cases.values())
    if state:
        all_cases = [c for c in all_cases if c.get("state") == state.upper()]
    total = len(all_cases)
    page = all_cases[offset:offset + limit]
    # Enrich with session info
    enriched = []
    for c in page:
        sid = c.get("session_id")
        sess = _sessions.get(sid, {})
        enriched.append({
            **c,
            "order_id": sess.get("order_id"),
            "customer_ref": sess.get("customer_ref"),
            "category": sess.get("category"),
            "assurance_level": sess.get("assurance_level"),
            "created_at": sess.get("created_at"),
        })
    return {"total": total, "cases": enriched, "limit": limit, "offset": offset}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Full case report with all signals and evidence."""
    case = next((c for c in _cases.values() if c.get("id") == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    sid = case.get("session_id")
    session = _sessions.get(sid, {})
    return {
        **case,
        "session": {
            "id": sid,
            "order_id": session.get("order_id"),
            "customer_ref": session.get("customer_ref"),
            "claim_text": session.get("claim_text"),
            "return_reason": session.get("return_reason"),
            "category": session.get("category"),
            "expected_serial": session.get("expected_serial"),
            "assurance_level": session.get("assurance_level"),
            "challenges": session.get("challenge_sequence", []),
            "evidence_ids": session.get("evidence_ids", []),
            "created_at": session.get("created_at"),
        },
    }


@router.post("/{case_id}/review")
async def review_case(case_id: str, req: ReviewRequest):
    """Reviewer submits a decision on a case."""
    case = next((c for c in _cases.values() if c.get("id") == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    valid_decisions = {"APPROVED", "REJECTED", "ESCALATED"}
    if req.decision.upper() not in valid_decisions:
        raise HTTPException(status_code=422, detail=f"Decision must be one of {valid_decisions}")
    case["reviewer_id"] = req.reviewer_id
    case["reviewer_decision"] = req.decision.upper()
    case["reviewer_notes"] = req.notes
    case["reviewed_at"] = datetime.utcnow().isoformat()
    logger.info("Case reviewed", case_id=case_id, decision=req.decision, reviewer=req.reviewer_id)
    return {"message": "Review recorded", "case_id": case_id, "decision": req.decision.upper()}


@router.post("/{case_id}/escalate")
async def escalate_case(case_id: str, reason: Optional[str] = None):
    """Force a case to REVIEW_REQUIRED state."""
    case = next((c for c in _cases.values() if c.get("id") == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case["state"] = "REVIEW_REQUIRED"
    case["routing"] = "REVIEW_REQUIRED"
    if reason:
        case["reasoning_narrative"] = (case.get("reasoning_narrative") or "") + f" [Escalated: {reason}]"
    return {"message": "Case escalated", "case_id": case_id, "state": "REVIEW_REQUIRED"}
