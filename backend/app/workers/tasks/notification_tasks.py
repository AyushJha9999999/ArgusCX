"""ArgusCX — Notification background tasks (Slack, Twilio, SendGrid)"""
from app.workers.celery_app import celery_app
import structlog
logger = structlog.get_logger(__name__)

@celery_app.task(name="notification_tasks.send_slack_alert", bind=True, max_retries=3)
def send_slack_alert(self, ticket_id: str, message: str):
    logger.info("📣 Sending Slack alert", ticket_id=ticket_id)
    # TODO: Use slack-sdk with SLACK_BOT_TOKEN from settings
    return {"ticket_id": ticket_id, "status": "queued"}

@celery_app.task(name="notification_tasks.send_email", bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str):
    logger.info("📧 Sending email", to=to)
    # TODO: Use sendgrid with SENDGRID_API_KEY from settings
    return {"to": to, "status": "queued"}
