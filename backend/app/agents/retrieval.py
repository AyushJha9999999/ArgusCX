"""
ArgusCX — Information Retrieval Agent
Searches policies, FAQs, and past tickets using RAG.
"""
from typing import Any, Dict
import structlog
from app.models.schemas import AgentState
from app.rag.retriever import retrieve_documents
from app.core.config import settings

logger = structlog.get_logger(__name__)

DEMO_POLICIES = [
    "Refund Policy: Orders damaged in transit are eligible for full refund within 7 days of delivery. Photo evidence required.",
    "Fraud Policy: Images showing signs of manipulation will be reviewed by the fraud team before any refund is processed.",
    "Payment Dispute Policy: Payment disputes must be raised within 30 days. Cross-verification with payment gateway required.",
    "Account Security Policy: Suspicious login attempts trigger automatic account lock and human review.",
    "Escalation Policy: Cases with confidence score below 75% or fraud risk above 65% are automatically escalated to human agents.",
]

DEMO_FAQS = [
    "Q: How long does a refund take? A: Approved refunds are processed within 3-5 business days.",
    "Q: What evidence do I need for a damaged item? A: Clear photos of the damage and the packaging are required.",
    "Q: Can I get a replacement instead of a refund? A: Yes, replacement is available for eligible items within 48 hours.",
]


async def run_retrieval_agent(state: AgentState) -> Dict[str, Any]:
    """
    Retrieves relevant policies, FAQs, and similar past tickets
    from the RAG knowledge base.
    """
    query = f"{state.ticket.subject} {state.ticket.message}"
    logger.info("📚 Retrieval agent searching knowledge base", query=query[:100])

    if settings.is_demo_mode:
        return _demo_retrieval(state)

    try:
        # Real RAG retrieval
        policy_results = await retrieve_documents(query, namespace="policies", top_k=3)
        faq_results = await retrieve_documents(query, namespace="faqs", top_k=2)
        past_results = await retrieve_documents(query, namespace="past_tickets", top_k=2)

        return {
            "policies": [doc.content for doc in policy_results.documents],
            "faqs": [doc.content for doc in faq_results.documents],
            "past_tickets": [doc.content for doc in past_results.documents],
            "confidence": 0.9,
            "reasoning": f"Retrieved {len(policy_results.documents)} policies, "
                         f"{len(faq_results.documents)} FAQs, "
                         f"{len(past_results.documents)} similar tickets.",
        }
    except Exception as e:
        logger.error("Retrieval agent failed", error=str(e))
        return _demo_retrieval(state) | {"error": str(e)}


def _demo_retrieval(state: AgentState) -> Dict[str, Any]:
    """Demo mode — return curated policies based on ticket category."""
    category = state.ticket.category
    if category and "refund" in category.value:
        policies = DEMO_POLICIES[:2]
    elif category and "fraud" in category.value:
        policies = [DEMO_POLICIES[1], DEMO_POLICIES[4]]
    elif category and "payment" in category.value:
        policies = [DEMO_POLICIES[2]]
    elif category and "account" in category.value:
        policies = [DEMO_POLICIES[3], DEMO_POLICIES[4]]
    else:
        policies = DEMO_POLICIES[:3]

    return {
        "policies": policies,
        "faqs": DEMO_FAQS[:2],
        "past_tickets": ["Similar ticket #4821: Damaged item, refund approved after photo verification."],
        "confidence": 0.88,
        "reasoning": f"Retrieved {len(policies)} relevant policies and 2 FAQs from knowledge base.",
    }
