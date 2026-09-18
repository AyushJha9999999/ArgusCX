"""Inbound support-channel adapters.

Mail providers should POST a verified inbound event to this authenticated API;
ArgusCX turns it into a normal ticket so all guardrails and handoff rules apply.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.schemas import Channel

router = APIRouter(prefix="/channels")


class InboundEmailRequest(BaseModel):
    message_id: str = Field(min_length=3, max_length=255)
    from_email: str = Field(min_length=3, max_length=320)
    from_name: Optional[str] = Field(default=None, max_length=160)
    subject: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=20000)
    order_id: Optional[str] = Field(default=None, max_length=255)
    customer_id: Optional[str] = Field(default=None, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/email/inbound")
async def receive_inbound_email(payload: InboundEmailRequest):
    """Create a ticket from a validated provider inbound-email webhook."""
    from app.api.routes.tickets import SubmitTicketRequest, submit_ticket

    ticket = await submit_ticket(SubmitTicketRequest(
        customer_name=payload.from_name or payload.from_email,
        customer_email=payload.from_email,
        customer_id=payload.customer_id,
        subject=payload.subject,
        message=payload.text,
        channel=Channel.EMAIL,
        order_id=payload.order_id,
        metadata={
            **payload.metadata,
            "inbound_message_id": payload.message_id,
            "source_channel": "email",
        },
    ))
    return {"accepted": True, "ticket": ticket.ticket}
