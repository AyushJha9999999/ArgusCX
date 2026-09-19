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


def _is_storage_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )

def _init_cloudinary():
    if not _is_storage_configured():
        return
    import cloudinary
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

async def _upload_to_cloudinary(file_bytes: bytes, evidence_id: str, filename: str) -> str:
    import cloudinary.uploader
    from fastapi.concurrency import run_in_threadpool
    
    # Run the synchronous Cloudinary upload function in a threadpool
    result = await run_in_threadpool(
        cloudinary.uploader.upload,
        file_bytes,
        folder=f"arguscx/evidence/{evidence_id}",
        public_id=Path(filename).stem,
        resource_type="auto"
    )
    return result.get("secure_url")

@router.post("/upload", response_model=EvidenceFile)
async def upload_evidence(file: UploadFile = File(...)):
    """
    Upload an evidence file (image, video, invoice).
    Uses Cloudinary when configured.
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

    if _is_storage_configured():
        _init_cloudinary()
        try:
            final_url = await _upload_to_cloudinary(file_bytes, evidence_id, safe_name)
            destination = "cloudinary"
            logger.info(
                "Evidence uploaded to Cloudinary",
                evidence_id=evidence_id,
                url=final_url,
                size_bytes=size_bytes,
            )
        except Exception as exc:
            logger.error("Cloudinary upload failed, falling back to local disk", error=str(exc))
            destination = "local_fallback"

    if destination != "cloudinary":
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
    """Serve a locally stored evidence file (used when Cloudinary is not configured)."""
    safe_name = Path(filename).name
    target_path = UPLOAD_DIR / evidence_id / safe_name
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found")

    from fastapi.responses import FileResponse
    return FileResponse(str(target_path))


@router.get("/health")
async def storage_health():
    """Check if Cloudinary is configured and reachable."""
    if not _is_storage_configured():
        return {"storage": "local", "cloudinary_configured": False}

    try:
        _init_cloudinary()
        import cloudinary.api
        from fastapi.concurrency import run_in_threadpool
        await run_in_threadpool(cloudinary.api.ping)
        return {
            "storage": "cloudinary",
            "cloudinary_configured": True,
            "status": "reachable",
        }
    except Exception as exc:
        return {
            "storage": "cloudinary",
            "cloudinary_configured": True,
            "status": "error",
            "detail": str(exc),
        }
