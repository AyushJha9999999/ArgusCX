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
from pydantic import BaseModel, Field

from app.models.schemas import (
    Ticket, TicketCreate, TicketResponse, AgentState,
    Channel, TicketCategory, Customer, TicketStatus, EvidenceFile,
    HumanOverride,
)
from app.agents.orchestrator import process_ticket
from app.services.preprocessor import preprocess_request
from app.services.guardrails import check_guardrails
from app.core.config import settings
from app.db.mongodb import get_tickets_col

router = APIRouter(prefix="/tickets")


class SubmitTicketRequest(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None
    subject: str
    message: str
    channel: Channel = Channel.WEB
    category: Optional[TicketCategory] = None
    account_age_days: Optional[int] = None
    previous_tickets: int = 0
    previous_fraud_flags: int = 0
    evidence_file_ids: List[str] = Field(default_factory=list)
    evidence_urls: List[str] = Field(default_factory=list)
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
        
        is_http = url.startswith("http://") or url.startswith("https://")
        size_bytes = 0
        if not is_http:
            try:
                if p.exists():
                    size_bytes = p.stat().st_size
            except Exception:
                pass
                
        evidence_files.append(EvidenceFile(
            id=request.evidence_file_ids[i] if i < len(request.evidence_file_ids) else f"ev-{i}",
            filename=p.name,
            url=url,
            file_type=_guess_mime(p.suffix),
            size_bytes=size_bytes,
        ))

    ticket = Ticket(
        customer=customer,
        subject=request.subject,
        message=request.message,
        channel=request.channel,
        category=category,
        evidence_files=evidence_files,
        metadata={
            **request.metadata,
            "order_id": request.order_id,
            "payment_id": request.payment_id,
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

    if result_state.should_escalate:
        from app.services.handoff_service import create_handoff
        handoff = await create_handoff(
            result_state.ticket,
            reason=result_state.escalation_reason or "AI confidence or policy requires human review.",
        )
        result_state.ticket.metadata["human_handoff"] = {
            key: value for key, value in handoff.items() if key != "context_packet"
        }

    processing_time = int(time.time() * 1000) - start_ms

    # Persist to store
    tickets_col = get_tickets_col()
    if tickets_col is not None:
        await tickets_col.insert_one(result_state.ticket.model_dump(mode="json"))

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
    )


@router.get("", response_model=List[Ticket])
async def list_tickets(
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all tickets with optional filters."""
    tickets_col = get_tickets_col()
    if tickets_col is None:
        return []
        
    query = {}
    if status:
        query["status"] = status.value
    if category:
        query["category"] = category.value
        
    cursor = tickets_col.find(query).sort("created_at", -1).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [Ticket(**doc) for doc in docs]


@router.get("/stats/summary")
async def ticket_stats() -> Dict[str, Any]:
    """Quick stats for the dashboard header."""
    tickets_col = get_tickets_col()
    if tickets_col is None:
        return {
            "total": 0, "auto_resolved": 0, "escalated": 0,
            "fraud_flagged": 0, "avg_confidence": 0.0, "avg_risk": 0.0,
        }

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "auto_resolved": {
                    "$sum": {"$cond": [{"$eq": ["$status", TicketStatus.AUTO_RESOLVED.value]}, 1, 0]}
                },
                "escalated": {
                    "$sum": {"$cond": [{"$eq": ["$status", TicketStatus.ESCALATED.value]}, 1, 0]}
                },
                "fraud_flagged": {
                    "$sum": {
                        "$cond": [
                            {"$or": [
                                {"$eq": ["$status", TicketStatus.FRAUD_FLAGGED.value]},
                                {"$gte": ["$fraud_analysis.fraud_score", 0.65]}
                            ]}, 1, 0
                        ]
                    }
                },
                "avg_confidence": {"$avg": "$confidence_score"},
                "avg_risk": {"$avg": "$risk_score"}
            }
        }
    ]
    
    docs = await tickets_col.aggregate(pipeline).to_list(length=1)
    if not docs:
        return {
            "total": 0, "auto_resolved": 0, "escalated": 0,
            "fraud_flagged": 0, "avg_confidence": 0.0, "avg_risk": 0.0,
        }
        
    stats = docs[0]
    return {
        "total": stats.get("total", 0),
        "auto_resolved": stats.get("auto_resolved", 0),
        "escalated": stats.get("escalated", 0),
        "fraud_flagged": stats.get("fraud_flagged", 0),
        "avg_confidence": round(stats.get("avg_confidence", 0.0) or 0.0, 3),
        "avg_risk": round(stats.get("avg_risk", 0.0) or 0.0, 3),
    }


@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID including full case file."""
    tickets_col = get_tickets_col()
    doc = await tickets_col.find_one({"id": ticket_id}) if tickets_col is not None else None
    if not doc:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return Ticket(**doc)


@router.patch("/{ticket_id}/resolve")
async def human_resolve(ticket_id: str, override: HumanOverride):
    """Human agent override — approve, reject, or modify."""
    tickets_col = get_tickets_col()
    if tickets_col is None:
        raise HTTPException(status_code=500, detail="Database not available")
        
    doc = await tickets_col.find_one({"id": ticket_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    ticket = Ticket(**doc)
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

    await tickets_col.replace_one({"id": ticket_id}, ticket.model_dump(mode="json"))

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
