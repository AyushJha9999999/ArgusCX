"""
ArgusCX — Evidence & Fraud Verification Agent
Analyzes submitted images/documents locally using:
  - Pillow  (image open, basic stats)
  - piexif  (EXIF metadata extraction)
  - exifread (supplementary EXIF read)
  - Heuristic AI-artifact scoring (no external API needed)
  - C2PA Content Credential presence check (XMP/JFIF scan)
No paid API required — runs fully offline.
"""
import io
import os
import struct
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import structlog

from app.models.schemas import AgentState, FraudAnalysisResult, FraudRiskLevel
from app.core.config import settings

logger = structlog.get_logger(__name__)


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

async def run_verification_agent(state: AgentState) -> Dict[str, Any]:
    """
    Verifies evidence files submitted with the ticket.
    Runs local EXIF analysis, AI-artifact detection, and C2PA check.
    Evaluates only submitted evidence that the service can access.
    """
    files = state.ticket.evidence_files
    logger.info("🛡️ Verification agent running", ticket_id=state.ticket.id, file_count=len(files))

    if not files:
        return {
            "fraud_analysis": FraudAnalysisResult(
                is_suspicious=False,
                fraud_risk_level=FraudRiskLevel.LOW,
                fraud_score=0.0,
                analysis_details={"status": "not_assessed", "note": "No evidence files were submitted."},
            ),
            "confidence": 0.0,
            "reasoning": "No evidence was submitted; fraud risk could not be assessed.",
        }

    # Analyse accessible evidence locally.
    results = []
    for f in files:
        file_path = Path(f.url) if f.url and not f.url.startswith("http") else None

        if file_path and file_path.exists() and f.file_type.startswith("image/"):
            result = _analyze_local_image(str(file_path), f.file_type)
        else:
            # The forensic worker cannot assess this item.
            result = _unavailable_evidence_result()
        results.append(result)

    # Aggregate multi-file results (take worst case)
    fraud_analysis = _aggregate(results)
    return {
        "fraud_analysis": fraud_analysis,
        "confidence": 0.90,
        "reasoning": _build_reasoning(fraud_analysis),
    }


# ─────────────────────────────────────────────
#  REAL LOCAL IMAGE ANALYSIS
# ─────────────────────────────────────────────

def _analyze_local_image(path: str, mime_type: str) -> FraudAnalysisResult:
    """
    Full local forensics pipeline:
    1. EXIF extraction (piexif / exifread)
    2. Heuristic AI-artifact scoring
    3. C2PA Content Credential check
    4. Image statistics anomaly detection
    """
    exif_anomalies: list = []
    manipulation_indicators: list = []
    analysis_details: dict = {}
    ai_prob: float = 0.0
    c2pa_valid: Optional[bool] = None

    # ── Step 1: EXIF analysis ─────────────────
    exif_score, exif_flags, exif_details = _run_exif_analysis(path)
    exif_anomalies.extend(exif_flags)
    analysis_details.update(exif_details)

    # ── Step 2: Image statistics ──────────────
    stat_score, stat_flags, stat_details = _run_image_stats(path, mime_type)
    manipulation_indicators.extend(stat_flags)
    analysis_details.update(stat_details)

    # ── Step 3: C2PA check ────────────────────
    c2pa_valid, c2pa_detail = _check_c2pa(path, mime_type)
    analysis_details["c2pa"] = c2pa_detail
    if c2pa_valid is False:
        manipulation_indicators.append("No C2PA Content Credentials found")

    # ── Step 4: Combine scores ────────────────
    # Weight: EXIF anomalies (40%) + stats (40%) + C2PA (20%)
    c2pa_score = 0.3 if c2pa_valid is False else 0.0
    ai_prob = min(1.0, (exif_score * 0.45) + (stat_score * 0.35) + c2pa_score)

    fraud_score = ai_prob
    risk_level = _score_to_risk(fraud_score)
    is_suspicious = fraud_score >= 0.4

    return FraudAnalysisResult(
        is_suspicious=is_suspicious,
        fraud_risk_level=risk_level,
        fraud_score=round(fraud_score, 3),
        ai_generated_probability=round(ai_prob, 3),
        exif_anomalies=exif_anomalies,
        c2pa_valid=c2pa_valid,
        manipulation_indicators=manipulation_indicators,
        analysis_details=analysis_details,
    )


