"""
ArgusCX -- Cases API

GET  /api/v1/cases                         List cases
GET  /api/v1/cases/{id}                    Full case detail
POST /api/v1/cases/{id}/review             Reviewer decision
POST /api/v1/cases/{id}/escalate           Force escalation
POST /api/v1/cases/{id}/analyse            AI vision analysis + email report
GET  /api/v1/cases/{id}/email-action       One-click Approve/Reject from email
"""
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import structlog

from app.core.config import settings
from app.db.mongodb import get_cases_col, get_sessions_col

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/cases")


class ReviewRequest(BaseModel):
    reviewer_id: str
    decision: str           # APPROVED | REJECTED | ESCALATED
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  LIST / GET
# ─────────────────────────────────────────────────────────────────────────────

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
            "evidence_urls": session.get("evidence_urls", []),
            "created_at": session.get("created_at"),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
#  REVIEW / ESCALATE
# ─────────────────────────────────────────────────────────────────────────────

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
        "reviewed_at": datetime.utcnow().isoformat(),
        "state": req.decision.upper(),
        "routing": req.decision.upper()
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


# ─────────────────────────────────────────────────────────────────────────────
#  AI VISION ANALYSIS + EMAIL REPORT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{case_id}/analyse")
async def analyse_case(
    case_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Trigger AI vision analysis on a case's evidence images.

    - Calls the vision LLM to analyse each evidence image
    - Stores the analysis report in the case document
    - Sends a rich HTML email to the company inbox with one-click Approve/Reject links
    Returns the analysis report immediately.
    """
    cases_col = get_cases_col()
    sessions_col = get_sessions_col()
    if cases_col is None or sessions_col is None:
        raise HTTPException(status_code=500, detail="Database not available")

    case = await cases_col.find_one({"id": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    sid = case.get("session_id")
    session = await sessions_col.find_one({"id": sid}) or {}
    evidence_urls: List[str] = session.get("evidence_urls") or []

    # Run vision analysis
    from app.services.vision_analysis_service import analyse_evidence_images
    report = await analyse_evidence_images(
        evidence_urls=evidence_urls,
        claim_text=session.get("claim_text"),
        return_reason=session.get("return_reason"),
        category=session.get("category"),
    )

    # Persist the report to the case document
    await cases_col.update_one(
        {"id": case_id},
        {"$set": {
            "ai_report": report,
            "ai_analysed_at": datetime.utcnow().isoformat(),
            "reasoning_narrative": _build_narrative(report),
        }},
    )

    # Build one-click email action URLs
    base_url = settings.DASHBOARD_BASE_URL or str(request.base_url).rstrip("/")
    approve_token = _sign_action_token(case_id, "APPROVED")
    reject_token = _sign_action_token(case_id, "REJECTED")
    approve_url = f"{base_url}/api/v1/cases/{case_id}/email-action?action=APPROVED&token={approve_token}"
    reject_url = f"{base_url}/api/v1/cases/{case_id}/email-action?action=REJECTED&token={reject_token}"

    # Prepare full case data for email
    case_data_for_email = {
        **case,
        "_id": str(case.get("_id", "")),
        "session": {
            "order_id": session.get("order_id"),
            "customer_ref": session.get("customer_ref"),
            "claim_text": session.get("claim_text"),
            "return_reason": session.get("return_reason"),
            "category": session.get("category"),
        },
    }

    # Send email in background (non-blocking)
    background_tasks.add_task(
        _send_report_email_bg,
        case_id=case_id,
        report=report,
        evidence_urls=evidence_urls,
        case_data=case_data_for_email,
        approve_url=approve_url,
        reject_url=reject_url,
    )

    logger.info("Case analysis complete", case_id=case_id, recommendation=report.get("overall_recommendation"))
    return {
        "case_id": case_id,
        "report": report,
        "email_queued": True,
        "message": "Analysis complete. Report email is being sent.",
    }


@router.get("/{case_id}/email-action", response_class=HTMLResponse)
async def handle_email_action(
    case_id: str,
    action: str = Query(..., description="APPROVED or REJECTED"),
    token: str = Query(..., description="Signed action token"),
):
    """
    One-click Approve/Reject endpoint linked from the evidence report email.

    Validates the signed token, records the decision, and returns a
    confirmation HTML page.
    """
    valid_actions = {"APPROVED", "REJECTED"}
    action = action.upper()
    if action not in valid_actions:
        return _html_response_page("❌ Invalid Action", "The action in this link is not recognised.", "#ef4444")

    # Verify token
    if not _verify_action_token(case_id, action, token):
        return _html_response_page("🔒 Invalid or Expired Link", "This action link is invalid or has already been used.", "#ef4444")

    cases_col = get_cases_col()
    if cases_col is None:
        return _html_response_page("⚠️ Database Error", "Could not connect to the database. Please try from the dashboard.", "#f59e0b")

    case = await cases_col.find_one({"id": case_id})
    if not case:
        return _html_response_page("❌ Case Not Found", f"Case {case_id} was not found.", "#ef4444")

    # Record the decision
    update = {
        "reviewer_id": "email_action",
        "reviewer_decision": action,
        "reviewer_notes": f"Decision made via email one-click link",
        "reviewed_at": datetime.utcnow().isoformat(),
        "state": action,
        "routing": action,
    }
    await cases_col.update_one({"id": case_id}, {"$set": update})
    logger.info("Email action recorded", case_id=case_id, action=action)

    if action == "APPROVED":
        return _html_response_page(
            "✅ Case Approved",
            f"Case <strong>{case_id}</strong> has been approved. The claim will be processed.",
            "#10b981",
        )
    else:
        return _html_response_page(
            "🚫 Case Rejected",
            f"Case <strong>{case_id}</strong> has been rejected. The claim has been denied.",
            "#ef4444",
        )


# ─────────────────────────────────────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_narrative(report: Dict[str, Any]) -> str:
    rec = report.get("overall_recommendation", "ESCALATE")
    conf = report.get("confidence", 0)
    summary = report.get("summary", "")
    findings = report.get("key_findings", [])
    findings_str = " | ".join(findings[:4]) if findings else "No specific findings."
    return (
        f"AI Vision Analysis — Recommendation: {rec} (confidence {conf:.0%}). "
        f"{summary} Key findings: {findings_str}"
    )


def _sign_action_token(case_id: str, action: str) -> str:
    """Generate an HMAC-signed token for an email action link."""
    secret = (settings.APP_SECRET_KEY.get_secret_value() if settings.APP_SECRET_KEY else "arguscx-email-secret")
    payload = f"{case_id}:{action}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]  # type: ignore[attr-defined]
    return sig


def _verify_action_token(case_id: str, action: str, token: str) -> bool:
    """Verify the HMAC token for an email action link."""
    expected = _sign_action_token(case_id, action)
    return hmac.compare_digest(expected, token)


def _html_response_page(title: str, message: str, color: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ArgusCX — {title}</title>
  <style>
    body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f3f4f6; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
    .card {{ background: #fff; border-radius: 16px; padding: 48px 40px; max-width: 480px; width: 90%; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
    .icon {{ font-size: 56px; margin-bottom: 16px; }}
    h1 {{ font-size: 24px; font-weight: 700; color: {color}; margin: 0 0 12px 0; }}
    p {{ font-size: 15px; color: #6b7280; line-height: 1.6; margin: 0 0 24px 0; }}
    .badge {{ display: inline-block; padding: 6px 16px; background: #f3f4f6; border-radius: 20px; font-size: 12px; color: #9ca3af; font-family: monospace; }}
    .footer {{ margin-top: 24px; font-size: 12px; color: #d1d5db; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{title.split()[0]}</div>
    <h1>{" ".join(title.split()[1:])}</h1>
    <p>{message}</p>
    <div class="footer">Secured by ArgusCX · This decision has been logged.</div>
  </div>
</body>
</html>"""


async def _send_report_email_bg(
    case_id: str,
    report: Dict[str, Any],
    evidence_urls: List[str],
    case_data: Dict[str, Any],
    approve_url: str,
    reject_url: str,
) -> None:
    """Background task: send the case report email."""
    from app.services.notification_service import send_case_report_email
    status = await send_case_report_email(
        case_id=case_id,
        report=report,
        evidence_urls=evidence_urls,
        case_data=case_data,
        approve_url=approve_url,
        reject_url=reject_url,
    )
    logger.info("Case report email dispatch", case_id=case_id, status=status)
