"""
ArgusCX — RAG Indexer
Initializes and populates the vector store with knowledge base documents.
"""
import structlog
from app.core.config import settings
from app.rag.retriever import get_vector_store

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────
#  Sample Knowledge Base (Hackathon Demo)
# ─────────────────────────────────────────────

SAMPLE_POLICIES = [
    {"title": "Damaged Item Refund Policy", "content": "Customers reporting damaged items are eligible for a full refund within 7 days of delivery. Clear photographic evidence of the damage and original packaging is required. Refunds are processed within 3-5 business days after verification.", "category": "policies", "tags": ["refund", "damaged", "delivery"]},
    {"title": "Fraud Detection Policy", "content": "All evidence submitted for refund claims undergoes automated verification including EXIF metadata analysis, AI-artifact detection, and C2PA Content Credentials verification. Suspicious evidence is escalated to the Trust & Safety team. False claims result in account suspension.", "category": "policies", "tags": ["fraud", "evidence", "verification"]},
    {"title": "Payment Dispute Resolution", "content": "Payment disputes must be raised within 30 days of the transaction. Disputes are cross-verified with the payment gateway (Stripe/Razorpay). Resolution timeline: 2-5 business days. For disputes above ₹10,000, escalation to billing team mandatory.", "category": "policies", "tags": ["payment", "dispute", "billing"]},
    {"title": "Account Security Policy", "content": "Suspicious account activity (multiple failed logins, unusual location changes) triggers automatic account lock. Identity verification required for unlock. Human security team reviews all flagged accounts within 24 hours.", "category": "policies", "tags": ["account", "security", "identity"]},
    {"title": "Escalation Thresholds Policy", "content": "Cases with agent confidence score below 75% or fraud risk score above 65% are automatically escalated to human agents. High-value disputes (>₹50,000) always require human approval. Escalated cases receive full AI-generated case files for human review.", "category": "policies", "tags": ["escalation", "confidence", "risk"]},
    {"title": "Repeat Contact Policy", "content": "Customers contacting support more than 3 times for the same issue are automatically assigned to a senior agent. Repeat contacts incur internal tracking to identify systemic issues. Resolution analytics are fed back to improve automated resolution rates.", "category": "policies", "tags": ["repeat", "contact", "senior"]},
    {"title": "Replacement vs Refund Policy", "content": "For eligible items, customers may choose between a full refund or a replacement. Replacements are dispatched within 48 hours for in-stock items. Refunds are processed within 3-5 business days. The choice must be made within 24 hours of case approval.", "category": "policies", "tags": ["replacement", "refund", "choice"]},
]

SAMPLE_FAQS = [
    {"title": "How long does a refund take?", "content": "Approved refunds are processed within 3-5 business days. UPI and net banking refunds may appear faster (same day) while card refunds take 5-7 business days depending on your bank.", "category": "faqs", "tags": ["refund", "timeline", "payment"]},
    {"title": "What evidence is needed for a damaged item?", "content": "Please provide: 1) Clear photos of the damaged item, 2) Photos of the original packaging including the shipping label, 3) Your order number. Videos are also accepted. All evidence is verified by our AI system.", "category": "faqs", "tags": ["damaged", "evidence", "photos"]},
    {"title": "How do I track my refund?", "content": "You will receive an email confirmation once your refund is approved. You can track your refund status in the 'My Orders' section of the app or website. Contact support if refund doesn't appear after 7 business days.", "category": "faqs", "tags": ["refund", "track", "status"]},
    {"title": "What if my account is locked?", "content": "Account locks are triggered by security measures. To unlock: 1) Click 'Forgot Password' to reset, 2) Verify your identity via OTP on registered mobile, 3) If issue persists, contact support with government ID proof.", "category": "faqs", "tags": ["account", "locked", "unlock"]},
    {"title": "Can I get an exchange instead of refund?", "content": "Yes, exchanges are available within 7 days of delivery for eligible items. The replacement item will be dispatched within 48 hours after the original item is picked up. Some categories (electronics, personal care) have different exchange windows.", "category": "faqs", "tags": ["exchange", "return", "replacement"]},
]

SAMPLE_PAST_TICKETS = [
    {"title": "Resolved: Damaged Earbuds - Genuine Case", "content": "Customer reported damaged earbuds with clear packaging photos. EXIF verified, no manipulation. Refund of ₹2499 approved and processed. Resolution time: 4 minutes (auto-resolved).", "category": "past_tickets", "tags": ["resolved", "damaged", "electronics", "auto_resolved"]},
    {"title": "Escalated: Fraudulent Damage Claim Detected", "content": "Customer submitted AI-generated damage photos. Fraud score: 0.94. EXIF metadata absent. C2PA invalid. Case escalated to Trust & Safety. Account flagged for review. Refund denied.", "category": "past_tickets", "tags": ["fraud", "escalated", "ai_generated", "denied"]},
    {"title": "Resolved: Payment Double Charge", "content": "Customer reported double charge of ₹1,200. Payment gateway logs confirmed duplicate transaction. Full refund issued for duplicate amount within 2 business days. Customer satisfied.", "category": "past_tickets", "tags": ["payment", "resolved", "duplicate", "billing"]},
    {"title": "Escalated: Account Takeover Attempt", "content": "Multiple failed login attempts from different IP addresses detected. Account automatically locked. Risk score: 0.88. Security team verified identity via government ID. Account restored after 24 hours.", "category": "past_tickets", "tags": ["account", "security", "escalated", "takeover"]},
    {"title": "Resolved: Late Delivery Complaint", "content": "Package delayed by 3 days beyond promised date. Tracking confirmed delivery partner issue. Customer offered ₹100 voucher as compensation + priority shipping on next order. Auto-resolved.", "category": "past_tickets", "tags": ["delivery", "late", "compensation", "auto_resolved"]},
]

ALL_DOCUMENTS = SAMPLE_POLICIES + SAMPLE_FAQS + SAMPLE_PAST_TICKETS


async def init_rag_index():
    """Initialize the RAG vector store on application startup."""
    logger.info("📚 Initializing RAG knowledge base...")
    try:
        store = await get_vector_store()
        await store.add_documents(ALL_DOCUMENTS)
        logger.info(
            "✅ RAG index initialized",
            total_documents=len(ALL_DOCUMENTS),
            policies=len(SAMPLE_POLICIES),
            faqs=len(SAMPLE_FAQS),
            past_tickets=len(SAMPLE_PAST_TICKETS),
        )
    except Exception as e:
        logger.warning("⚠️ RAG index initialization failed — using in-memory fallback", error=str(e))
