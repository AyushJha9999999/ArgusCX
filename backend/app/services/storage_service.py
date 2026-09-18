"""S3-compatible evidence storage.

The service returns no upload link until real object storage is configured.
"""
from datetime import timedelta
from typing import Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

try:
    from minio import Minio
except ImportError:  # pragma: no cover - dependency is deployment-specific
    Minio = None

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not Minio or not all((settings.OBJECT_STORAGE_ENDPOINT, settings.OBJECT_STORAGE_ACCESS_KEY, settings.OBJECT_STORAGE_SECRET_KEY, settings.OBJECT_STORAGE_BUCKET)):
        return None
    _client = Minio(
        settings.OBJECT_STORAGE_ENDPOINT,
        access_key=settings.OBJECT_STORAGE_ACCESS_KEY.get_secret_value(),
        secret_key=settings.OBJECT_STORAGE_SECRET_KEY.get_secret_value(),
        secure=settings.OBJECT_STORAGE_SECURE,
    )
    return _client


def ensure_bucket() -> bool:
    client = _get_client()
    bucket = settings.OBJECT_STORAGE_BUCKET
    if not client or not bucket:
        return False
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        return True
    except Exception as exc:
        logger.error("Object storage bucket check failed", error=str(exc))
        return False


def generate_presigned_upload_url(
    session_id: str,
    evidence_id: str,
    mime_type: str = "video/mp4",
    ttl_minutes: int = 15,
) -> Optional[str]:
    client = _get_client()
    bucket = settings.OBJECT_STORAGE_BUCKET
    if not client or not bucket or not ensure_bucket():
        return None
    try:
        return client.presigned_put_object(bucket, f"{session_id}/{evidence_id}", expires=timedelta(minutes=ttl_minutes))
    except Exception as exc:
        logger.error("Presigned upload URL creation failed", error=str(exc))
        return None


def get_evidence_url(session_id: str, evidence_id: str) -> Optional[str]:
    bucket = settings.OBJECT_STORAGE_BUCKET
    return f"/{bucket}/{session_id}/{evidence_id}" if bucket else None


def download_evidence_bytes(storage_url: str) -> Optional[bytes]:
    client = _get_client()
    bucket = settings.OBJECT_STORAGE_BUCKET
    if not client or not bucket:
        return None
    try:
        object_name = storage_url.removeprefix(f"/{bucket}/")
        response = client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    except Exception as exc:
        logger.error("Evidence download failed", error=str(exc))
        return None
