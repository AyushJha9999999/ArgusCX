"""
ArgusCX — Data Investigation Agent
Fetches order data, payment logs, user history from external systems.
"""
import random
from datetime import datetime, timedelta
from typing import Any, Dict
import structlog
from app.models.schemas import AgentState
from app.core.config import settings

logger = structlog.get_logger(__name__)


async def run_investigation_agent(state: AgentState) -> Dict[str, Any]:
    """Cross-references customer claims with actual order/payment data."""
    logger.info("🔎 Investigation agent running", ticket_id=state.ticket.id)

    if settings.is_demo_mode:
        return _demo_investigation(state)

    try:
        order_data = await _fetch_order_data(state.ticket.customer.id)
        payment_data = await _fetch_payment_data(state.ticket.customer.id)
        user_history = await _fetch_user_history(state.ticket.customer.id)

        anomalies = _detect_anomalies(order_data, payment_data, user_history)

        return {
            "order_data": order_data,
            "payment_data": payment_data,
            "user_history": user_history,
            "anomalies": anomalies,
            "confidence": 0.85,
            "reasoning": f"Investigation complete. Found {len(anomalies)} anomalies.",
        }
    except Exception as e:
        logger.error("Investigation agent failed", error=str(e))
        return _demo_investigation(state) | {"error": str(e)}


def _demo_investigation(state: AgentState) -> Dict[str, Any]:
    """Realistic demo data for hackathon demonstration."""
    customer = state.ticket.customer
    base_date = datetime.utcnow() - timedelta(days=3)

    order_data = {
        "order_id": f"ORD-{random.randint(100000, 999999)}",
        "customer_id": customer.id,
        "status": "delivered",
        "items": [
            {"name": "Premium Wireless Earbuds", "sku": "WE-2024-PRO", "qty": 1, "price": 2499.00}
        ],
        "total_amount": 2499.00,
        "currency": "INR",
        "ordered_at": (base_date - timedelta(days=5)).isoformat(),
        "delivered_at": base_date.isoformat(),
        "delivery_address": "Mumbai, Maharashtra",
        "delivery_partner": "Delhivery",
        "tracking_id": f"DLVRY{random.randint(1000000, 9999999)}",
    }

    payment_data = {
        "payment_id": f"PAY-{random.randint(100000, 999999)}",
        "order_id": order_data["order_id"],
        "status": "captured",
        "method": "UPI",
        "amount": 2499.00,
        "currency": "INR",
        "gateway": "Razorpay",
        "paid_at": (base_date - timedelta(days=5, hours=1)).isoformat(),
        "refund_status": None,
    }

    user_history = {
        "customer_id": customer.id,
        "account_created": (datetime.utcnow() - timedelta(days=customer.account_age_days or 180)).isoformat(),
        "total_orders": customer.previous_tickets + random.randint(5, 20),
        "total_spent_inr": random.randint(10000, 80000),
        "previous_refunds": random.randint(0, 2),
        "previous_fraud_flags": customer.previous_fraud_flags,
        "support_tickets": customer.previous_tickets,
        "loyalty_tier": "Silver",
    }

    anomalies = []
    if customer.previous_fraud_flags > 0:
        anomalies.append(f"Customer has {customer.previous_fraud_flags} previous fraud flag(s)")
    if customer.previous_tickets > 5:
        anomalies.append("High number of previous support tickets")

    return {
        "order_data": order_data,
        "payment_data": payment_data,
        "user_history": user_history,
        "anomalies": anomalies,
        "confidence": 0.9,
        "reasoning": (
            f"Order {order_data['order_id']} delivered on {base_date.date()}. "
            f"Payment captured via {payment_data['method']}. "
            f"Customer has {user_history['total_orders']} total orders. "
            + (f"⚠️ {len(anomalies)} anomalies detected." if anomalies else "No anomalies detected.")
        ),
    }


async def _fetch_order_data(customer_id: str) -> Dict[str, Any]:
    """Fetch from Shopify/internal OMS via MCP connector."""
    # TODO: Implement real Shopify/CRM integration
    raise NotImplementedError("Real order fetch not implemented. Set DEMO_MODE=true.")


async def _fetch_payment_data(customer_id: str) -> Dict[str, Any]:
    """Fetch from Stripe/Razorpay payment gateway."""
    raise NotImplementedError("Real payment fetch not implemented. Set DEMO_MODE=true.")


async def _fetch_user_history(customer_id: str) -> Dict[str, Any]:
    """Fetch from CRM / operational database."""
    raise NotImplementedError("Real user history fetch not implemented. Set DEMO_MODE=true.")


def _detect_anomalies(order: Dict, payment: Dict, history: Dict) -> list:
    """Cross-reference claims with actual data to find inconsistencies."""
    anomalies = []
    if history.get("previous_fraud_flags", 0) > 0:
        anomalies.append("Previous fraud flags on account")
    if history.get("previous_refunds", 0) > 3:
        anomalies.append("Unusually high refund history")
    return anomalies
