"""
ArgusCX -- LLM Reasoning Worker
Uses Qwen2-7B-Instruct via Ollama for claim-evidence consistency analysis.
LLM receives structured signals -- it is NOT the visual truth engine.
LLM output is ONE signal among many (claim_consistency).

LIMITATION: LLM output is probabilistic. Contradictions are signals, not facts.
LIMITATION: Qwen2-7B on CPU: 30-60s. Timeout at 30s, fallback to signals-only.
"""
import json
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL   = "qwen2:7b-instruct"
FALLBACK_MODEL  = "llama3.1:8b"
TIMEOUT_SECONDS = 30


SYSTEM_PROMPT = """You are an evidence analyst for a product return verification system.
Your role: analyze whether a customer's claim is consistent with the technical evidence collected.

IMPORTANT RULES:
- Never accuse the customer of fraud. Your job is to identify inconsistencies.
- Use evidentiary language: "not visible in evidence", "inconsistent with", "cannot confirm".
- Never say "customer caused damage" or "customer is lying".
- Output ONLY valid JSON.
- If evidence is insufficient, say so honestly.
"""

ANALYSIS_PROMPT = """Analyze this return claim against collected evidence.

CUSTOMER CLAIM:
{claim_text}

RETURN REASON: {return_reason}
PRODUCT CATEGORY: {category}

TECHNICAL EVIDENCE SIGNALS:
{signals_summary}

Output JSON with these exact keys:
{{
  "assertions": ["list of customer claim assertions you can extract"],
  "contradictions": ["list of claim-evidence inconsistencies found, or empty list"],
  "routing_recommendation": "AUTO_APPROVED | REVIEW_REQUIRED | AUTO_REJECTED",
  "narrative": "2-3 sentence investigator-style summary using evidentiary language",
  "confidence": 0.0-1.0
}}
"""


def _build_signals_summary(signals: Dict[str, Any]) -> str:
    lines = []
    pid = signals.get("product_identity", {})
    if pid.get("serial_match") is False:
        lines.append(f"SERIAL MISMATCH: expected {pid.get('expected_serial')}, detected {pid.get('detected_serial')}")
    elif pid.get("serial_match") is True:
        lines.append(f"SERIAL MATCH CONFIRMED: {pid.get('detected_serial')}")
    elif not pid.get("serial_readable", True):
        lines.append("SERIAL: not readable in evidence")

    dmg = signals.get("damage_evidence", {})
    if dmg.get("damage_types"):
        lines.append(f"DAMAGE DETECTED: {', '.join(dmg['damage_types'])} severity={dmg.get('severity')}")
    else:
        lines.append("DAMAGE: no damage detected in evidence")

    replay = signals.get("screen_replay_risk", {})
    if (replay.get("score") or 0) > 0.4:
        lines.append(f"SCREEN REPLAY RISK: score={replay.get('score')} findings={replay.get('findings')}")

    reuse = signals.get("evidence_reuse", {})
    if reuse.get("matched_session_id"):
        lines.append(f"EVIDENCE REUSE: near-duplicate evidence from session {reuse.get('matched_session_id')}")

    outbound = signals.get("outbound_comparison", {})
    if outbound.get("damage_in_return") and not outbound.get("damage_in_outbound"):
        lines.append("OUTBOUND COMPARISON: damage not visible in outbound (pre-shipping) evidence")
    elif outbound.get("damage_in_outbound") and outbound.get("damage_in_return"):
        lines.append("OUTBOUND COMPARISON: damage present in both outbound and return evidence")

    return chr(10).join(lines) if lines else "No strong signals detected."


async def run_llm_analysis(
    claim_text: Optional[str],
    return_reason: Optional[str],
    category: Optional[str],
    signals: Dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """Run LLM claim-evidence consistency analysis via Ollama."""
    if not HTTPX_AVAILABLE:
        return {"skipped": True, "reason": "httpx_not_installed"}
    if not claim_text:
        return {"skipped": True, "reason": "no_claim_text", "assertions": [], "contradictions": []}

    signals_summary = _build_signals_summary(signals)
    prompt = ANALYSIS_PROMPT.format(
        claim_text=claim_text,
        return_reason=return_reason or "not specified",
        category=category or "not specified",
        signals_summary=signals_summary,
    )

    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            raw_response = resp.json().get("response", "{}")
            result = json.loads(raw_response)
            return {
                "assertions":               result.get("assertions", []),
                "contradictions":           result.get("contradictions", []),
                "routing_recommendation":   result.get("routing_recommendation", "REVIEW_REQUIRED"),
                "narrative":                result.get("narrative", ""),
                "confidence":               result.get("confidence", 0.5),
                "model_used":               model,
            }
    except httpx.TimeoutException:
        logger.warning("LLM timeout -- using fallback", model=model, timeout=TIMEOUT_SECONDS)
        return {"skipped": True, "reason": "llm_timeout", "assertions": [], "contradictions": []}
    except Exception as exc:
        logger.error("LLM analysis failed", error=str(exc), model=model)
        # Try fallback model
        if model != FALLBACK_MODEL:
            return await run_llm_analysis(claim_text, return_reason, category, signals, FALLBACK_MODEL)
        return {"skipped": True, "reason": str(exc), "assertions": [], "contradictions": []}
