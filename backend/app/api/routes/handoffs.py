"""Operator API for transferring AI context to a human support team."""
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.handoff_service import create_handoff, get_handoff
from app.db.mongodb import get_tickets_col
from app.models.schemas import Ticket

router = APIRouter(prefix="/handoffs")


class HandoffRequest(BaseModel):
    ticket_id: str
    reason: str = Field(min_length=3, max_length=800)
    queue: str = Field(default="support", min_length=2, max_length=80)
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None


@router.post("", status_code=201)
async def handoff_to_human(payload: HandoffRequest, request: Request):
    tickets_col = get_tickets_col()
    doc = await tickets_col.find_one({"id": payload.ticket_id}) if tickets_col is not None else None
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket = Ticket(**doc)
    identity = getattr(request.state, "authenticated_user", {})
    requested_by = identity.get("email") if isinstance(identity, dict) else None
    return await create_handoff(ticket, payload.reason, payload.queue, payload.priority, requested_by or "operator")


@router.get("/{ticket_id}")
async def get_ticket_handoff(ticket_id: str):
    handoff = get_handoff(ticket_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="No human handoff exists for this ticket")
    return handoff
