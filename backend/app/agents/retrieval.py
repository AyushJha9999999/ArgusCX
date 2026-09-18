"""
ArgusCX — Information Retrieval Agent
Searches policies, FAQs, and past tickets using real semantic RAG (sentence-transformers).
Organisation-owned knowledge is retrieved through the embedding vector store.
"""
from typing import Any, Dict
import structlog
from app.models.schemas import AgentState
from app.rag.retriever import retrieve_documents
from app.core.config import settings

logger = structlog.get_logger(__name__)


async def run_retrieval_agent(state: AgentState) -> Dict[str, Any]:
    """
    Retrieves relevant policies, FAQs, and similar past tickets
    from the RAG knowledge base using semantic search.
    """
    query = f"{state.ticket.subject} {state.ticket.message}"
    logger.info("📚 Retrieval agent searching knowledge base", query=query[:100])

    try:
        # Real RAG retrieval via sentence-transformer embeddings
        policy_results = await retrieve_documents(query, namespace="policies", top_k=3)
        faq_results = await retrieve_documents(query, namespace="faqs", top_k=2)
        past_results = await retrieve_documents(query, namespace="past_tickets", top_k=2)

        policies = [doc.content for doc in policy_results.documents]
        faqs = [doc.content for doc in faq_results.documents]
        past_tickets = [doc.content for doc in past_results.documents]

        logger.info(
            "Retrieval complete",
            policies_found=len(policies),
            faqs_found=len(faqs),
            past_tickets_found=len(past_tickets),
            top_policy_score=round(policy_results.scores[0], 3) if policy_results.scores else 0,
        )

        return {
            "policies": policies,
            "faqs": faqs,
            "past_tickets": past_tickets,
            "confidence": min(0.95, max(policy_results.scores[0], 0.0)) if policy_results.scores else 0.0,
            "reasoning": (
                f"Retrieved {len(policies)} policies (top score: {policy_results.scores[0]:.3f}), "
                f"{len(faqs)} FAQs, {len(past_tickets)} similar past tickets "
                f"via semantic embedding search."
            ) if policy_results.scores else "No matching documents found in knowledge base.",
        }
    except Exception as e:
        logger.error("Retrieval agent failed", error=str(e))
        return {
            "policies": [],
            "faqs": [],
            "past_tickets": [],
            "confidence": 0.0,
            "reasoning": "Knowledge retrieval did not complete.",
            "error": "retrieval_unavailable",
        }
