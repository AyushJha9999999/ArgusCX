"""
ArgusCX — Resolution Agent
Applies policy engine and makes final resolution decision.
"""
from typing import Any, Dict
import structlog
from app.models.schemas import AgentState, ResolutionDecision, FraudRiskLevel, TicketCategory
from app.core.config import settings

logger = structlog.get_logger(__name__)


async def run_resolution_agent(state: AgentState) -> Dict[str, Any]:
    """
    Applies policy rules to reach a resolution decision.
    Returns decision, customer-facing message, confidence, and escalation flag.
    """
    logger.info("✅ Resolution agent running", ticket_id=state.ticket.id)

    fraud = state.fraud_analysis
    category = state.ticket.category
    order = state.order_data or {}
    payment = state.payment_data or {}

    # ── Fraud Rejection ───────────────────────
    if fraud and fraud.fraud_risk_level in [FraudRiskLevel.CRITICAL]:
        return {
            "decision": ResolutionDecision.FRAUD_REJECT,
            "message": (
                "We've reviewed your request and our verification system detected "
                "inconsistencies in the submitted evidence. This case has been "
                "escalated to our Trust & Safety team. If you believe this is an "
                "error, please contact us with additional documentation."
            ),
            "confidence": 0.95,
            "should_escalate": True,
            "escalation_reason": "Critical fraud indicators detected — AI-generated evidence",
            "reasoning": "FRAUD_REJECT: Critical fraud score from Evidence Verification agent.",
        }

    # ── High Risk → Human Review ──────────────
    if fraud and fraud.fraud_risk_level == FraudRiskLevel.HIGH:
        return {
            "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
            "message": (
                "Your case is under review by our specialized team. "
                "We aim to resolve this within 24 hours. "
                "You'll receive an update via email shortly."
            ),
            "confidence": 0.70,
            "should_escalate": True,
            "escalation_reason": "High fraud risk score — human verification required",
            "reasoning": "ESCALATE: High fraud risk (score > 0.65). Requires human review.",
        }

    # ── Order/Refund Auto-Resolution ──────────
    if category in [TicketCategory.ORDER_REFUND, None] and fraud and not fraud.is_suspicious:
        amount = order.get("total_amount", 0)
        currency = order.get("currency", "INR")
        order_id = order.get("order_id", "your order")
        return {
            "decision": ResolutionDecision.AUTO_RESOLVE,
            "message": (
                f"We've verified your damaged item report for {order_id}. "
                f"A full refund of {currency} {amount:.2f} has been initiated. "
                f"You will receive the amount within 3-5 business days. "
                f"We apologize for the inconvenience."
            ),
            "confidence": 0.92,
            "should_escalate": False,
            "escalation_reason": None,
            "reasoning": (
                f"AUTO_RESOLVE: Order verified ({order_id}), "
                f"evidence clean (fraud_score={fraud.fraud_score:.2f}), "
                f"policy permits full refund for verified damage."
            ),
        }

    # ── Payment Dispute ───────────────────────
    if category == TicketCategory.BILLING_PAYMENT:
        py_id = payment.get("payment_id", "your payment")
        return {
            "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
            "message": (
                f"We're investigating your payment dispute for {py_id}. "
                f"Our billing team has been notified and will contact you within 2 business days. "
                f"Reference case: #{state.ticket.id[:8].upper()}"
            ),
            "confidence": 0.82,
            "should_escalate": True,
            "escalation_reason": "Payment dispute requires billing team review",
            "reasoning": "ESCALATE: Payment disputes require human billing team investigation.",
        }

    # ── Account Issues ────────────────────────
    if category == TicketCategory.ACCOUNT:
        return {
            "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
            "message": (
                "For security reasons, your account issue has been escalated "
                "to our Account Security team. We'll contact you via your registered "
                "email within 24 hours."
            ),
            "confidence": 0.88,
            "should_escalate": True,
            "escalation_reason": "Account security issue requires identity verification",
            "reasoning": "ESCALATE: Account issues require identity verification by security team.",
        }

    # ── Low Confidence → Request More Info ────
    if not state.retrieved_policies and not order:
        return {
            "decision": ResolutionDecision.REQUEST_MORE_INFO,
            "message": (
                "Thank you for reaching out. To better assist you, could you please "
                "provide your order number, a description of the issue, and any "
                "relevant photos or documents?"
            ),
            "confidence": 0.45,
            "should_escalate": False,
            "escalation_reason": None,
            "reasoning": "REQUEST_MORE_INFO: Insufficient context to make a resolution decision.",
        }

    # ── Default Escalation ────────────────────
    return {
        "decision": ResolutionDecision.ESCALATE_TO_HUMAN,
        "message": (
            "We've reviewed your case and it requires personalized attention. "
            "A support specialist will contact you within 4 hours."
        ),
        "confidence": 0.60,
        "should_escalate": True,
        "escalation_reason": "Could not auto-resolve with available context",
        "reasoning": "ESCALATE: Default fallback — insufficient confidence for auto-resolution.",
    }
