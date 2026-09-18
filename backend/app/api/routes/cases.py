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

from app.db.mongodb import get_cases_col, get_sessions_col

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
    cases_col = get_cases_col()
    sessions_col = get_sessions_col()
    if cases_col is None or sessions_col is None:
        return {"total": 0, "cases": [], "limit": limit, "offset": offset}
        
    query = {}
    if state:
        query["state"] = state.upper()
        
    total = await cases_col.count_documents(query)
    cursor = cases_col.find(query).skip(offset).limit(limit)
    page = await cursor.to_list(length=limit)
    
    # Enrich with session info
    enriched = []
    for c in page:
        sid = c.get("session_id")
        sess = await sessions_col.find_one({"id": sid}) or {}
        enriched.append({
            **c,
            "_id": str(c.get("_id")) if c.get("_id") else None,
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
    cases_col = get_cases_col()
    sessions_col = get_sessions_col()
    if cases_col is None or sessions_col is None:
        raise HTTPException(status_code=500, detail="Database not available")
        
    case = await cases_col.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if "_id" in case:
        case["_id"] = str(case["_id"])
        
    sid = case.get("session_id")
    session = await sessions_col.find_one({"id": sid}) or {}
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
    cases_col = get_cases_col()
    if cases_col is None:
        raise HTTPException(status_code=500, detail="Database not available")
        
    case = await cases_col.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    valid_decisions = {"APPROVED", "REJECTED", "ESCALATED"}
    if req.decision.upper() not in valid_decisions:
        raise HTTPException(status_code=422, detail=f"Decision must be one of {valid_decisions}")
        
    update = {
        "reviewer_id": req.reviewer_id,
        "reviewer_decision": req.decision.upper(),
        "reviewer_notes": req.notes,
        "reviewed_at": datetime.utcnow().isoformat()
    }
    await cases_col.update_one({"id": case_id}, {"$set": update})
    
    logger.info("Case reviewed", case_id=case_id, decision=req.decision, reviewer=req.reviewer_id)
    return {"message": "Review recorded", "case_id": case_id, "decision": req.decision.upper()}


@router.post("/{case_id}/escalate")
async def escalate_case(case_id: str, reason: Optional[str] = None):
    """Force a case to REVIEW_REQUIRED state."""
    cases_col = get_cases_col()
    if cases_col is None:
        raise HTTPException(status_code=500, detail="Database not available")
        
    case = await cases_col.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    update = {
        "state": "REVIEW_REQUIRED",
        "routing": "REVIEW_REQUIRED",
    }
    if reason:
        update["reasoning_narrative"] = (case.get("reasoning_narrative") or "") + f" [Escalated: {reason}]"
        
    await cases_col.update_one({"id": case_id}, {"$set": update})
    return {"message": "Case escalated", "case_id": case_id, "state": "REVIEW_REQUIRED"}
