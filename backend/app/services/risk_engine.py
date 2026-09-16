"""
ArgusCX -- Multi-Signal Risk Engine

DESIGN PRINCIPLES:
- Every signal is a SEPARATE score with its own explanation.
- No single signal auto-rejects (multi-signal confirmation required).
- Language is evidentiary, never accusatory.
- All thresholds are tenant-configurable.
"""
from typing import Any, Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)

# Case states
VERIFIED          = "VERIFIED"
INCONSISTENT      = "INCONSISTENT"
SUSPICIOUS        = "SUSPICIOUS"
REVIEW_REQUIRED   = "REVIEW_REQUIRED"
REJECTED          = "REJECTED"

ROUTING_AUTO_APPROVED  = "AUTO_APPROVED"
ROUTING_REVIEW         = "REVIEW_REQUIRED"
ROUTING_AUTO_REJECTED  = "AUTO_REJECTED"


def compute_risk_signals(
    forensic_findings: List[Dict],
    screen_replay_findings: List[Dict],
    challenge_completion_ratio: float,
    product_identity: Optional[Dict],
    damage_finding: Optional[Dict],
    evidence_reuse: Optional[Dict],
    llm_reasoning: Optional[Dict],
    outbound_comparison: Optional[Dict],
    assurance_level: str,
    policy: Dict,
) -> Dict[str, Any]:
    """Compute all per-signal scores. Returns structured signals dict."""
    signals = {}

    # Evidence Integrity
    ela  = max((f["score"] for f in forensic_findings if f.get("finding_type") == "ELA"      and f.get("score") is not None), default=0.0)
    noise= max((f["score"] for f in forensic_findings if f.get("finding_type") == "NOISE"    and f.get("score") is not None), default=0.0)
    meta = max((f["score"] for f in forensic_findings if f.get("finding_type") == "METADATA" and f.get("score") is not None), default=0.0)
    integrity_score = ela * 0.5 + noise * 0.3 + meta * 0.2
    assurance_mult = {"live_video": 1.0, "guided_photo": 0.85, "upload": 0.60, "unknown": 0.50}.get(assurance_level, 0.50)
    signals["evidence_integrity"] = {
        "score": round(integrity_score, 3),
        "assurance_level": assurance_level,
        "assurance_confidence": round(assurance_mult, 2),
        "findings": [f.get("finding_type") for f in forensic_findings if (f.get("score") or 0) > 0.3],
    }

    # Screen Replay
    moire    = max((f["score"] for f in screen_replay_findings if f.get("finding_type") == "MOIRE"    and f.get("score") is not None), default=0.0)
    geo      = max((f["score"] for f in screen_replay_findings if f.get("finding_type") == "GEOMETRY" and f.get("score") is not None), default=0.0)
    temporal = max((f["score"] for f in screen_replay_findings if f.get("finding_type") == "TEMPORAL" and f.get("score") is not None), default=0.0)
    replay_score = moire * 0.40 + geo * 0.35 + temporal * 0.25
    signals["screen_replay_risk"] = {
        "score": round(replay_score, 3),
        "findings": [f.get("finding_type") for f in screen_replay_findings if (f.get("score") or 0) > 0.3],
        "limitation": "OLED screens may reduce moire signal confidence.",
    }

    # Challenge Completion
    signals["challenge_completion"] = {
        "score": round(1.0 - challenge_completion_ratio, 3),
        "completion_ratio": round(challenge_completion_ratio, 2),
    }

    # Product Identity
    if product_identity:
        sm = product_identity.get("serial_match")
        sr = product_identity.get("serial_readable", True)
        vs = product_identity.get("visual_similarity_score") or 0.0
        identity_score = 1.0 if sm is False and sr else (0.5 if sm is None and not sr else 0.0)
        signals["product_identity"] = {
            "score": round(identity_score, 3),
            "serial_match": sm, "serial_readable": sr,
            "detected_serial": product_identity.get("detected_serial"),
            "expected_serial": product_identity.get("expected_serial"),
            "visual_similarity_score": round(vs, 3),
        }
    else:
        signals["product_identity"] = {"score": 0.0, "serial_match": None, "note": "not_analysed"}

    # Damage
    if damage_finding:
        sev_map = {"NONE": 0.0, "LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8}
        sev = damage_finding.get("severity", "NONE")
        signals["damage_evidence"] = {
            "score": sev_map.get(sev, 0.0),
            "damage_types": damage_finding.get("damage_types", []),
            "severity": sev, "confidence": damage_finding.get("confidence"),
        }
    else:
        signals["damage_evidence"] = {"score": 0.0, "damage_types": [], "severity": "NONE"}

    # Evidence Reuse
    if evidence_reuse and evidence_reuse.get("matched_session_id"):
        pd = evidence_reuse.get("phash_distance", 99)
        reuse_score = max(0.0, 1.0 - (pd or 99) / 15.0)
        signals["evidence_reuse"] = {
            "score": round(min(reuse_score, 1.0), 3),
            "matched_session_id": evidence_reuse.get("matched_session_id"),
            "phash_distance": pd,
            "note": "Near-duplicate evidence detected from a previous session.",
        }
    else:
        signals["evidence_reuse"] = {"score": 0.0, "matched_session_id": None}

    # Claim Consistency (LLM)
    if llm_reasoning:
        contradictions = llm_reasoning.get("contradictions", [])
        signals["claim_consistency"] = {
            "score": round(min(len(contradictions) * 0.25, 1.0), 3),
            "contradictions": contradictions,
            "assertions": llm_reasoning.get("assertions", []),
        }
    else:
        signals["claim_consistency"] = {"score": 0.0, "contradictions": [], "note": "llm_not_available"}

    # Outbound Comparison
    if outbound_comparison:
        out_dmg = outbound_comparison.get("outbound_damage_detected", False)
        ret_dmg = outbound_comparison.get("return_damage_detected", False)
        sim = outbound_comparison.get("similarity_score") or 0.0
        delta = 0.6 if (ret_dmg and not out_dmg) else 0.0
        signals["outbound_comparison"] = {
            "score": round(delta, 3),
            "similarity_score": round(sim, 3),
            "damage_in_outbound": out_dmg, "damage_in_return": ret_dmg,
            "note": "Damage not visible in outbound evidence." if delta > 0 else "Evidence consistent.",
        }
    else:
        signals["outbound_comparison"] = {"score": 0.0, "note": "outbound_evidence_not_provided"}

    return signals


def determine_case_state(
    signals: Dict[str, Any],
    policy: Dict,
) -> Tuple[str, str, str]:
    """
    Aggregate signals into a case state.
    Returns: (state, routing, reasoning_prefix)
    """
    review_threshold = float(policy.get("review_threshold", 0.6))
    suspicious = []
    review = []

    pid = signals.get("product_identity", {})
    if pid.get("serial_match") is False and pid.get("serial_readable", True):
        suspicious.append(
            f"Serial mismatch: expected {pid.get('expected_serial')}, "
            f"detected {pid.get('detected_serial')}"
        )

    reuse = signals.get("evidence_reuse", {})
    if (reuse.get("score") or 0) > 0.70:
        suspicious.append(
            f"Near-duplicate evidence (phash_distance={reuse.get('phash_distance')})"
        )

    replay = signals.get("screen_replay_risk", {})
    if (replay.get("score") or 0) > 0.60:
        suspicious.append("Screen replay indicators: moire and/or planar geometry")

    challenge = signals.get("challenge_completion", {})
    if (challenge.get("score") or 0) > 0.60:
        review.append("Multiple challenges not completed")

    contradictions = signals.get("claim_consistency", {}).get("contradictions", [])
    if contradictions:
        review.append(f"Claim-evidence contradictions: {'; '.join(contradictions[:2])}")

    if (signals.get("outbound_comparison", {}).get("score") or 0) > 0.5:
        review.append("Damage not visible in available outbound evidence")

    if pid.get("serial_match") is None and not pid.get("serial_readable", True):
        review.append("Serial number was not readable in captured evidence")

    if (signals.get("evidence_integrity", {}).get("score") or 0) > review_threshold:
        review.append("Evidence integrity anomalies detected (ELA/noise/metadata)")

    if suspicious:
        return SUSPICIOUS, ROUTING_REVIEW, "Suspicious signals detected."
    elif len(review) >= 2:
        return REVIEW_REQUIRED, ROUTING_REVIEW, "Multiple signals require human review."
    elif len(review) == 1:
        return INCONSISTENT, ROUTING_REVIEW, review[0]
    else:
        return VERIFIED, ROUTING_AUTO_APPROVED, "All evidence signals consistent with legitimate return."


def build_case(
    session_id: str,
    tenant_id: str,
    signals: Dict[str, Any],
    state: str,
    routing: str,
    reasoning_prefix: str,
    llm_narrative: Optional[str],
    claim_assertions: List[str],
    contradictions: List[str],
) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "tenant_id": tenant_id,
        "state": state,
        "routing": routing,
        "risk_signals_json": signals,
        "reasoning_narrative": llm_narrative or reasoning_prefix,
        "claim_assertions_json": claim_assertions,
        "contradictions_json": contradictions,
    }
