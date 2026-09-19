"""
ArgusCX — Vision Analysis Service

Uses a vision-capable LLM (via Groq) to analyse evidence images submitted
during a return-verification session and generate a structured forensic report.

The report covers:
  - Product condition (damage, scratches, missing parts)
  - Authenticity indicators (serial number, brand markings visible)
  - Claim consistency (does evidence match the stated return reason?)
  - Fraud indicators (AI-generated imagery, staging, image reuse signs)
  - Overall recommendation (APPROVE / REJECT / ESCALATE) with rationale
"""
from __future__ import annotations

import base64
import json
import re
import time
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ── Groq vision model — best free-tier option ─────────────────────────────────
VISION_MODEL = "llama-3.2-11b-vision-preview"
FALLBACK_MODEL = "llama-3.3-70b-versatile"   # text-only fallback (no images)

GROQ_VISION_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = """You are ArgusCX Forensic Analyst, an expert AI system that examines
photographic evidence submitted with product return claims. Your job is to produce a
thorough, structured analysis for every piece of evidence.

Respond ONLY with a valid JSON object matching this schema (no markdown fences):
{
  "overall_recommendation": "APPROVE" | "REJECT" | "ESCALATE",
  "confidence": 0.0-1.0,
  "summary": "<2-3 sentence plain-English verdict>",
  "product_condition": {
    "assessment": "<detailed description of physical condition>",
    "damage_detected": true | false,
    "damage_details": "<specifics or null>",
    "risk_level": "low" | "medium" | "high"
  },
  "authenticity": {
    "assessment": "<evaluation of product authenticity markers visible>",
    "serial_visible": true | false,
    "brand_markings_valid": true | false,
    "risk_level": "low" | "medium" | "high"
  },
  "claim_consistency": {
    "assessment": "<does the visual evidence match the stated claim?>",
    "consistent": true | false,
    "discrepancies": ["<list of any inconsistencies>"],
    "risk_level": "low" | "medium" | "high"
  },
  "fraud_indicators": {
    "assessment": "<evaluation of any signs of fraud or manipulation>",
    "ai_generated_likely": true | false,
    "staging_signs": true | false,
    "image_manipulation_detected": true | false,
    "indicators": ["<list of specific red flags, or empty>"],
    "risk_level": "low" | "medium" | "high"
  },
  "key_findings": ["<bullet-point key findings, 3-6 items>"]
}"""


# ─────────────────────────────────────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

async def analyse_evidence_images(
    evidence_urls: List[str],
    claim_text: Optional[str],
    return_reason: Optional[str],
    category: Optional[str],
) -> Dict[str, Any]:
    """
    Analyse a list of evidence image URLs with a vision LLM.

    Returns a report dict with:
      - per_image: list of per-image analysis dicts
      - aggregate: rolled-up recommendation + summary across all images
      - model_used: which LLM was used
      - analysed_at: ISO timestamp
    """
    if not settings.GROQ_API_KEY:
        return _no_llm_fallback(evidence_urls)

    context = _build_context_text(claim_text, return_reason, category)
    per_image: List[Dict[str, Any]] = []

    valid_urls = [u for u in evidence_urls if u and u.startswith("http")]

    if not valid_urls:
        return _no_evidence_fallback()

    total = len(valid_urls)

    for idx, url in enumerate(valid_urls, start=1):
        if idx > 1:
            await asyncio.sleep(1.0)  # Rate limit protection for Groq API
        try:
            res = await _analyse_single_image(url, context, idx, total)
            res["url"] = url
            res["index"] = idx
            per_image.append(res)
        except Exception as e:
            logger.warning("Vision analysis failed for image", url=url, error=str(e))
            per_image.append({
                "url": url,
                "index": idx,
                "overall_recommendation": "ESCALATE",
                "confidence": 0.0,
                "summary": "Analysis failed due to a system error.",
                "error": str(e)
            })

    aggregate = _aggregate_results(per_image)
    aggregate["per_image"] = per_image
    aggregate["model_used"] = VISION_MODEL
    aggregate["analysed_at"] = _iso_now()
    aggregate["image_count"] = len(valid_urls)
    return aggregate


# ─────────────────────────────────────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_context_text(
    claim_text: Optional[str],
    return_reason: Optional[str],
    category: Optional[str],
) -> str:
    parts = []
    if category:
        parts.append(f"Product category: {category}")
    if return_reason:
        parts.append(f"Return reason stated: {return_reason}")
    if claim_text:
        parts.append(f"Customer claim text: \"{claim_text}\"")
    return "\n".join(parts) if parts else "No additional claim context provided."


