"""SMTP delivery for real human-support handoffs.

All SMTP values come from deployment configuration. A missing mail provider is
reported as `not_configured`; it never becomes a fake successful notification.
"""
import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from typing import Literal

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

DeliveryStatus = Literal["sent", "not_configured", "failed"]


def _send_message_sync(message: EmailMessage) -> None:
    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=ssl.create_default_context(), timeout=15) as client:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
            client.send_message(message)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as client:
        client.ehlo()
        if settings.SMTP_USE_TLS:
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
        client.send_message(message)


async def send_handoff_email(subject: str, body: str) -> DeliveryStatus:
    """Notify the configured human-support inbox of a handoff."""
    if not settings.smtp_configured:
        return "not_configured"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME or settings.APP_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = settings.SUPPORT_HANDOFF_EMAIL
    message.set_content(body)
    try:
        await asyncio.to_thread(_send_message_sync, message)
        logger.info("Human handoff email sent", recipient=settings.SUPPORT_HANDOFF_EMAIL)
        return "sent"
    except Exception as exc:
        logger.error("Human handoff email failed", error=str(exc))
        return "failed"
