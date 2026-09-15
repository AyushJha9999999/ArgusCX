"""
ArgusCX — Analytics Routes
Returns live statistics computed from the in-memory ticket store.
Also exposes trend and fraud-breakdown endpoints for the dashboard.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter
from app.models.schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics")


def _get_tickets():
    """Lazy import to avoid circular dependency with tickets module."""
    from app.api.routes.tickets import _tickets
    return list(_tickets.values())


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary():
    """Live aggregated analytics computed from all processed tickets."""
    tickets = _get_tickets()
    total = len(tickets)

    if total == 0:
        # Return seeded demo data when no tickets have been submitted yet
        return AnalyticsSummary(
            total_tickets=47,
            auto_resolved=31,
            escalated=10,
            fraud_flagged=6,
            avg_resolution_time_ms=3420.0,
            avg_confidence_score=0.84,
            resolution_rate=0.66,
            fraud_detection_rate=0.13,
            tickets_by_category={
                "order_refund": 22,
                "billing_payment": 12,
                "technical": 7,
                "account": 4,
                "fraud": 2,
            },
            tickets_by_channel={
                "web": 18,
                "mobile": 14,
                "whatsapp": 9,
                "email": 6,
            },
            tickets_by_status={
                "auto_resolved": 31,
                "escalated": 10,
                "fraud_flagged": 6,
            },
        )

    from app.models.schemas import TicketStatus

    auto_resolved = sum(1 for t in tickets if t.status == TicketStatus.AUTO_RESOLVED)
    escalated = sum(1 for t in tickets if t.status == TicketStatus.ESCALATED)
    fraud_flagged = sum(
        1 for t in tickets
        if t.status == TicketStatus.FRAUD_FLAGGED
        or (t.fraud_analysis and t.fraud_analysis.fraud_score >= 0.65)
    )

    avg_confidence = round(
        sum(t.confidence_score for t in tickets) / total, 3
    ) if total else 0.0

    resolution_rate = round(auto_resolved / total, 3) if total else 0.0
    fraud_rate = round(fraud_flagged / total, 3) if total else 0.0

    by_category: dict = {}
    by_channel: dict = {}
    by_status: dict = {}

    for t in tickets:
        cat = t.category.value if t.category else "general"
        by_category[cat] = by_category.get(cat, 0) + 1
        ch = t.channel.value if t.channel else "web"
        by_channel[ch] = by_channel.get(ch, 0) + 1
        st = t.status.value if t.status else "open"
        by_status[st] = by_status.get(st, 0) + 1

    return AnalyticsSummary(
        total_tickets=total,
        auto_resolved=auto_resolved,
        escalated=escalated,
        fraud_flagged=fraud_flagged,
        avg_confidence_score=avg_confidence,
        resolution_rate=resolution_rate,
        fraud_detection_rate=fraud_rate,
        tickets_by_category=by_category,
        tickets_by_channel=by_channel,
        tickets_by_status=by_status,
        period_start=min((t.created_at for t in tickets), default=None),
        period_end=datetime.utcnow(),
    )


@router.get("/trends")
async def analytics_trends():
    """
    Returns hourly ticket volume for the last 24 hours.
    Used by the dashboard complaint-spike chart.
    """
    tickets = _get_tickets()
    now = datetime.utcnow()
    hours = []
    for i in range(23, -1, -1):
        bucket_start = now - timedelta(hours=i + 1)
        bucket_end = now - timedelta(hours=i)
        label = bucket_end.strftime("%H:00")
        count = sum(
            1 for t in tickets
            if bucket_start <= t.created_at < bucket_end
        )
        hours.append({"hour": label, "tickets": count})

    # Seed with realistic demo data if no real tickets yet
    if all(h["tickets"] == 0 for h in hours):
        import random
        base = [1, 0, 1, 0, 2, 3, 5, 8, 12, 14, 11, 9, 7, 8, 10, 13, 15, 12, 9, 6, 4, 3, 2, 1]
        for i, h in enumerate(hours):
            h["tickets"] = base[i] + random.randint(0, 2)

    return {"trends": hours, "period": "last_24h"}


@router.get("/fraud-stats")
async def fraud_stats():
    """Fraud detection breakdown for the dashboard gauge."""
    tickets = _get_tickets()
    total = len(tickets)

    genuine = sum(
        1 for t in tickets
        if t.fraud_analysis and not t.fraud_analysis.is_suspicious
    )
    suspicious = sum(
        1 for t in tickets
        if t.fraud_analysis and t.fraud_analysis.is_suspicious
        and t.fraud_analysis.fraud_score < 0.8
    )
    critical = sum(
        1 for t in tickets
        if t.fraud_analysis and t.fraud_analysis.fraud_score >= 0.8
    )
    no_evidence = total - genuine - suspicious - critical

    if total == 0:
        return {
            "total_with_evidence": 24,
            "genuine": 18,
            "suspicious": 4,
            "critical_fraud": 2,
            "no_evidence": 23,
            "fraud_rate": 0.25,
        }

    return {
        "total_with_evidence": genuine + suspicious + critical,
        "genuine": genuine,
        "suspicious": suspicious,
        "critical_fraud": critical,
        "no_evidence": no_evidence,
        "fraud_rate": round((suspicious + critical) / max(genuine + suspicious + critical, 1), 3),
    }


@router.get("/complaint-clusters")
async def complaint_clusters():
    """
    Root-cause complaint clustering — groups tickets by category
    and flags categories with rapid growth (spike detection).
    """
    tickets = _get_tickets()
    now = datetime.utcnow()
    recent_window = now - timedelta(hours=6)

    clusters = {}
    for t in tickets:
        cat = t.category.value if t.category else "general"
        if cat not in clusters:
            clusters[cat] = {"category": cat, "total": 0, "recent": 0, "spike": False}
        clusters[cat]["total"] += 1
        if t.created_at >= recent_window:
            clusters[cat]["recent"] += 1

    # Flag spike if >40% of all tickets in a category came in last 6h
    for c in clusters.values():
        if c["total"] > 0 and (c["recent"] / c["total"]) > 0.4:
            c["spike"] = True

    result = sorted(clusters.values(), key=lambda x: x["total"], reverse=True)

    if not result:
        result = [
            {"category": "order_refund", "total": 22, "recent": 11, "spike": True},
            {"category": "billing_payment", "total": 12, "recent": 3, "spike": False},
            {"category": "technical", "total": 7, "recent": 2, "spike": False},
            {"category": "account", "total": 4, "recent": 1, "spike": False},
        ]

    return {"clusters": result, "spike_detected": any(c["spike"] for c in result)}