async def _analyse_single_image(
    url: str,
    context: str,
    idx: int,
    total: int,
) -> Dict[str, Any]:
    """Call Groq vision API for a single image URL."""
    user_content: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                f"You are examining evidence image {idx} of {total} for a product return claim.\n\n"
                f"Claim context:\n{context}\n\n"
                "Analyse this image thoroughly and return a structured JSON report."
            ),
        },
        {
            "type": "image_url",
            "image_url": {"url": url, "detail": "high"},
        },
    ]

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 1024,
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            GROQ_VISION_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if response.status_code != 200:
        # Vision model might not be available — try text-only fallback
        logger.warning(
            "Vision model unavailable, trying text fallback",
            status=response.status_code,
            model=VISION_MODEL,
        )
        return await _text_only_fallback(url, context, idx, total)

    raw = response.json()
    content = raw["choices"][0]["message"]["content"].strip()
    return _parse_llm_json(content)


async def _text_only_fallback(
    url: str,
    context: str,
    idx: int,
    total: int,
) -> Dict[str, Any]:
    """Fallback: describe URL and ask the text LLM for a plausible assessment."""
    payload = {
        "model": settings.GROQ_MODEL or FALLBACK_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Evidence image {idx} of {total} is available at: {url}\n"
                    f"Claim context:\n{context}\n\n"
                    "Based on the claim context and typical return fraud patterns, provide your "
                    "best forensic assessment. Recommend ESCALATE since you cannot actually view the image."
                ),
            },
        ],
        "max_tokens": 800,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GROQ_VISION_URL,
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    raw = response.json()
    content = raw["choices"][0]["message"]["content"].strip()
    result = _parse_llm_json(content)
    result["_note"] = "Analysed without visual access (text fallback)"
    return result


def _parse_llm_json(content: str) -> Dict[str, Any]:
    """Extract and parse the JSON block from the LLM response."""
    # Strip any markdown fences
    cleaned = re.sub(r"```(?:json)?", "", content).strip().strip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON substring
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "overall_recommendation": "ESCALATE",
        "confidence": 0.2,
        "summary": "Could not parse AI response. Manual review required.",
        "raw_response": content[:500],
    }


def _aggregate_results(per_image: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Roll up per-image results into an overall recommendation."""
    if not per_image:
        return {
            "overall_recommendation": "ESCALATE",
            "confidence": 0.0,
            "summary": "No images were successfully analysed.",
        }

    recommendations = [r.get("overall_recommendation", "ESCALATE") for r in per_image]
    confidences = [float(r.get("confidence", 0.3)) for r in per_image]
    avg_confidence = sum(confidences) / len(confidences)

    # Strictest recommendation wins
    if "REJECT" in recommendations:
        final = "REJECT"
    elif "ESCALATE" in recommendations:
        final = "ESCALATE"
    else:
        final = "APPROVE"

    summaries = [r.get("summary", "") for r in per_image if r.get("summary")]
    key_findings: List[str] = []
    for r in per_image:
        key_findings.extend(r.get("key_findings", []))

    # Deduplicate findings
    seen: set = set()
    unique_findings = [f for f in key_findings if not (f in seen or seen.add(f))]  # type: ignore[func-returns-value]

    return {
        "overall_recommendation": final,
        "confidence": round(avg_confidence, 3),
        "summary": " ".join(summaries[:2]) or "Analysis complete.",
        "key_findings": unique_findings[:8],
    }


def _no_llm_fallback(evidence_urls: List[str]) -> Dict[str, Any]:
    return {
        "overall_recommendation": "ESCALATE",
        "confidence": 0.0,
        "summary": "LLM not configured — automated analysis unavailable. Manual review required.",
        "per_image": [],
        "model_used": "none",
        "analysed_at": _iso_now(),
        "image_count": len(evidence_urls),
    }


def _no_evidence_fallback() -> Dict[str, Any]:
    return {
        "overall_recommendation": "ESCALATE",
        "confidence": 0.0,
        "summary": "No valid evidence image URLs found. Manual review required.",
        "per_image": [],
        "model_used": "none",
        "analysed_at": _iso_now(),
        "image_count": 0,
    }


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
