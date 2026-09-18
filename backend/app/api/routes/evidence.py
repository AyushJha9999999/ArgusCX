"""
ArgusCX — Evidence upload route
Saves uploaded files to AWS S3 (ap-southeast-1) when credentials are configured.
Falls back to local ./uploads directory for development.
"""
import os
import io
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException
import structlog

from app.models.schemas import EvidenceFile
from app.core.config import settings

router = APIRouter(prefix="/evidence")
logger = structlog.get_logger(__name__)

# Resolve upload directory relative to the backend working directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()


def _ensure_upload_dir(evidence_id: str) -> Path:
    """Create the upload subdirectory for this evidence item."""
    target = UPLOAD_DIR / evidence_id
    target.mkdir(parents=True, exist_ok=True)
    return target


def _guess_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")


def _is_s3_configured() -> bool:
    return bool(
        settings.OBJECT_STORAGE_BUCKET
        and settings.OBJECT_STORAGE_ACCESS_KEY
        and settings.OBJECT_STORAGE_SECRET_KEY
    )


async def _upload_to_s3(file_bytes: bytes, s3_key: str, content_type: str) -> str:
    """Upload bytes to AWS S3 and return the public HTTPS URL."""
    import aioboto3
    from botocore.config import Config

    region = settings.OBJECT_STORAGE_REGION or "ap-southeast-1"
    bucket = settings.OBJECT_STORAGE_BUCKET

    session = aioboto3.Session(
        aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY.get_secret_value(),
        aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_KEY.get_secret_value(),
        region_name=region,
    )

    config = Config(region_name=region, signature_version="s3v4")
    
    # Use endpoint_url only if explicitly overridden (for Cloudflare R2 etc.)
    # For standard AWS S3, let boto3 resolve the regional endpoint automatically.
    endpoint_url = None
    if settings.OBJECT_STORAGE_ENDPOINT and "amazonaws.com" not in settings.OBJECT_STORAGE_ENDPOINT:
        endpoint_url = settings.OBJECT_STORAGE_ENDPOINT

    async with session.client("s3", endpoint_url=endpoint_url, config=config) as s3:
        await s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )

    # Return the canonical S3 URL
    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"


@router.post("/upload", response_model=EvidenceFile)
async def upload_evidence(file: UploadFile = File(...)):
    """
    Upload an evidence file (image, video, invoice).
    Uses AWS S3 bucket 'arguscx-uploads-rimo-1734' in ap-southeast-1 when configured.
    Falls back to local disk under ./uploads/{id}/{filename} otherwise.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    safe_name = Path(file.filename).name.replace(" ", "_")
    evidence_id = str(uuid4())
    content_type = file.content_type or _guess_content_type(safe_name)

    file_bytes = await file.read()
    size_bytes = len(file_bytes)
    destination = "local"
    final_url = ""

    if _is_s3_configured():
        s3_key = f"evidence/{evidence_id}/{safe_name}"
        try:
            final_url = await _upload_to_s3(file_bytes, s3_key, content_type)
            destination = "s3"
            logger.info(
                "Evidence uploaded to S3",
                evidence_id=evidence_id,
                bucket=settings.OBJECT_STORAGE_BUCKET,
                key=s3_key,
                size_bytes=size_bytes,
            )
        except Exception as exc:
            logger.error("S3 upload failed, falling back to local disk", error=str(exc))
            # Fall through to local storage on S3 error
            destination = "local_fallback"

    if destination != "s3":
        target_dir = _ensure_upload_dir(evidence_id)
        target_path = target_dir / safe_name
        try:
            with target_path.open("wb") as f:
                f.write(file_bytes)
            final_url = f"/api/v1/evidence/uploads/{evidence_id}/{safe_name}"
            logger.info(
                "Evidence saved to local disk",
                evidence_id=evidence_id,
                path=str(target_path),
                size_bytes=size_bytes,
            )
        except Exception as exc:
            logger.error("Evidence file write failed", error=str(exc))
            raise HTTPException(status_code=500, detail="Failed to save evidence file")

    return EvidenceFile(
        id=evidence_id,
        filename=safe_name,
        url=final_url,
        file_type=content_type,
        size_bytes=size_bytes,
    )


@router.get("/uploads/{evidence_id}/{filename}")
async def serve_evidence(evidence_id: str, filename: str):
    """Serve a locally stored evidence file (used when S3 is not configured)."""
    safe_name = Path(filename).name
    target_path = UPLOAD_DIR / evidence_id / safe_name
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found")

    from fastapi.responses import FileResponse
    return FileResponse(str(target_path))


@router.get("/health")
async def storage_health():
    """Check if S3 is reachable and the bucket is accessible."""
    if not _is_s3_configured():
        return {"storage": "local", "s3_configured": False}

    try:
        import aioboto3
        region = settings.OBJECT_STORAGE_REGION or "ap-southeast-1"
        session = aioboto3.Session(
            aws_access_key_id=settings.OBJECT_STORAGE_ACCESS_KEY.get_secret_value(),
            aws_secret_access_key=settings.OBJECT_STORAGE_SECRET_KEY.get_secret_value(),
            region_name=region,
        )
        async with session.client("s3", region_name=region) as s3:
            await s3.head_bucket(Bucket=settings.OBJECT_STORAGE_BUCKET)
        return {
            "storage": "s3",
            "s3_configured": True,
            "bucket": settings.OBJECT_STORAGE_BUCKET,
            "region": region,
            "status": "reachable",
        }
    except Exception as exc:
        return {
            "storage": "s3",
            "s3_configured": True,
            "bucket": settings.OBJECT_STORAGE_BUCKET,
            "status": "error",
            "detail": str(exc),
        }
