"""
ArgusCX — Knowledge Base Routes
Exposes the in-memory RAG store for browsing and manual search.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.rag.retriever import get_vector_store, retrieve_documents
from app.rag.indexer import ALL_DOCUMENTS
from app.models.schemas import KnowledgeDocument, RAGResult

router = APIRouter(prefix="/knowledge")


class SearchRequest(BaseModel):
    query: str
    namespace: Optional[str] = None
    top_k: int = 5


class KnowledgeDocumentCreate(BaseModel):
    title: str
    content: str
    category: str = "policies"
    tags: List[str] = []


@router.get("/documents", response_model=List[dict])
async def list_documents(
    category: Optional[str] = Query(None, description="Filter by category: policies | faqs | past_tickets"),
    limit: int = Query(50, ge=1, le=200),
):
    """Return all documents in the RAG knowledge base."""
    docs = ALL_DOCUMENTS
    if category:
        docs = [d for d in docs if d.get("category") == category]
    return docs[:limit]


@router.post("/documents", response_model=dict, status_code=201)
async def add_document(document: KnowledgeDocumentCreate):
    """Ingest an organisation-owned policy, FAQ, or approved runbook."""
    normalized = {
        "title": document.title.strip(),
        "content": document.content.strip(),
        "category": document.category.strip().lower(),
        "tags": [tag.strip().lower() for tag in document.tags if tag.strip()],
    }
    if not normalized["title"] or not normalized["content"]:
        raise HTTPException(status_code=422, detail="title and content are required")
    ALL_DOCUMENTS.append(normalized)
    store = await get_vector_store()
    await store.add_documents([normalized])
    return {"document": normalized, "total_documents": len(ALL_DOCUMENTS)}


@router.post("/search", response_model=dict)
async def search_knowledge(req: SearchRequest):
    """Perform a RAG search over the knowledge base."""
    result: RAGResult = await retrieve_documents(
        query=req.query,
        namespace=req.namespace,
        top_k=req.top_k,
    )
    return {
        "query": result.query,
        "results": [
            {
                "title": doc.title,
                "content": doc.content,
                "category": doc.category,
                "tags": doc.tags,
                "score": round(score, 4),
            }
            for doc, score in zip(result.documents, result.scores)
        ],
        "total": len(result.documents),
    }


@router.get("/stats")
async def knowledge_stats():
    """Return knowledge base statistics."""
    by_cat: dict = {}
    for d in ALL_DOCUMENTS:
        cat = d.get("category", "unknown")
        by_cat[cat] = by_cat.get(cat, 0) + 1
    return {
        "total_documents": len(ALL_DOCUMENTS),
        "by_category": by_cat,
        "vector_store": "in_memory_keyword",
    }