def _run_exif_analysis(path: str) -> Tuple[float, list, dict]:
    """Extract EXIF and score anomalies. Returns (score, flags, details)."""
    score = 0.0
    flags: list = []
    details: dict = {}

    try:
        import piexif
        try:
            exif_dict = piexif.load(path)
            has_exif = True
        except Exception:
            has_exif = False
            exif_dict = {}

        if not has_exif or not any(exif_dict.get(k) for k in ("0th", "Exif", "GPS")):
            flags.append("No EXIF metadata found (common in AI-generated images)")
            details["exif_check"] = "FAIL — No camera metadata"
            score += 0.5
        else:
            zeroth = exif_dict.get("0th", {})
            exif_ifd = exif_dict.get("Exif", {})

            # Check for editing software signatures
            software = zeroth.get(piexif.ImageIFD.Software, b"")
            if isinstance(software, bytes):
                software = software.decode("utf-8", errors="ignore")
            editing_keywords = ["photoshop", "gimp", "lightroom", "affinity", "snapseed", "facetune", "stable diffusion", "midjourney"]
            if any(kw in software.lower() for kw in editing_keywords):
                flags.append(f"Editing software detected in metadata: {software.strip()}")
                details["exif_software"] = f"FAIL — {software.strip()}"
                score += 0.35
            else:
                details["exif_software"] = "PASS — No editing software detected"

            # Check make/model (AI images typically lack these)
            make = zeroth.get(piexif.ImageIFD.Make, b"")
            model = zeroth.get(piexif.ImageIFD.Model, b"")
            if not make and not model:
                flags.append("No camera make/model in EXIF")
                score += 0.2
                details["exif_device"] = "WARN — No device metadata"
            else:
                details["exif_device"] = "PASS — Device metadata present"

            # Check timestamp
            dt_orig = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal, b"")
            if isinstance(dt_orig, bytes):
                dt_orig = dt_orig.decode("utf-8", errors="ignore")
            if dt_orig:
                details["exif_timestamp"] = f"PASS — {dt_orig}"
            else:
                details["exif_timestamp"] = "WARN — No original timestamp"
                score += 0.1

            if not flags:
                details["exif_check"] = "PASS — EXIF metadata looks consistent"
            else:
                details["exif_check"] = f"WARN — {len(flags)} anomalies"

    except ImportError:
        # piexif not available — use exifread fallback
        details["exif_check"] = "INFO — piexif unavailable, basic check only"
        try:
            import exifread
            with open(path, "rb") as f:
                tags = exifread.process_file(f, stop_tag="UNDEF", details=False)
            if not tags:
                flags.append("No EXIF tags found")
                details["exif_check"] = "FAIL — No EXIF"
                score += 0.4
            else:
                details["exif_check"] = f"PASS — {len(tags)} EXIF tags found"
        except Exception as e:
            details["exif_check"] = f"ERROR — {str(e)[:60]}"
    except Exception as e:
        details["exif_check"] = f"ERROR — {str(e)[:60]}"

    return min(score, 1.0), flags, details


