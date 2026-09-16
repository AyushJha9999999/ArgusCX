"""
ArgusCX -- Storage Service
MinIO/S3 presigned upload URLs + evidence download.
Gracefully degrades to stub mode when MinIO is unavailable.
"""
import os
from datetime import timedelta
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    from minio import Minio
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False

_client = None
_bucket_name = "argusgx-evidence"


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not MINIO_AVAILABLE:
        return None
    try:
        endpoint   = os.environ.get("MINIO_ENDPOINT",   "localhost:9000")
        access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        secure     = os.environ.get("MINIO_SECURE", "false").lower() == "true"
        _client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    except Exception as exc:
        logger.error("MinIO init failed", error=str(exc))
        _client = None
    return _client


def ensure_bucket():
    c = _get_client()
    if not c:
        return
    try:
        if not c.bucket_exists(_bucket_name):
            c.make_bucket(_bucket_name)
    except Exception as exc:
        logger.error("ensure_bucket failed", error=str(exc))


def generate_presigned_upload_url(
    session_id: str,
    evidence_id: str,
    mime_type: str = "video/mp4",
    ttl_minutes: int = 15,
) -> Optional[str]:
    c = _get_client()
    if not c:
        return f"http://localhost:9000/{_bucket_name}/{session_id}/{evidence_id}"
    obj = f"{session_id}/{evidence_id}"
    try:
        return c.presigned_put_object(_bucket_name, obj, expires=timedelta(minutes=ttl_minutes))
    except Exception as exc:
        logger.error("presigned_url_failed", error=str(exc))
        return None


def get_evidence_url(session_id: str, evidence_id: str) -> str:
    return f"/{_bucket_name}/{session_id}/{evidence_id}"


def download_evidence_bytes(storage_url: str) -> Optional[bytes]:
    c = _get_client()
    if not c:
        return None
    try:
        parts = storage_url.lstrip("/").split("/", 1)
        bucket = parts[0] if len(parts) > 0 else _bucket_name
        obj    = parts[1] if len(parts) > 1 else storage_url
        resp = c.get_object(bucket, obj)
        data = resp.read()
        resp.close()
        return data
    except Exception as exc:
        logger.error("download_evidence_failed", url=storage_url, error=str(exc))
        return None
