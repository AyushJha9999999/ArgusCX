"""
ArgusCX — Multi-Signal Scoring Engine
Computes realistic confidence, risk, and fraud scores from all available signals:
  - Behavioural signals (fraud history, account age, ticket volume)
  - Textual signals (sentiment, urgency, threatening language, claim consistency)
  - Evidence signals (EXIF, C2PA, AI artifacts, file-integrity)
  - Investigation signals (anomalies found, claim verified, risk indicators)
  - Policy signals (auto-resolve eligibility, constraint count)

All three scores are independently computed then blended — they are NEVER identical.
"""
import math
import re
import random
from typing import Any, Dict, List, Optional

import structlog

from app.models.schemas import (
    AgentState,
    FraudAnalysisResult,
    FraudRiskLevel,
)

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────

def compute_scores(state: AgentState) -> Dict[str, float]:
    """
    Central scoring function.  Returns a dict with:
      fraud_score        0-1  (likelihood of fraud)
      risk_score         0-1  (operational risk / escalation probability)
      confidence_score   0-1  (system certainty in its decision)
    """
    signals = _extract_signals(state)

    fraud_score = _compute_fraud_score(signals)
    risk_score = _compute_risk_score(signals, fraud_score)
    confidence_score = _compute_confidence_score(signals, fraud_score, risk_score)

    # Clamp all to [0, 1]
    fraud_score = round(max(0.0, min(1.0, fraud_score)), 3)
    risk_score = round(max(0.0, min(1.0, risk_score)), 3)
    confidence_score = round(max(0.0, min(1.0, confidence_score)), 3)

    logger.info(
        "Scoring engine results",
        fraud=fraud_score,
        risk=risk_score,
        confidence=confidence_score,
        signals=signals,
    )
    return {
        "fraud_score": fraud_score,
        "risk_score": risk_score,
        "confidence_score": confidence_score,
    }


# ─────────────────────────────────────────────
#  SIGNAL EXTRACTION
# ─────────────────────────────────────────────

def _extract_signals(state: AgentState) -> Dict[str, Any]:
    customer = state.ticket.customer
    message = state.ticket.message or ""
    subject = state.ticket.subject or ""
    full_text = (subject + " " + message).lower()

    # ── Behavioural signals ───────────────────
    fraud_flags = customer.previous_fraud_flags or 0
    prev_tickets = customer.previous_tickets or 0
    account_age = customer.account_age_days or 0

    # ── Text signals ──────────────────────────
    urgency_words = ["immediately", "urgent", "asap", "right now", "now", "instant",
                     "fast", "quick", "emergency", "hurry", "rush"]
    threat_words = ["chargeback", "lawyer", "sue", "legal", "court", "report",
                    "police", "fraud", "scam", "fake", "destroy", "expose"]
    claim_amount_match = re.findall(r"(?:rs\.?|inr|usd|\$|₹)\s*(\d[\d,]*)", full_text)
    high_claim = False
    if claim_amount_match:
        try:
            amount = int(claim_amount_match[0].replace(",", ""))
            high_claim = amount > 5000
        except ValueError:
            pass

    urgency_count = sum(1 for w in urgency_words if w in full_text)
    threat_count = sum(1 for w in threat_words if w in full_text)
    short_message = len(message.strip()) < 60  # Very short = less verifiable

    # ── Evidence signals ──────────────────────
    fa: Optional[FraudAnalysisResult] = state.fraud_analysis
    has_evidence = bool(state.ticket.evidence_files)
    evidence_fraud_score = fa.fraud_score if fa else None
    evidence_ai_prob = fa.ai_generated_probability if fa else 0.0
    evidence_risk_level = fa.fraud_risk_level if fa else None
    exif_anomaly_count = len(fa.exif_anomalies) if fa else 0
    manipulation_count = len(fa.manipulation_indicators) if fa else 0
    c2pa_valid = fa.c2pa_valid if fa else None

    # ── Investigation signals ─────────────────
    inv_step = next(
        (s for s in state.ticket.agent_steps
         if s.agent_type.value == "data_investigation"),
        None,
    )
    anomaly_count = 0
    claim_verified = True
    risk_indicator_count = 0
    investigation_confidence = 0.75

    if inv_step and inv_step.output_data:
        anomaly_count = len(inv_step.output_data.get("anomalies", []))
        claim_verified = inv_step.output_data.get("claim_verified", True)
        risk_indicator_count = len(inv_step.output_data.get("risk_indicators", []))
        investigation_confidence = inv_step.output_data.get("confidence", 0.75)

    return {
        # Behavioural
        "fraud_flags": fraud_flags,
        "prev_tickets": prev_tickets,
        "account_age": account_age,
        # Text
        "urgency_count": urgency_count,
        "threat_count": threat_count,
        "high_claim": high_claim,
        "short_message": short_message,
        "message_length": len(message.strip()),
        # Evidence
        "has_evidence": has_evidence,
        "evidence_fraud_score": evidence_fraud_score,
        "evidence_ai_prob": evidence_ai_prob,
        "evidence_risk_level": evidence_risk_level,
        "exif_anomaly_count": exif_anomaly_count,
        "manipulation_count": manipulation_count,
        "c2pa_valid": c2pa_valid,
        # Investigation
        "anomaly_count": anomaly_count,
        "claim_verified": claim_verified,
        "risk_indicator_count": risk_indicator_count,
        "investigation_confidence": investigation_confidence,
    }


