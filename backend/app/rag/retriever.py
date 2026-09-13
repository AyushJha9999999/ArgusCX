"""
ArgusCX — RAG Retriever
Similarity search over the vector store.
"""
from typing import List, Optional
import structlog
from app.models.schemas import KnowledgeDocument, RAGResult
from app.core.config import settings

logger = structlog.get_logger(__name__)

# In-memory store for demo (no external vector DB needed)
_in_memory_store: List[dict] = []


class InMemoryVectorStore:
    """Simple in-memory store using keyword matching for demo mode."""

    async def add_documents(self, documents: List[dict]):
        global _in_memory_store
        _in_memory_store.extend(documents)
        logger.debug("Added documents to in-memory store", count=len(documents))

    async def search(self, query: str, namespace: Optional[str] = None, top_k: int = 3) -> RAGResult:
        query_lower = query.lower()
        results = []

        for doc in _in_memory_store:
            if namespace and doc.get("category") != namespace:
                continue
            score = _keyword_score(query_lower, doc)
            results.append((score, doc))

        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:top_k]

        docs = [
            KnowledgeDocument(
                title=d["title"],
                content=d["content"],
                category=d["category"],
                tags=d.get("tags", []),
            )
            for _, d in top
        ]
        scores = [s for s, _ in top]
        return RAGResult(documents=docs, scores=scores, query=query)


_store_instance: Optional[InMemoryVectorStore] = None


async def get_vector_store() -> InMemoryVectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = InMemoryVectorStore()
    return _store_instance


async def retrieve_documents(query: str, namespace: Optional[str] = None, top_k: int = 3) -> RAGResult:
    """Main retrieval function used by the Retrieval Agent."""
    store = await get_vector_store()
    return await store.search(query, namespace=namespace, top_k=top_k)


def _keyword_score(query: str, doc: dict) -> float:
    """Simple keyword overlap scoring for demo mode."""
    text = f"{doc['title']} {doc['content']} {' '.join(doc.get('tags', []))}".lower()
    query_words = set(query.split())
    doc_words = set(text.split())
    overlap = query_words & doc_words
    return len(overlap) / max(len(query_words), 1)