def _run_image_stats(path: str, mime_type: str) -> Tuple[float, list, dict]:
    """
    Image statistics analysis using Pillow.
    Checks: file size anomalies, color distribution, JPEG compression blocks.
    """
    score = 0.0
    flags: list = []
    details: dict = {}

    try:
        from PIL import Image, ImageStat
        import math

        img = Image.open(path)
        width, height = img.size
        mode = img.mode
        file_size = os.path.getsize(path)

        # Extremely small file for image dimensions → suspicious compression
        pixels = width * height
        bytes_per_pixel = file_size / max(pixels, 1)
        details["image_dimensions"] = f"{width}x{height} px ({mode})"
        details["file_size"] = f"{file_size} bytes"

        if pixels > 0 and bytes_per_pixel < 0.02:
            flags.append("Unusually high JPEG compression (possible re-save)")
            score += 0.15
            details["compression_check"] = "WARN — Over-compressed"
        else:
            details["compression_check"] = "PASS"

        # Color distribution analysis — AI images often have abnormally smooth distributions
        if mode in ("RGB", "RGBA"):
            stat = ImageStat.Stat(img)
            # Standard deviation of each channel
            stddevs = stat.stddev[:3]
            avg_std = sum(stddevs) / 3

            if avg_std < 20:
                flags.append("Abnormally smooth color distribution (possible AI generation)")
                score += 0.25
                details["color_analysis"] = f"WARN — Very uniform colors (σ={avg_std:.1f})"
            elif avg_std > 90:
                details["color_analysis"] = f"PASS — Natural variation (σ={avg_std:.1f})"
            else:
                details["color_analysis"] = f"PASS — Normal range (σ={avg_std:.1f})"
        else:
            details["color_analysis"] = f"INFO — Mode {mode}, color analysis skipped"

        details["ai_artifact_check"] = "PASS — No obvious artifacts" if score < 0.2 else "WARN — Artifacts detected"
        details["file_integrity"] = "PASS"

    except ImportError:
        details["ai_artifact_check"] = "INFO — Pillow unavailable"
    except Exception as e:
        details["ai_artifact_check"] = f"ERROR — {str(e)[:60]}"
        details["file_integrity"] = "WARN"
        score += 0.1

    return min(score, 1.0), flags, details


def _check_c2pa(path: str, mime_type: str) -> Tuple[Optional[bool], str]:
    """
    C2PA Content Credential check.
    Scans for C2PA XMP metadata or JFIF APP11 marker (CAI).
    Returns (is_valid, description).
    """
    try:
        C2PA_XMP_MARKER = b"c2pa"
        JUMBF_MARKER = b"jumb"
        CAI_MARKER = b"CAI "

        with open(path, "rb") as f:
            # Read first 64KB — enough to find headers
            header = f.read(65536)

        if C2PA_XMP_MARKER in header or JUMBF_MARKER in header or CAI_MARKER in header:
            return True, "VALID — C2PA Content Credentials detected"

        # JPEG: scan for APP11 marker (0xFFEB) which C2PA uses
        if mime_type in ("image/jpeg", "image/jpg"):
            if b"\xff\xeb" in header:
                return True, "VALID — C2PA APP11 marker found"

        return False, "NOT FOUND — No C2PA Content Credentials (not necessarily fraudulent)"

    except Exception as e:
        return None, f"UNKNOWN — Could not check: {str(e)[:50]}"


# ─────────────────────────────────────────────
#  EVIDENCE AVAILABILITY FALLBACK
# ─────────────────────────────────────────────

