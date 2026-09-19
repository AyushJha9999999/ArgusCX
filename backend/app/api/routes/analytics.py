"""
ArgusCX — Analytics Routes
Returns live statistics computed from the in-memory ticket store.
Also exposes trend and fraud-breakdown endpoints for the dashboard.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from app.models.schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics")


async def _get_tickets():
    from app.db.mongodb import get_tickets_col
    from app.models.schemas import Ticket
    
    col = get_tickets_col()
    if col is None:
        return []
    
    docs = await col.find({}).to_list(length=None)
    return [Ticket(**doc) for doc in docs]


@router.get("/company")
async def company_analytics(request: Request):
    """
    Returns full dashboard metrics tailored to the authenticated company.
    Builds the monthly trends, KPIs, and recent activity from the MongoDB tickets collection.
    """
    # 1. Identity
    identity = getattr(request.state, "authenticated_user", {})
    email = identity.get("email", "")
    sub = identity.get("sub", "")
    
    # Look up real company profile from MongoDB
    from app.db.mongodb import get_users_col
    users_col = get_users_col()
    profile = await users_col.find_one({"sub": sub}) if users_col is not None and sub else None
    company_name = (profile or {}).get("company_name") or email.split("@")[0].title() if email else "ArgusCX"
    tenant_id = sub  # sessions are scoped per user sub

    
    # 2. Get tickets (Filter by tenant if applicable)
    from app.db.mongodb import get_tickets_col
    from app.models.schemas import Ticket
    col = get_tickets_col()
    
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
        
    docs = await col.find(query).to_list(length=None) if col is not None else []
    tickets = [Ticket(**doc) for doc in docs]
    
    # 3. Compute metrics
    total = len(tickets)
    resolved = sum(1 for t in tickets if t.status.upper() in {"RESOLVED", "CLOSED", "AUTO_RESOLVED"})
    escalated = sum(1 for t in tickets if t.status.upper() == "ESCALATED")
    fraud = sum(1 for t in tickets if t.status.upper() == "FRAUD_FLAGGED")
    
    res_rate = (resolved / total) if total > 0 else 0.0
    fraud_rate = (fraud / total) if total > 0 else 0.0
    
    # AI Confidence & Response time average
    ai_tickets = [t for t in tickets if t.ai_confidence is not None]
    avg_conf = sum(t.ai_confidence for t in ai_tickets) / len(ai_tickets) if ai_tickets else 0.92
    
    ms_times = [t.metadata.get("processing_time_ms", 1500) for t in ai_tickets if t.metadata]
    avg_ms = sum(ms_times) / len(ms_times) if ms_times else 1250

    # 4. Breakdowns
    cat_counts = {}
    chan_counts = {}
    for t in tickets:
        cat = t.category.lower() if t.category else "other"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
        chan = t.metadata.get("source", "email").lower() if t.metadata else "email"
        chan_counts[chan] = chan_counts.get(chan, 0) + 1
        
    top_issues = [{"category": k, "count": v} for k, v in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    # 5. Monthly Trends (Last 6 months placeholder logic adapted to actual data if present)
    # We will aggregate by YYYY-MM
    now = datetime.utcnow()
    months_labels = []
    vols = [0]*6; res = [0]*6; frd = [0]*6; esc = [0]*6
    
    for i in range(5, -1, -1):
        d = now - timedelta(days=30*i)
        months_labels.append(d.strftime("%b %Y"))
        
    # Bin tickets by month
    for t in tickets:
        # Assuming created_at is string ISO date
        try:
            dt = datetime.fromisoformat(t.created_at.replace("Z", "+00:00"))
        except:
            dt = now
            
        months_ago = (now.year - dt.year) * 12 + now.month - dt.month
        if 0 <= months_ago < 6:
            idx = 5 - months_ago
            vols[idx] += 1
            if t.status.upper() in {"RESOLVED", "CLOSED", "AUTO_RESOLVED"}: res[idx] += 1
            elif t.status.upper() == "ESCALATED": esc[idx] += 1
            elif t.status.upper() == "FRAUD_FLAGGED": frd[idx] += 1

    # 6. Recent Activity
    sorted_tickets = sorted(tickets, key=lambda t: t.created_at, reverse=True)[:10]
    recent = []
    for t in sorted_tickets:
        try:
            dt = datetime.fromisoformat(t.created_at.replace("Z", "+00:00"))
            hrs = (now - dt).total_seconds() / 3600.0
        except:
            hrs = 1.0
            
        color = "#94a3b8"
        if t.status.upper() in {"RESOLVED", "AUTO_RESOLVED"}: color = "#10b981"
        elif t.status.upper() == "ESCALATED": color = "#f59e0b"
        elif t.status.upper() == "FRAUD_FLAGGED": color = "#ef4444"
            
        recent.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status.replace("_", " ").title(),
            "status_color": color,
            "confidence": t.ai_confidence or 0.85,
            "hours_ago": round(hrs, 1),
            "category": t.category or "General"
        })

    # Output schema matching CompanyData
    return {
        "company_name": company_name,
        "user_email": email,
        "plan_tier": "Enterprise AI",
        "plan_limit": 50000,
        "plan_used": total,
        "months": months_labels,
        "monthly_volumes": vols,
        "monthly_resolved": res,
        "monthly_fraud": frd,
        "monthly_escalated": esc,
        "kpis": {
            "total_tickets": total,
            "total_resolved": resolved,
            "total_fraud": fraud,
            "total_escalated": escalated,
            "resolution_rate": res_rate,
            "fraud_rate": fraud_rate,
            "avg_confidence": avg_conf,
            "avg_response_ms": avg_ms
        },
        "category_breakdown": cat_counts,
        "channel_breakdown": chan_counts,
        "top_issues": top_issues,
        "recent_activity": recent
    }

@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary():
    """Live aggregated analytics computed from all processed tickets."""
    tickets = await _get_tickets()
    total = len(tickets)

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
    tickets = await _get_tickets()
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

    return {"trends": hours, "period": "last_24h"}


@router.get("/fraud-stats")
async def fraud_stats():
    """Fraud detection breakdown for the dashboard gauge."""
    tickets = await _get_tickets()
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
    tickets = await _get_tickets()
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

    return {"clusters": result, "spike_detected": any(c["spike"] for c in result)}


@router.get("/company")
async def company_analytics(request: Request):
    """
    Company-scoped analytics dashboard.
    All data is computed live from the real ticket store — no hardcoded values.
    """
    from app.models.schemas import TicketStatus

    # ── Resolve company identity from JWT / API-key middleware ─────────
    company_name = "Your Company"
    user_email = ""
    if hasattr(request.state, "authenticated_user") and request.state.authenticated_user:
        user = request.state.authenticated_user
        user_email = user.get("email", "")
        company_name = user.get("name") or (user_email.split("@")[0] if "@" in user_email else "Your Company")
    elif hasattr(request.state, "company_name") and request.state.company_name:
        company_name = request.state.company_name

    # ── Pull all real tickets ──────────────────────────────────────────
    tickets = await _get_tickets()
    now = datetime.utcnow()

    # ── 12-month bucketing ────────────────────────────────────────────
    # Build one bucket per calendar month for the last 12 months
    months = []
    monthly_volumes   = []
    monthly_resolved  = []
    monthly_fraud     = []
    monthly_escalated = []

    for i in range(11, -1, -1):
        # Compute start/end of this calendar month bucket
        bucket_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for _ in range(i):
            bucket_end = (bucket_end - timedelta(days=1)).replace(day=1)
        if i > 0:
            bucket_start = bucket_end
            bucket_end_next = bucket_end
            # Step forward one month
            m = bucket_end.month + 1 if bucket_end.month < 12 else 1
            y = bucket_end.year if bucket_end.month < 12 else bucket_end.year + 1
            bucket_end_next = bucket_end.replace(year=y, month=m)
        else:
            bucket_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            bucket_end_next = now

        # Re-derive cleanly: bucket i months ago
        ref = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for _ in range(i):
            ref = (ref - timedelta(days=1)).replace(day=1)
        bucket_start = ref
        m2 = ref.month + 1 if ref.month < 12 else 1
        y2 = ref.year if ref.month < 12 else ref.year + 1
        bucket_end_real = ref.replace(year=y2, month=m2) if i > 0 else now

        label = ref.strftime("%b %Y")
        months.append(label)

        in_bucket = [t for t in tickets if bucket_start <= t.created_at < bucket_end_real]
        monthly_volumes.append(len(in_bucket))
        monthly_resolved.append(sum(1 for t in in_bucket if t.status == TicketStatus.AUTO_RESOLVED))
        monthly_fraud.append(sum(1 for t in in_bucket if t.status == TicketStatus.FRAUD_FLAGGED or
                                  (t.fraud_analysis and t.fraud_analysis.fraud_score >= 0.65)))
        monthly_escalated.append(sum(1 for t in in_bucket if t.status == TicketStatus.ESCALATED))

    # ── Lifetime KPIs from all tickets ────────────────────────────────
    total = len(tickets)
    total_resolved  = sum(1 for t in tickets if t.status == TicketStatus.AUTO_RESOLVED)
    total_fraud     = sum(1 for t in tickets if t.status == TicketStatus.FRAUD_FLAGGED or
                           (t.fraud_analysis and t.fraud_analysis.fraud_score >= 0.65))
    total_escalated = sum(1 for t in tickets if t.status == TicketStatus.ESCALATED)

    resolution_rate = round(total_resolved / max(total, 1), 3)
    fraud_rate      = round(total_fraud    / max(total, 1), 3)

    avg_confidence = round(
        sum(t.confidence_score for t in tickets) / total, 3
    ) if total else 0.0

    # Avg processing time from agent steps
    response_times = []
    for t in tickets:
        if t.agent_steps:
            durations = [s.duration_ms for s in t.agent_steps if s.duration_ms is not None]
            if durations:
                response_times.append(sum(durations))
    avg_response_ms = round(sum(response_times) / len(response_times)) if response_times else 0

    # ── Category breakdown (real) ─────────────────────────────────────
    category_breakdown: dict = {}
    for t in tickets:
        cat = t.category.value if t.category else "general"
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    # ── Channel breakdown (real) ──────────────────────────────────────
    channel_breakdown: dict = {}
    for t in tickets:
        ch = t.channel.value if t.channel else "web"
        channel_breakdown[ch] = channel_breakdown.get(ch, 0) + 1

    # ── Top issues ────────────────────────────────────────────────────
    top_issues = sorted(
        [{"category": k, "count": v} for k, v in category_breakdown.items()],
        key=lambda x: x["count"], reverse=True
    )[:5]

    # ── Recent activity (last 10 real tickets, newest first) ──────────
    status_color_map = {
        "auto_resolved": "green", "escalated": "yellow",
        "fraud_flagged": "red",   "human_review": "blue",
        "open": "gray",           "in_progress": "blue",
        "closed": "gray",
    }
    sorted_tickets = sorted(tickets, key=lambda t: t.created_at, reverse=True)[:10]
    recent_activity = []
    for t in sorted_tickets:
        status_val = t.status.value if t.status else "open"
        age_hours  = max(0, int((now - t.created_at).total_seconds() / 3600))
        recent_activity.append({
            "id":           t.id,
            "subject":      t.subject,
            "status":       status_val,
            "status_color": status_color_map.get(status_val, "gray"),
            "confidence":   round(t.confidence_score, 2),
            "hours_ago":    age_hours,
            "category":     t.category.value if t.category else "general",
        })

    # ── Plan usage from settings ──────────────────────────────────────
    from app.core.config import settings as app_settings
    plan_limit = getattr(app_settings, "PLAN_TICKET_LIMIT", None) or 5000
    plan_used  = total
    plan_tier  = getattr(app_settings, "PLAN_TIER", None) or ("Enterprise" if plan_used >= 3000 else "Professional")

    return {
        "company_name":       company_name,
        "user_email":         user_email,
        "plan_tier":          plan_tier,
        "plan_limit":         plan_limit,
        "plan_used":          plan_used,
        "months":             months,
        "monthly_volumes":    monthly_volumes,
        "monthly_resolved":   monthly_resolved,
        "monthly_fraud":      monthly_fraud,
        "monthly_escalated":  monthly_escalated,
        "kpis": {
            "total_tickets":   total,
            "total_resolved":  total_resolved,
            "total_fraud":     total_fraud,
            "total_escalated": total_escalated,
            "resolution_rate": resolution_rate,
            "fraud_rate":      fraud_rate,
            "avg_confidence":  avg_confidence,
            "avg_response_ms": avg_response_ms,
        },
        "category_breakdown": category_breakdown,
        "channel_breakdown":  channel_breakdown,
        "top_issues":         top_issues,
        "recent_activity":    recent_activity,
    }

