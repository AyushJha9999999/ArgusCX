"""ArgusCX — Knowledge base route stub"""
from fastapi import APIRouter
from app.rag.indexer import ALL_DOCUMENTS

router = APIRouter(prefix="/knowledge")

@router.get("")
async def list_knowledge():
    return {"total": len(ALL_DOCUMENTS), "documents": ALL_DOCUMENTS}
