"""
ArgusCX — Tickets API Routes
POST /tickets → Submit a ticket through the full agent pipeline
GET  /tickets → List all tickets
GET  /tickets/{id} → Get a specific ticket
"""
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.models.schemas import (
    Ticket, TicketCreate, TicketResponse, AgentState,
    Channel, TicketCategory, Customer, TicketStatus
)
from app.agents.orchestrator import process_ticket
from app.core.config import settings

router = APIRouter(prefix="/tickets")

# In-memory store for demo
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
    demo_scenario: Optional[str] = None  # "genuine" | "fraud" | "tampered"


@router.post("", response_model=TicketResponse)
async def submit_ticket(request: SubmitTicketRequest):
    """Submit a new support ticket and run it through the agent pipeline."""
    start_ms = int(time.time() * 1000)

    customer = Customer(
        id=request.customer_id or f"CUST-{int(time.time())}",
        name=request.customer_name,
        email=request.customer_email,
        channel=request.channel,
        account_age_days=request.account_age_days,
        previous_tickets=request.previous_tickets,
        previous_fraud_flags=request.previous_fraud_flags,
    )

    ticket = Ticket(
        customer=customer,
        subject=request.subject,
        message=request.message,
        channel=request.channel,
        category=request.category,
    )

    # Run through agent pipeline
    state = AgentState(ticket=ticket)
    result_state = await process_ticket(state)

    # Update ticket with results
    result_state.ticket.confidence_score = result_state.confidence_score
    result_state.ticket.risk_score = result_state.risk_score
    result_state.ticket.fraud_analysis = result_state.fraud_analysis
    result_state.ticket.resolution_decision = result_state.resolution_decision
    result_state.ticket.resolution_message = result_state.resolution_message
    result_state.ticket.retrieved_context = result_state.retrieved_policies

    if not result_state.should_escalate:
        result_state.ticket.status = TicketStatus.AUTO_RESOLVED

    processing_time = int(time.time() * 1000) - start_ms

    # Store ticket
    _tickets[result_state.ticket.id] = result_state.ticket

    return TicketResponse(
        ticket=result_state.ticket,
        processing_time_ms=processing_time,
        demo_mode=settings.is_demo_mode,
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


@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a specific ticket by ID."""
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.get("/stats/summary")
async def ticket_stats() -> Dict[str, Any]:
    """Quick stats for the dashboard."""
    tickets = list(_tickets.values())
    total = len(tickets)
    if total == 0:
        return {"total": 0}

    return {
        "total": total,
        "auto_resolved": sum(1 for t in tickets if t.status == TicketStatus.AUTO_RESOLVED),
        "escalated": sum(1 for t in tickets if t.status == TicketStatus.ESCALATED),
        "fraud_flagged": sum(1 for t in tickets if t.status == TicketStatus.FRAUD_FLAGGED),
        "avg_confidence": round(sum(t.confidence_score for t in tickets) / total, 3),
        "avg_risk": round(sum(t.risk_score for t in tickets) / total, 3),
    }
