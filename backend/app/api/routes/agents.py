"""ArgusCX — Stub routes for agents, knowledge, evidence, auth"""
from fastapi import APIRouter

router = APIRouter(prefix="/agents")

@router.get("")
async def list_agents():
    return [
        {"id": "orchestrator", "type": "orchestrator", "status": "idle", "description": "Master orchestrator — LangGraph"},
        {"id": "retrieval", "type": "information_retrieval", "status": "idle", "description": "RAG over policies, FAQs, past tickets"},
        {"id": "investigation", "type": "data_investigation", "status": "idle", "description": "Fetches order, payment, user history"},
        {"id": "verification", "type": "evidence_verification", "status": "idle", "description": "EXIF, AI-artifact, C2PA analysis"},
        {"id": "resolution", "type": "resolution", "status": "idle", "description": "Policy engine + refund decision"},
        {"id": "escalation", "type": "escalation", "status": "idle", "description": "Human handoff + Slack alerts"},
    ]
