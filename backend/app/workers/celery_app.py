"""
ArgusCX — Celery Worker Configuration
Background task processing (evidence analysis, async agent runs, notifications)
All config from environment variables — no hardcoded values.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "arguscx",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.evidence_tasks",
        "app.workers.tasks.notification_tasks",
        "app.workers.tasks.analytics_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.evidence_tasks.*": {"queue": "evidence"},
        "app.workers.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.workers.tasks.analytics_tasks.*": {"queue": "analytics"},
    },
)

if __name__ == "__main__":
    celery_app.start()
