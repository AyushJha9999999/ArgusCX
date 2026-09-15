"""
ArgusCX — Tickets API Routes
POST /tickets → Submit a ticket through the full agent pipeline
GET  /tickets → List all tickets
GET  /tickets/{id} → Get a specific ticket
GET  /tickets/stats/summary → Quick stats
PATCH /tickets/{id}/resolve → Human agent resolve/reject

All ticket processing now goes through:
1. Guardrails (safety check)
2. Preprocessor (language, PII, intent, sentiment)
3. Full LangGraph agent pipeline
"""
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import (
    Ticket, TicketCreate, TicketResponse, AgentState,
    Channel, TicketCategory, Customer, TicketStatus, EvidenceFile,
    HumanOverride,
)
from app.agents.orchestrator import process_ticket
from app.services.preprocessor import preprocess_request
from app.services.guardrails import check_guardrails
from app.core.config import settings

router = APIRouter(prefix="/tickets")

# In-memory store (persists for the lifetime of the process)
_tickets: Dict[str, Ticket] = {}


class SubmitTicketRequest(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None
    subject: str
    message: str
    channel: Channel = Channel.WEB
    category: Optional[TicketCategory] = None
    account_age_days: Optional[int] = 180
    previous_tickets: int = 0
    previous_fraud_flags: int = 0
    evidence_file_ids: List[str] = []
    evidence_urls: List[str] = []


@router.post("", response_model=TicketResponse)
async def submit_ticket(request: SubmitTicketRequest):
    """Submit a new support ticket through the full AI pipeline."""
    start_ms = int(time.time() * 1000)

    # ── Step 1: Guardrails Check ──────────────
    guardrail_result = await check_guardrails(request.message, context="customer_input")

    if guardrail_result.recommendation == "block":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Message blocked by safety guardrails",
                "explanation": guardrail_result.explanation,
                "risk_flags": guardrail_result.risk_flags,
            },
        )

    # ── Step 2: Preprocess Request ────────────
    preprocessed = await preprocess_request(request.message, request.subject)

    # Auto-detect category from intent if not provided
    category = request.category
    if not category:
        intent_to_category = {
            "refund_request": TicketCategory.ORDER_REFUND,
            "payment_issue": TicketCategory.BILLING_PAYMENT,
            "account_issue": TicketCategory.ACCOUNT,
            "fraud_report": TicketCategory.FRAUD,
            "order_status": TicketCategory.GENERAL,
            "complaint": TicketCategory.GENERAL,
            "general_inquiry": TicketCategory.GENERAL,
            "feedback": TicketCategory.GENERAL,
        }
        category = intent_to_category.get(preprocessed.intent, TicketCategory.GENERAL)

    # ── Step 3: Build Ticket ──────────────────
    customer = Customer(
        id=request.customer_id or f"CUST-{int(time.time())}",
        name=request.customer_name,
        email=request.customer_email,
        channel=request.channel,
        account_age_days=request.account_age_days,
        previous_tickets=request.previous_tickets,
        previous_fraud_flags=request.previous_fraud_flags,
    )

    evidence_files: List[EvidenceFile] = []
    for i, url in enumerate(request.evidence_urls):
        from pathlib import Path
        p = Path(url)
        evidence_files.append(EvidenceFile(
            id=request.evidence_file_ids[i] if i < len(request.evidence_file_ids) else f"ev-{i}",
            filename=p.name,
            url=url,
            file_type=_guess_mime(p.suffix),
            size_bytes=p.stat().st_size if p.exists() else 0,
        ))

    ticket = Ticket(
        customer=customer,
        subject=request.subject,
        message=request.message,
        channel=request.channel,
        category=category,
        evidence_files=evidence_files,
        metadata={
            "preprocessor": {
                "language": preprocessed.language,
                "intent": preprocessed.intent,
                "sentiment": preprocessed.sentiment,
                "urgency": preprocessed.urgency,
                "pii_detected": preprocessed.pii_detected,
                "summary": preprocessed.summary,
            },
            "guardrails": {
                "recommendation": guardrail_result.recommendation,
                "is_toxic": guardrail_result.is_toxic,
                "is_jailbreak": guardrail_result.is_jailbreak,
                "risk_flags": guardrail_result.risk_flags,
            },
        },
    )

    # ── Step 4: Run Agent Pipeline ────────────
    state = AgentState(ticket=ticket)
    result_state = await process_ticket(state)

    # Sync results back onto ticket
    result_state.ticket.confidence_score = result_state.confidence_score
    result_state.ticket.risk_score = result_state.risk_score
    result_state.ticket.fraud_analysis = result_state.fraud_analysis
    result_state.ticket.resolution_decision = result_state.resolution_decision
    result_state.ticket.resolution_message = result_state.resolution_message
    result_state.ticket.retrieved_context = result_state.retrieved_policies

    if not result_state.should_escalate:
        result_state.ticket.status = TicketStatus.AUTO_RESOLVED

    processing_time = int(time.time() * 1000) - start_ms

    # Persist to store
    _tickets[result_state.ticket.id] = result_state.ticket

    # Broadcast real-time update via WebSocket
    try:
        from app.api.websockets.ticket_ws import broadcast
        import asyncio
        asyncio.create_task(broadcast({
            "type": "ticket_update",
            "ticket_id": result_state.ticket.id,
            "status": result_state.ticket.status.value,
            "confidence": result_state.ticket.confidence_score,
            "risk": result_state.ticket.risk_score,
            "fraud_score": result_state.ticket.fraud_analysis.fraud_score if result_state.ticket.fraud_analysis else 0,
            "resolution": result_state.ticket.resolution_decision.value if result_state.ticket.resolution_decision else None,
            "preprocessing": ticket.metadata.get("preprocessor", {}),
        }))
    except Exception:
        pass

    return TicketResponse(
        ticket=result_state.ticket,
        processing_time_ms=processing_time,
        demo_mode=False,
    )


