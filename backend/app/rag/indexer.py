"""Knowledge-base bootstrap.

Customer policies are ingested through the authenticated knowledge API. The
platform starts empty rather than silently using someone else's policy text.
"""
import structlog

from app.rag.retriever import get_vector_store

logger = structlog.get_logger(__name__)
ALL_DOCUMENTS: list[dict] = []


async def init_rag_index() -> None:
    await get_vector_store()
    logger.info("Knowledge base ready for authenticated document ingestion", total_documents=0)