# ─────────────────────────────────────────────
#  FRAUD SCORE  (0 = clean, 1 = definite fraud)
# ─────────────────────────────────────────────

def _compute_fraud_score(s: Dict[str, Any]) -> float:
    score = 0.0

    # Evidence is the strongest signal (weight 0.45 if present)
    if s["evidence_fraud_score"] is not None:
        score += s["evidence_fraud_score"] * 0.45
        score += s["evidence_ai_prob"] * 0.15
    else:
        # No evidence — penalise slightly for unsubstantiated claims
        score += 0.04

    # Prior fraud history (weight 0.25)
    flag_score = min(1.0, s["fraud_flags"] / 3.0)  # 3+ flags → max
    score += flag_score * 0.25

    # Investigation anomalies (weight 0.15)
    if not s["claim_verified"]:
        score += 0.10
    anomaly_contribution = min(0.10, s["anomaly_count"] * 0.025)
    score += anomaly_contribution
    risk_ind_contribution = min(0.05, s["risk_indicator_count"] * 0.015)
    score += risk_ind_contribution

    # Behavioural text signals (weight 0.10)
    text_score = 0.0
    text_score += min(0.04, s["threat_count"] * 0.015)
    text_score += min(0.03, s["urgency_count"] * 0.01)
    if s["high_claim"]:
        text_score += 0.02
    if s["short_message"] and s["has_evidence"] is False:
        text_score += 0.01
    score += min(0.10, text_score)

    # New account submitting high-volume fraud-flagged requests
    if s["account_age"] < 30 and s["fraud_flags"] > 0:
        score += 0.05

    # Add a small realistic jitter (±2%) to avoid identical scores
    score += random.uniform(-0.02, 0.02)

    return score


# ─────────────────────────────────────────────
#  RISK SCORE  (operational / escalation risk)
# ─────────────────────────────────────────────

def _compute_risk_score(s: Dict[str, Any], fraud_score: float) -> float:
    """
    Risk is broader than fraud — it captures operational risk:
    financial exposure, legal threat, reputational harm, etc.
    It should be >= fraud_score in most cases.
    """
    score = fraud_score * 0.55  # Fraud score is a major input

    # Legal / financial threats
    score += min(0.15, s["threat_count"] * 0.045)
    if s["high_claim"]:
        score += 0.08

    # High ticket volume from the same customer
    if s["prev_tickets"] > 10:
        score += 0.06
    elif s["prev_tickets"] > 5:
        score += 0.03

    # Investigation anomalies independently contribute to risk
    score += min(0.08, s["anomaly_count"] * 0.02)

    # Unverified claim without evidence
    if not s["has_evidence"] and not s["claim_verified"]:
        score += 0.05

    # Urgency + no evidence = higher operational risk
    if s["urgency_count"] >= 2 and not s["has_evidence"]:
        score += 0.04

    # Add small jitter independent of fraud jitter
    score += random.uniform(-0.015, 0.015)

    return score


# ─────────────────────────────────────────────
#  CONFIDENCE SCORE  (system certainty in decision)
# ─────────────────────────────────────────────

def _compute_confidence_score(
    s: Dict[str, Any], fraud_score: float, risk_score: float
) -> float:
    """
    Confidence is about HOW SURE the system is — not how risky or fraudulent.
    High confidence = the system has enough data to decide reliably.
    Low confidence = missing evidence, contradictions, edge cases.
    """
    base = s["investigation_confidence"]  # LLM-given investigation confidence

    # Evidence quality boosts confidence significantly
    if s["has_evidence"]:
        base = min(1.0, base + 0.12)
        if s["c2pa_valid"] is True:
            base = min(1.0, base + 0.05)
    else:
        base = max(0.40, base - 0.08)  # Less confident without files

    # Consistent signals → higher confidence
    if s["fraud_flags"] > 1 and fraud_score > 0.70:
        base = min(1.0, base + 0.08)  # Signals align → confident
    if s["claim_verified"] and fraud_score < 0.30:
        base = min(1.0, base + 0.06)  # Clean case → confident

    # Contradictory signals → reduce confidence
    if s["fraud_flags"] > 0 and s["claim_verified"] and s["evidence_fraud_score"] is None:
        base -= 0.06  # Flag history but no evidence to verify claim

    # Very short message = less data = lower confidence
    if s["short_message"]:
        base -= 0.04

    # High anomaly/risk indicator count with unverified claim → moderate confidence
    if not s["claim_verified"] and s["anomaly_count"] > 2:
        base = min(1.0, base + 0.04)

    # Add small jitter
    base += random.uniform(-0.01, 0.01)

    return max(0.40, base)
