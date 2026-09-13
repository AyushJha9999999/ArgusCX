"""ArgusCX — Analytics Routes"""
from fastapi import APIRouter
from app.models.schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics")

@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary():
    """Return aggregated analytics for the dashboard."""
    return AnalyticsSummary(
        total_tickets=47,
        auto_resolved=31,
        escalated=10,
        fraud_flagged=6,
        avg_resolution_time_ms=3420.0,
        avg_confidence_score=0.84,
        resolution_rate=0.66,
        fraud_detection_rate=0.13,
        tickets_by_category={"order_refund": 22, "billing_payment": 12, "technical": 7, "account": 4, "fraud": 2},
        tickets_by_channel={"web": 18, "mobile": 14, "whatsapp": 9, "email": 6},
        tickets_by_status={"auto_resolved": 31, "escalated": 10, "fraud_flagged": 6},
    )
