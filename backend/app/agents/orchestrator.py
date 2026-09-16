"""
ArgusCX — Agent Orchestrator
LangGraph StateGraph that routes tickets through specialist agents.
"""
import time
from typing import Literal
import structlog
from langgraph.graph import StateGraph, END

from app.models.schemas import (
    AgentState, AgentType, AgentStatus, ResolutionDecision,
    FraudRiskLevel, AgentStep
)
from app.core.config import settings
from app.agents.retrieval import run_retrieval_agent
from app.agents.investigation import run_investigation_agent
from app.agents.verification import run_verification_agent
from app.agents.resolution import run_resolution_agent
from app.agents.escalation import run_escalation_agent
from app.services.scoring_engine import compute_scores

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────
#  NODE FUNCTIONS (Each agent is a node)
# ─────────────────────────────────────────────

async def retrieval_node(state: AgentState) -> AgentState:
    """Information Retrieval Agent — RAG over policies, FAQs, past tickets."""
    logger.info("🔍 Retrieval agent running", ticket_id=state.ticket.id)
    state.current_agent = AgentType.INFORMATION_RETRIEVAL
    start = time.time()

    result = await run_retrieval_agent(state)
    state.retrieved_policies = result.get("policies", [])
    state.retrieved_faqs = result.get("faqs", [])
    state.retrieved_past_tickets = result.get("past_tickets", [])

    _add_agent_step(state, AgentType.INFORMATION_RETRIEVAL, result, start)
    state.completed_agents.append(AgentType.INFORMATION_RETRIEVAL)
    return state


async def investigation_node(state: AgentState) -> AgentState:
    """Data Investigation Agent — Fetches order, payment, and user history."""
    logger.info("🔎 Investigation agent running", ticket_id=state.ticket.id)
    state.current_agent = AgentType.DATA_INVESTIGATION
    start = time.time()

    result = await run_investigation_agent(state)
    state.order_data = result.get("order_data")
    state.payment_data = result.get("payment_data")
    state.user_history = result.get("user_history")

    _add_agent_step(state, AgentType.DATA_INVESTIGATION, result, start)
    state.completed_agents.append(AgentType.DATA_INVESTIGATION)
    return state


async def verification_node(state: AgentState) -> AgentState:
    """Evidence & Fraud Verification Agent — Image forensics, EXIF, C2PA."""
    logger.info("🛡️ Verification agent running", ticket_id=state.ticket.id)
    state.current_agent = AgentType.EVIDENCE_VERIFICATION
    start = time.time()

    result = await run_verification_agent(state)
    state.fraud_analysis = result.get("fraud_analysis")
    # Risk score will be computed by scoring engine after resolution

    _add_agent_step(state, AgentType.EVIDENCE_VERIFICATION, result, start)
    state.completed_agents.append(AgentType.EVIDENCE_VERIFICATION)
    return state


async def resolution_node(state: AgentState) -> AgentState:
    """Resolution Agent — Applies policy engine and makes resolution decision."""
    logger.info("✅ Resolution agent running", ticket_id=state.ticket.id)
    state.current_agent = AgentType.RESOLUTION
    start = time.time()

    result = await run_resolution_agent(state)
    state.resolution_decision = result.get("decision")
    state.resolution_message = result.get("message")
    llm_confidence = result.get("confidence", 0.0)
    state.should_escalate = result.get("should_escalate", False)
    state.escalation_reason = result.get("escalation_reason")

    # ── Multi-signal scoring engine ───────────────────────────
    # Runs AFTER all agents complete so it has all available signals.
    # Produces three distinct scores (fraud ≠ risk ≠ confidence).
    try:
        scores = compute_scores(state)
        state.risk_score = scores["risk_score"]
        # Blend LLM confidence with signal-based confidence (60/40)
        if llm_confidence > 0:
            state.confidence_score = round(
                llm_confidence * 0.60 + scores["confidence_score"] * 0.40, 3
            )
        else:
            state.confidence_score = scores["confidence_score"]
        # Update fraud_analysis fraud_score with engine score if more refined
        if state.fraud_analysis:
            import dataclasses
            state.fraud_analysis = state.fraud_analysis.model_copy(
                update={"fraud_score": scores["fraud_score"]}
            )
        logger.info(
            "Scoring engine applied",
            fraud=scores["fraud_score"],
            risk=scores["risk_score"],
            confidence=state.confidence_score,
        )
    except Exception as e:
        logger.error("Scoring engine failed, using LLM confidence", error=str(e))
        state.confidence_score = llm_confidence

    _add_agent_step(state, AgentType.RESOLUTION, result, start)
    state.completed_agents.append(AgentType.RESOLUTION)
    return state


