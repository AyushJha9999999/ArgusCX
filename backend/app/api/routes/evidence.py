"""ArgusCX — Evidence upload route stub"""
from fastapi import APIRouter, UploadFile, File
from app.models.schemas import EvidenceFile
from uuid import uuid4

router = APIRouter(prefix="/evidence")

@router.post("/upload")
async def upload_evidence(file: UploadFile = File(...)):
    """Upload evidence file and return its reference."""
    evidence_id = str(uuid4())
    return EvidenceFile(
        id=evidence_id,
        filename=file.filename,
        url=f"/uploads/{evidence_id}/{file.filename}",
        file_type=file.content_type or "application/octet-stream",
        size_bytes=0,
    )