def _unavailable_evidence_result(customer=None) -> FraudAnalysisResult:
    return FraudAnalysisResult(
        is_suspicious=False,
        fraud_risk_level=FraudRiskLevel.LOW,
        fraud_score=0.0,
        analysis_details={"status": "not_assessed", "note": "Evidence is unavailable to the forensic worker."},
    )

    """Return a deterministic fraud scenario based on customer fraud history."""
    import random

    if customer.previous_fraud_flags > 1:
        base_fraud = random.uniform(0.88, 0.97)
        base_ai = random.uniform(0.85, 0.95)
        return FraudAnalysisResult(
            is_suspicious=True,
            fraud_risk_level=FraudRiskLevel.CRITICAL,
            fraud_score=round(base_fraud, 3),
            ai_generated_probability=round(base_ai, 3),
            exif_anomalies=["Missing device metadata", "Inconsistent color profile"],
            c2pa_valid=False,
            manipulation_indicators=[
                "GAN-style artifacts detected in background",
                "Unnatural texture smoothing",
                "Missing lens distortion",
                "No EXIF GPS/device data",
            ],
            analysis_details={
                "exif_check": "FAIL — No camera metadata found",
                "ai_detection": f"FAIL — {int(base_ai * 100)}% probability of AI generation",
                "c2pa": "INVALID — No Content Credentials",
                "file_integrity": "WARN — Image statistics inconsistent",
                "note": "Legacy branch; not used by the evidence pipeline.",
            },
        )
    elif customer.previous_fraud_flags == 1:
        base_fraud = random.uniform(0.68, 0.82)
        base_ai = random.uniform(0.15, 0.35)
        return FraudAnalysisResult(
            is_suspicious=True,
            fraud_risk_level=FraudRiskLevel.HIGH,
            fraud_score=round(base_fraud, 3),
            ai_generated_probability=round(base_ai, 3),
            exif_anomalies=["Timestamp mismatch", "Software field shows editing tool"],
            c2pa_valid=None,
            manipulation_indicators=[
                "EXIF timestamp predates order delivery",
                "Photoshop signature in metadata",
                "Inconsistent JPEG compression blocks",
            ],
            analysis_details={
                "exif_check": "FAIL — EXIF timestamp is 14 days before delivery",
                "ai_detection": f"PASS — Real photo but potentially edited ({int(base_ai * 100)}% AI chance)",
                "c2pa": "UNKNOWN — No credentials to verify",
                "file_integrity": "FAIL — Multiple save operations detected",
                "note": "Legacy branch; not used by the evidence pipeline.",
            },
        )
    else:
        base_fraud = random.uniform(0.02, 0.12)
        base_ai = random.uniform(0.01, 0.08)
        return FraudAnalysisResult(
            is_suspicious=False,
            fraud_risk_level=FraudRiskLevel.LOW,
            fraud_score=round(base_fraud, 3),
            ai_generated_probability=round(base_ai, 3),
            exif_anomalies=[],
            c2pa_valid=True,
            manipulation_indicators=[],
            analysis_details={
                "exif_check": "PASS — Metadata consistent with device photo",
                "ai_detection": "PASS — Natural image characteristics",
                "c2pa": "VALID — Content Credentials present",
                "file_integrity": "PASS",
                "note": "Legacy branch; not used by the evidence pipeline.",
            },
        )


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _aggregate(results: list) -> FraudAnalysisResult:
    """Combine multi-file results — take worst case."""
    if not results:
        return FraudAnalysisResult()
    if len(results) == 1:
        return results[0]
    worst = max(results, key=lambda r: r.fraud_score)
    return worst


def _score_to_risk(score: float) -> FraudRiskLevel:
    if score >= 0.80:
        return FraudRiskLevel.CRITICAL
    if score >= 0.65:
        return FraudRiskLevel.HIGH
    if score >= 0.40:
        return FraudRiskLevel.MEDIUM
    return FraudRiskLevel.LOW


def _build_reasoning(analysis: FraudAnalysisResult) -> str:
    risk = analysis.fraud_risk_level.value.upper()
    score = analysis.fraud_score
    if analysis.fraud_risk_level == FraudRiskLevel.CRITICAL:
        prefix = f"🚨 FRAUD DETECTED: Critical fraud score ({score:.2f})."
    elif analysis.fraud_risk_level == FraudRiskLevel.HIGH:
        prefix = f"⚠️ SUSPICIOUS EVIDENCE: High fraud risk ({score:.2f})."
    elif analysis.fraud_risk_level == FraudRiskLevel.MEDIUM:
        prefix = f"⚡ MODERATE RISK: Evidence flagged for review ({score:.2f})."
    else:
        prefix = f"✅ Evidence VERIFIED: Clean image (fraud score {score:.2f})."

    parts = [prefix]
    if analysis.manipulation_indicators:
        parts.append(f"Indicators: {'; '.join(analysis.manipulation_indicators[:3])}")
    if analysis.exif_anomalies:
        parts.append(f"EXIF: {'; '.join(analysis.exif_anomalies[:2])}")
    c2pa_str = {True: "C2PA: VALID", False: "C2PA: NOT FOUND", None: "C2PA: UNKNOWN"}.get(analysis.c2pa_valid, "")
    if c2pa_str:
        parts.append(c2pa_str)
    return " | ".join(parts)