async def escalation_node(state: AgentState) -> AgentState:
    """Escalation Agent — Packages full case file for human handoff."""
    logger.info("🚨 Escalation agent running", ticket_id=state.ticket.id)
    state.current_agent = AgentType.ESCALATION
    start = time.time()

    result = await run_escalation_agent(state)

    _add_agent_step(state, AgentType.ESCALATION, result, start)
    state.completed_agents.append(AgentType.ESCALATION)
    return state


# ─────────────────────────────────────────────
#  ROUTING LOGIC
# ─────────────────────────────────────────────

def should_verify_evidence(state: AgentState) -> Literal["verification", "resolution"]:
    """Route to verification if evidence files are present."""
    if state.ticket.evidence_files and settings.FEATURE_FRAUD_DETECTION_ENABLED:
        return "verification"
    return "resolution"


def should_escalate(state: AgentState) -> Literal["escalation", END]:
    """Route to escalation if confidence is low or fraud risk is high."""
    fraud = state.fraud_analysis

    # High fraud risk → escalate
    if fraud and fraud.fraud_risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
        state.should_escalate = True
        return "escalation"

    # Low confidence → escalate
    if state.confidence_score < settings.AGENT_CONFIDENCE_THRESHOLD:
        state.should_escalate = True
        return "escalation"

    # Explicit escalation decision
    if state.should_escalate:
        return "escalation"

    return END


# ─────────────────────────────────────────────
#  BUILD LANGGRAPH
# ─────────────────────────────────────────────

def build_orchestrator() -> StateGraph:
    """Constructs the LangGraph agent pipeline."""
    workflow = StateGraph(AgentState)

    # Add all agent nodes
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("investigation", investigation_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("resolution", resolution_node)
    workflow.add_node("escalation", escalation_node)

    # Entry point
    workflow.set_entry_point("retrieval")

    # Edges
    workflow.add_edge("retrieval", "investigation")
    workflow.add_conditional_edges(
        "investigation",
        should_verify_evidence,
        {"verification": "verification", "resolution": "resolution"},
    )
    workflow.add_edge("verification", "resolution")
    workflow.add_conditional_edges(
        "resolution",
        should_escalate,
        {"escalation": "escalation", END: END},
    )
    workflow.add_edge("escalation", END)

    return workflow.compile()


# Singleton compiled graph
_graph = build_orchestrator()


async def process_ticket(state: AgentState) -> AgentState:
    """Main entry point — runs a ticket through the full agent pipeline."""
    logger.info(
        "🎯 Orchestrator processing ticket",
        ticket_id=state.ticket.id,
        category=state.ticket.category,
        has_evidence=bool(state.ticket.evidence_files),
    )
    result = await _graph.ainvoke(state)
    return AgentState(**result)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _add_agent_step(state: AgentState, agent_type: AgentType, result: dict, start: float):
    duration_ms = int((time.time() - start) * 1000)
    step = AgentStep(
        agent_type=agent_type,
        status=AgentStatus.COMPLETED if not result.get("error") else AgentStatus.FAILED,
        output_data=result,
        reasoning=result.get("reasoning"),
        confidence=result.get("confidence", 0.0),
        duration_ms=duration_ms,
        error=result.get("error"),
    )
    state.ticket.agent_steps.append(step)