@router.get("", response_model=List[Ticket])
async def list_tickets(
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all tickets with optional filters."""
    tickets = list(_tickets.values())
    if status:
        tickets = [t for t in tickets if t.status == status]
    if category:
        tickets = [t for t in tickets if t.category == category]
    tickets.sort(key=lambda t: t.created_at, reverse=True)
    return tickets[offset: offset + limit]


@router.get("/stats/summary")
async def ticket_stats() -> Dict[str, Any]:
    """Quick stats for the dashboard header."""
    tickets = list(_tickets.values())
    total = len(tickets)
    if total == 0:
        return {
            "total": 0,
            "auto_resolved": 0,
            "escalated": 0,
            "fraud_flagged": 0,
            "avg_confidence": 0.0,
            "avg_risk": 0.0,
        }

    return {
        "total": total,
        "auto_resolved": sum(1 for t in tickets if t.status == TicketStatus.AUTO_RESOLVED),
        "escalated": sum(1 for t in tickets if t.status == TicketStatus.ESCALATED),
        "fraud_flagged": sum(
            1 for t in tickets
            if t.status == TicketStatus.FRAUD_FLAGGED
            or (t.fraud_analysis and t.fraud_analysis.fraud_score >= 0.65)
        ),
        "avg_confidence": round(sum(t.confidence_score for t in tickets) / total, 3),
        "avg_risk": round(sum(t.risk_score for t in tickets) / total, 3),
    }


@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID including full case file."""
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.patch("/{ticket_id}/resolve")
async def human_resolve(ticket_id: str, override: HumanOverride):
    """Human agent override — approve, reject, or modify."""
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    action = override.action.lower()
    if action == "approve":
        ticket.status = TicketStatus.CLOSED
        ticket.assigned_to = override.agent_id
        ticket.metadata["human_approved"] = True
        ticket.metadata["human_notes"] = override.notes
    elif action == "reject":
        ticket.status = TicketStatus.CLOSED
        ticket.metadata["human_rejected"] = True
        ticket.metadata["human_notes"] = override.notes
        ticket.resolution_message = "Your request has been reviewed and rejected. " + (override.notes or "")
    elif action == "modify":
        ticket.status = TicketStatus.CLOSED
        ticket.metadata["human_modified"] = True
        ticket.metadata["human_notes"] = override.notes
        if override.modified_resolution:
            ticket.resolution_message = override.modified_resolution
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {override.action}")

    _tickets[ticket_id] = ticket

    try:
        from app.api.websockets.ticket_ws import broadcast
        import asyncio
        asyncio.create_task(broadcast({
            "type": "ticket_resolved",
            "ticket_id": ticket_id,
            "action": action,
            "agent_id": override.agent_id,
        }))
    except Exception:
        pass

    return {"message": f"Ticket {ticket_id} {action}d by agent {override.agent_id}", "ticket_id": ticket_id, "new_status": ticket.status.value}


def _guess_mime(ext: str) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".pdf": "application/pdf",
        ".mp4": "video/mp4",
    }.get(ext.lower(), "application/octet-stream")
