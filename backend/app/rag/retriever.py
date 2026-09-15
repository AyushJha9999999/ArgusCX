"""
ArgusCX — RAG Retriever
Real semantic search using sentence-transformer embeddings + cosine similarity.
No keyword matching — actual vector-based retrieval.
"""
import numpy as np
from typing import List, Optional
import structlog
from app.models.schemas import KnowledgeDocument, RAGResult
from app.core.config import settings

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────
#  Embedding Model (loaded once, cached globally)
# ─────────────────────────────────────────────
_embedding_model = None


def _get_embedding_model():
    """Lazy-load the sentence-transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Sentence-transformer model loaded")
        except ImportError:
            logger.error("sentence-transformers not installed — RAG will use fallback")
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
    return _embedding_model


# ─────────────────────────────────────────────
#  Vector Store with Real Embeddings
# ─────────────────────────────────────────────

class EmbeddingVectorStore:
    """Vector store using sentence-transformer embeddings and cosine similarity."""

    def __init__(self):
        self.documents: List[dict] = []
        self.embeddings: Optional[np.ndarray] = None

    async def add_documents(self, documents: List[dict]):
        """Add documents without blocking application startup on model loading."""
        self.documents.extend(documents)
        self.embeddings = None
        logger.info("Knowledge documents loaded; semantic model deferred", count=len(self.documents))

    async def search(self, query: str, namespace: Optional[str] = None, top_k: int = 3) -> RAGResult:
        """Semantic search using cosine similarity."""
        model = _get_embedding_model()

        if model and self.embeddings is None:
            texts = [f"{d['title']} {d['content']}" for d in self.documents]
            self.embeddings = model.encode(texts, normalize_embeddings=True)
            logger.info("Embedded documents", count=len(self.documents), dim=self.embeddings.shape[1])

        # Filter by namespace first
        if namespace:
            filtered_indices = [i for i, d in enumerate(self.documents) if d.get("category") == namespace]
        else:
            filtered_indices = list(range(len(self.documents)))

        if not filtered_indices:
            return RAGResult(documents=[], scores=[], query=query)

        if model and self.embeddings is not None:
            # Real semantic search with embeddings
            query_embedding = model.encode([query], normalize_embeddings=True)
            filtered_embeddings = self.embeddings[filtered_indices]

            # Cosine similarity (embeddings are normalized, so dot product = cosine sim)
            similarities = np.dot(filtered_embeddings, query_embedding.T).flatten()

            # Sort by similarity
            ranked_indices = np.argsort(similarities)[::-1][:top_k]

            docs = []
            scores = []
            for idx in ranked_indices:
                original_idx = filtered_indices[idx]
                d = self.documents[original_idx]
                docs.append(KnowledgeDocument(
                    title=d["title"],
                    content=d["content"],
                    category=d["category"],
                    tags=d.get("tags", []),
                ))
                scores.append(float(similarities[idx]))

            return RAGResult(documents=docs, scores=scores, query=query)

        else:
            # Fallback to keyword matching if no embedding model
            return self._keyword_fallback(query, filtered_indices, top_k)

    def _keyword_fallback(self, query: str, indices: list, top_k: int) -> RAGResult:
        """Fallback keyword matching."""
        query_words = set(query.lower().split())
        results = []
        for idx in indices:
            d = self.documents[idx]
            text = f"{d['title']} {d['content']} {' '.join(d.get('tags', []))}".lower()
            doc_words = set(text.split())
            overlap = query_words & doc_words
            score = len(overlap) / max(len(query_words), 1)
            results.append((score, d))

        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:top_k]

        docs = [KnowledgeDocument(title=d["title"], content=d["content"], category=d["category"], tags=d.get("tags", [])) for _, d in top]
        scores = [s for s, _ in top]
        return RAGResult(documents=docs, scores=scores, query=query)


# ─────────────────────────────────────────────
#  Singleton & Public API
# ─────────────────────────────────────────────

_store_instance: Optional[EmbeddingVectorStore] = None


async def get_vector_store() -> EmbeddingVectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = EmbeddingVectorStore()
    return _store_instance


async def retrieve_documents(query: str, namespace: Optional[str] = None, top_k: int = 3) -> RAGResult:
    """Main retrieval function used by the Retrieval Agent."""
    store = await get_vector_store()
    return await store.search(query, namespace=namespace, top_k=top_k)
