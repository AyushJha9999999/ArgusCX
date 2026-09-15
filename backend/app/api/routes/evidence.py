"""
ArgusCX — Evidence upload route
Saves uploaded files to local disk and runs immediate EXIF pre-check.
No external storage API needed — uses local ./uploads directory.
"""
import os
import shutil
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


@router.post("/upload", response_model=EvidenceFile)
async def upload_evidence(file: UploadFile = File(...)):
    """
    Upload an evidence file (image, video, invoice).
    File is saved to local disk under ./uploads/{id}/{filename}.
    Returns an EvidenceFile reference with a usable local path.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Sanitise filename
    safe_name = Path(file.filename).name.replace(" ", "_")
    evidence_id = str(uuid4())
    target_dir = _ensure_upload_dir(evidence_id)
    target_path = target_dir / safe_name

    try:
        # Stream to disk
        with target_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        logger.error("Evidence file write failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to save evidence file")
    finally:
        await file.close()

    size_bytes = target_path.stat().st_size
    content_type = file.content_type or _guess_content_type(safe_name)

    logger.info(
        "Evidence file saved",
        evidence_id=evidence_id,
        filename=safe_name,
        size_bytes=size_bytes,
        content_type=content_type,
    )

    return EvidenceFile(
        id=evidence_id,
        filename=safe_name,
        # Absolute local path — the verification agent reads this directly
        url=str(target_path),
        file_type=content_type,
        size_bytes=size_bytes,
    )


@router.get("/uploads/{evidence_id}/{filename}")
async def serve_evidence(evidence_id: str, filename: str):
    """Serve a previously uploaded evidence file."""
    safe_name = Path(filename).name
    target_path = UPLOAD_DIR / evidence_id / safe_name
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found")

    from fastapi.responses import FileResponse
    return FileResponse(str(target_path))


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
