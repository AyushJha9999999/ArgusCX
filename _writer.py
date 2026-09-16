"""
ArgusCX Platform File Generator
Run: python _writer.py
Writes all service, worker, and route files for the platform.
"""
import os
import textwrap

BASE = r"c:\Users\Srijit\Downloads\ArgusCX-main\backend\app"
FRONT = r"c:\Users\Srijit\Downloads\ArgusCX-main\frontend"

os.makedirs(os.path.join(BASE, "services"), exist_ok=True)
os.makedirs(os.path.join(BASE, "workers", "tasks"), exist_ok=True)
os.makedirs(os.path.join(BASE, "api", "routes"), exist_ok=True)
os.makedirs(os.path.join(FRONT, "app", "verify"), exist_ok=True)

def w(rel, code):
    full = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(code).lstrip())
    print(f"  Written: {rel} ({len(code)} bytes)")

def wf(rel, code):
    full = os.path.join(FRONT, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(code).lstrip())
    print(f"  Written (frontend): {rel} ({len(code)} bytes)")

# ─────────────────────────────────────────────────────────
# services/manifest_service.py
# ─────────────────────────────────────────────────────────
w("services/manifest_service.py", '''
    """
    ArgusCX -- Evidence Manifest Service
    SHA-256 chain-of-custody manifest. Tamper-evident.
    """
    import hashlib
    import json
    from datetime import datetime
    from typing import List, Optional


    def compute_file_hash(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()


    def compute_manifest_hash(
        session_id: str,
        evidence_hashes: List[str],
        analysis_result_hash: Optional[str],
        created_at: str,
    ) -> str:
        data = {
            "session_id": session_id,
            "evidence_hashes": sorted(evidence_hashes),
            "analysis_result_hash": analysis_result_hash or "",
            "created_at": created_at,
            "version": "1.0",
        }
        s = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode()).hexdigest()


    def build_manifest(
        session_id: str,
        evidence_hashes: List[str],
        analysis_result: dict,
    ) -> dict:
        created_at = datetime.utcnow().isoformat()
        s = json.dumps(analysis_result, sort_keys=True, separators=(",", ":"))
        analysis_result_hash = hashlib.sha256(s.encode()).hexdigest()
        manifest_hash = compute_manifest_hash(
            session_id=session_id,
            evidence_hashes=evidence_hashes,
            analysis_result_hash=analysis_result_hash,
            created_at=created_at,
        )
        return {
            "evidence_hashes_json": evidence_hashes,
            "analysis_result_hash": analysis_result_hash,
            "manifest_hash": manifest_hash,
            "created_at": created_at,
        }


    def verify_manifest(
        session_id: str,
        evidence_hashes: List[str],
        analysis_result_hash: str,
        stored_manifest_hash: str,
        created_at: str,
    ) -> bool:
        expected = compute_manifest_hash(
            session_id, evidence_hashes, analysis_result_hash, created_at
        )
        return expected == stored_manifest_hash
''')

# ─────────────────────────────────────────────────────────
# services/webhook_service.py
# ─────────────────────────────────────────────────────────
w("services/webhook_service.py", '''
    """
    ArgusCX -- Webhook Service
    HMAC-SHA256 signed webhook delivery (Shopify-style pattern).
    """
    import hashlib
    import hmac
    import json
    import secrets
    from datetime import datetime
    from typing import Any, Dict, Optional

    import httpx
    import structlog

    logger = structlog.get_logger(__name__)
    TIMEOUT_SECONDS = 15


    def generate_webhook_secret() -> str:
        return secrets.token_hex(32)


    def sign_payload(secret: str, payload: str) -> str:
        """Returns sha256=<hex> HMAC signature over payload body."""
        sig = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={sig}"


    def verify_signature(secret: str, payload: str, provided_sig: str) -> bool:
        return hmac.compare_digest(sign_payload(secret, payload), provided_sig)


    async def deliver_webhook(
        url: str,
        secret: str,
        event: str,
        payload: Dict[str, Any],
        attempt: int = 1,
    ) -> bool:
        body = json.dumps(payload, default=str)
        signature = sign_payload(secret, body)
        headers = {
            "Content-Type": "application/json",
            "X-ArgusCX-Signature": signature,
            "X-ArgusCX-Event": event,
            "X-ArgusCX-Delivery-Id": secrets.token_hex(16),
            "X-ArgusCX-Attempt": str(attempt),
            "User-Agent": "ArgusCX-Webhook/1.0",
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                resp = await client.post(url, content=body, headers=headers)
                ok = 200 <= resp.status_code < 300
                if ok:
                    logger.info("Webhook delivered", url=url, event=event, status=resp.status_code)
                else:
                    logger.warning("Webhook failed", url=url, event=event, status=resp.status_code)
                return ok
        except Exception as exc:
            logger.error("Webhook exception", url=url, error=str(exc), attempt=attempt)
            return False


    def build_verification_completed_payload(
        session_id: str,
        order_id: Optional[str],
        case_state: str,
        routing: str,
        risk_signals: Dict[str, Any],
        reasoning_narrative: Optional[str],
        evidence_manifest_hash: Optional[str],
        case_url: str,
    ) -> Dict[str, Any]:
        return {
            "event": "verification.completed",
            "api_version": "2024-09",
            "session_id": session_id,
            "order_id": order_id,
            "case_state": case_state,
            "routing": routing,
            "risk_signals": risk_signals,
            "reasoning_narrative": reasoning_narrative,
            "evidence_manifest_hash": evidence_manifest_hash,
            "case_url": case_url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
''')

# ─────────────────────────────────────────────────────────
# services/risk_engine.py
# ─────────────────────────────────────────────────────────
w("services/risk_engine.py", '''
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
''')

# ─────────────────────────────────────────────────────────
# services/storage_service.py
# ─────────────────────────────────────────────────────────
w("services/storage_service.py", '''
    """
    ArgusCX -- Storage Service
    MinIO/S3 presigned upload URLs + evidence download.
    Gracefully degrades to stub mode when MinIO is unavailable.
    """
    import os
    from datetime import timedelta
    from typing import Optional
    import structlog

    logger = structlog.get_logger(__name__)

    try:
        from minio import Minio
        MINIO_AVAILABLE = True
    except ImportError:
        MINIO_AVAILABLE = False

    _client = None
    _bucket_name = "argusgx-evidence"


    def _get_client():
        global _client
        if _client is not None:
            return _client
        if not MINIO_AVAILABLE:
            return None
        try:
            endpoint   = os.environ.get("MINIO_ENDPOINT",   "localhost:9000")
            access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
            secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
            secure     = os.environ.get("MINIO_SECURE", "false").lower() == "true"
            _client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        except Exception as exc:
            logger.error("MinIO init failed", error=str(exc))
            _client = None
        return _client


    def ensure_bucket():
        c = _get_client()
        if not c:
            return
        try:
            if not c.bucket_exists(_bucket_name):
                c.make_bucket(_bucket_name)
        except Exception as exc:
            logger.error("ensure_bucket failed", error=str(exc))


    def generate_presigned_upload_url(
        session_id: str,
        evidence_id: str,
        mime_type: str = "video/mp4",
        ttl_minutes: int = 15,
    ) -> Optional[str]:
        c = _get_client()
        if not c:
            return f"http://localhost:9000/{_bucket_name}/{session_id}/{evidence_id}"
        obj = f"{session_id}/{evidence_id}"
        try:
            return c.presigned_put_object(_bucket_name, obj, expires=timedelta(minutes=ttl_minutes))
        except Exception as exc:
            logger.error("presigned_url_failed", error=str(exc))
            return None


    def get_evidence_url(session_id: str, evidence_id: str) -> str:
        return f"/{_bucket_name}/{session_id}/{evidence_id}"


    def download_evidence_bytes(storage_url: str) -> Optional[bytes]:
        c = _get_client()
        if not c:
            return None
        try:
            parts = storage_url.lstrip("/").split("/", 1)
            bucket = parts[0] if len(parts) > 0 else _bucket_name
            obj    = parts[1] if len(parts) > 1 else storage_url
            resp = c.get_object(bucket, obj)
            data = resp.read()
            resp.close()
            return data
        except Exception as exc:
            logger.error("download_evidence_failed", url=storage_url, error=str(exc))
            return None
''')

print("=== All services written ===")

# ─────────────────────────────────────────────────────────
# workers/tasks/forensics_worker.py
# ─────────────────────────────────────────────────────────
w("workers/tasks/forensics_worker.py", '''
    """
    ArgusCX -- Forensics Analysis Worker
    Signals: ELA, Noise Analysis, Metadata, pHash

    LIMITATIONS:
    - ELA unreliable on AI-generated or heavily recompressed images.
    - Metadata absence is common on modern phones (weak signal alone).
    - pHash evaded by cropping/rotation/strong color grading.
    """
    import hashlib
    import io
    from typing import Any, Dict, List, Optional, Tuple
    import structlog

    logger = structlog.get_logger(__name__)

    try:
        from PIL import Image
        PIL_AVAILABLE = True
    except ImportError:
        PIL_AVAILABLE = False

    try:
        import cv2
        import numpy as np
        CV2_AVAILABLE = True
    except ImportError:
        CV2_AVAILABLE = False

    try:
        import imagehash
        IMAGEHASH_AVAILABLE = True
    except ImportError:
        IMAGEHASH_AVAILABLE = False

    try:
        import piexif
        PIEXIF_AVAILABLE = True
    except ImportError:
        PIEXIF_AVAILABLE = False

    MODEL_VERSION = "forensics-v1.0"


    def compute_ela(image_bytes: bytes, quality: int = 85) -> Tuple[float, dict]:
        """ELA: detect JPEG compression inconsistencies indicating edits."""
        if not PIL_AVAILABLE:
            return 0.0, {"skipped": "pillow_not_installed"}
        try:
            import numpy as np_local
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            buf.seek(0)
            recomp = Image.open(buf).convert("RGB")
            ela = np_local.abs(np_local.array(img, dtype=np_local.float32) - np_local.array(recomp, dtype=np_local.float32))
            ela_mean = float(np_local.mean(ela)) / 255.0
            ela_max  = float(np_local.max(ela))  / 255.0
            h, w, _ = ela.shape
            bs = max(h // 8, 8)
            regional = [float(np_local.mean(ela[r:r+bs, c:c+bs])) / 255.0
                        for r in range(0, h, bs) for c in range(0, w, bs)]
            region_var = float(np_local.var(regional))
            score = min(ela_mean * 3.0 + region_var * 10.0, 1.0)
            return score, {"ela_mean": round(ela_mean, 4), "ela_max": round(ela_max, 4),
                           "region_variance": round(region_var, 4), "quality_used": quality,
                           "limitation": "ELA unreliable on AI-generated or heavily recompressed images"}
        except Exception as exc:
            logger.error("ELA failed", error=str(exc))
            return 0.0, {"error": str(exc)}


    def analyze_noise(image_bytes: bytes) -> Tuple[float, dict]:
        """Noise residual: composite images may have inconsistent noise."""
        if not CV2_AVAILABLE:
            return 0.0, {"skipped": "opencv_not_installed"}
        try:
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return 0.0, {"error": "decode_failed"}
            denoised = cv2.fastNlMeansDenoising(img, h=10)
            residual = np.abs(img.astype(np.float32) - denoised.astype(np.float32))
            noise_mean = float(np.mean(residual))
            h_img, w_img = img.shape
            bs = max(h_img // 8, 8)
            regional = [float(np.mean(residual[r:r+bs, c:c+bs]))
                        for r in range(0, h_img, bs) for c in range(0, w_img, bs)]
            reg_var = float(np.var(regional)) if regional else 0.0
            score = min(noise_mean / 15.0 * 0.6 + reg_var / 5.0 * 0.4, 1.0)
            return score, {"noise_mean": round(noise_mean, 4), "regional_variance": round(reg_var, 4)}
        except Exception as exc:
            logger.error("Noise analysis failed", error=str(exc))
            return 0.0, {"error": str(exc)}


    def analyze_metadata(image_bytes: bytes) -> Tuple[float, dict]:
        """EXIF metadata anomaly detection."""
        if not PIEXIF_AVAILABLE:
            return 0.0, {"skipped": "piexif_not_installed"}
        try:
            exif = piexif.load(image_bytes)
        except Exception:
            return 0.2, {"findings": ["metadata_completely_absent"],
                         "limitation": "Metadata absence is common on modern phones."}
        score = 0.0
        findings = []
        zero_ifd = exif.get("0th", {})
        exif_ifd = exif.get("Exif", {})
        software = zero_ifd.get(piexif.ImageIFD.Software, b"")
        if isinstance(software, bytes):
            software = software.decode("utf-8", errors="ignore").lower()
        if any(kw in software for kw in ["photoshop", "lightroom", "gimp", "affinity", "snapseed"]):
            findings.append(f"editing_software:{software}")
            score += 0.5
        orig = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal)
        digi = exif_ifd.get(piexif.ExifIFD.DateTimeDigitized)
        if orig and digi and orig != digi:
            findings.append("timestamp_inconsistency")
            score += 0.2
        if not zero_ifd.get(piexif.ImageIFD.Make, b""):
            findings.append("camera_make_missing")
            score += 0.1
        return min(score, 1.0), {"findings": findings, "software": software}


    def compute_phash(image_bytes: bytes) -> Optional[str]:
        """Perceptual hash. Hamming <= 10 = near-duplicate."""
        if not (IMAGEHASH_AVAILABLE and PIL_AVAILABLE):
            return None
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return str(imagehash.phash(img))
        except Exception as exc:
            logger.error("pHash failed", error=str(exc))
            return None


    def phash_distance(h1: str, h2: str) -> int:
        try:
            return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)
        except Exception:
            return 99


    def analyse_evidence(image_bytes: bytes) -> Dict[str, Any]:
        results = {}
        ela_score, ela_det = compute_ela(image_bytes)
        results["ELA"]      = {"score": ela_score,  "details": ela_det,   "model_version": MODEL_VERSION}
        noise_score, n_det  = analyze_noise(image_bytes)
        results["NOISE"]    = {"score": noise_score, "details": n_det,    "model_version": MODEL_VERSION}
        meta_score, m_det   = analyze_metadata(image_bytes)
        results["METADATA"] = {"score": meta_score,  "details": m_det,   "model_version": MODEL_VERSION}
        results["phash"]    = compute_phash(image_bytes)
        results["sha256"]   = hashlib.sha256(image_bytes).hexdigest()
        return results
''')

# ─────────────────────────────────────────────────────────
# workers/tasks/screen_replay_worker.py
# ─────────────────────────────────────────────────────────
w("workers/tasks/screen_replay_worker.py", '''
    """
    ArgusCX -- Screen Replay Detection Worker
    Detects photo/video displayed on a screen instead of real product.
    Signals: Moire (FFT), Planar Geometry, Display Boundary (Hough), Temporal

    LIMITATIONS (all probabilistic):
    - OLED anti-reflection may eliminate moire signal.
    - Full-frame screen may reduce geometry signal.
    - Static real product also has low temporal variance.
    - Challenge-response is the PRIMARY defense.
    """
    from typing import Any, Dict, List, Optional, Tuple
    import structlog

    logger = structlog.get_logger(__name__)

    try:
        import cv2
        import numpy as np
        CV2_AVAILABLE = True
    except ImportError:
        CV2_AVAILABLE = False

    MODEL_VERSION = "screen-replay-v1.0"


    def detect_moire(image_bytes: bytes) -> Tuple[float, dict]:
        """FFT-based moire pattern detection."""
        if not CV2_AVAILABLE:
            return 0.0, {"skipped": "opencv_not_available"}
        try:
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return 0.0, {"error": "decode_failed"}
            f = np.fft.fft2(img.astype(np.float32))
            mag = 20 * np.log(np.abs(np.fft.fftshift(f)) + 1)
            h, w = mag.shape
            cy, cx = h // 2, w // 2
            y_g, x_g = np.ogrid[:h, :w]
            dist = np.sqrt((x_g - cx)**2 + (y_g - cy)**2)
            dc_r = max(h, w) // 16
            mid_mask   = (dist >= dc_r*2)  & (dist <= max(h, w)//4)
            outer_mask = dist > max(h, w)//4
            mid_e   = float(np.mean(mag[mid_mask]))   if mid_mask.any()   else 0.0
            outer_e = float(np.mean(mag[outer_mask])) if outer_mask.any() else 0.0
            total_e = float(np.mean(mag))
            ratio = (mid_e - outer_e) / (total_e + 1e-6)
            score = min(max(ratio / 3.0, 0.0), 1.0)
            return score, {"mid_energy": round(mid_e, 3), "outer_energy": round(outer_e, 3),
                           "moire_ratio": round(ratio, 4),
                           "limitation": "OLED screens may not produce detectable moire"}
        except Exception as exc:
            logger.error("Moire detection failed", error=str(exc))
            return 0.0, {"error": str(exc)}


    def detect_planar_geometry(image_bytes: bytes) -> Tuple[float, dict]:
        """Large quadrilateral = potential screen surface."""
        if not CV2_AVAILABLE:
            return 0.0, {"skipped": "opencv_not_available"}
        try:
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return 0.0, {"error": "decode_failed"}
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            best = 0.0
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if area < h * w * 0.1:
                    continue
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                if len(approx) == 4:
                    best = max(best, min(area / (h * w) * 1.5, 1.0))
            return best, {"rect_area_fraction": round(best, 3),
                          "limitation": "Attacker filling full frame may reduce signal"}
        except Exception as exc:
            logger.error("Planar geometry failed", error=str(exc))
            return 0.0, {"error": str(exc)}


    def detect_display_boundary(image_bytes: bytes) -> Tuple[float, dict]:
        """Hough line transform: screens have strong parallel H/V edges."""
        if not CV2_AVAILABLE:
            return 0.0, {"skipped": "opencv_not_available"}
        try:
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return 0.0, {"error": "decode_failed"}
            edges = cv2.Canny(img, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 80,
                                    minLineLength=img.shape[1]//4, maxLineGap=10)
            if lines is None:
                return 0.0, {"lines_found": 0}
            h_cnt = v_cnt = 0
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                if angle < 10 or angle > 170:
                    h_cnt += 1
                elif 80 < angle < 100:
                    v_cnt += 1
            score = min(min(h_cnt, v_cnt) / 5.0, 1.0)
            return score, {"horizontal_lines": h_cnt, "vertical_lines": v_cnt}
        except Exception as exc:
            logger.error("Display boundary failed", error=str(exc))
            return 0.0, {"error": str(exc)}


    def analyze_temporal_consistency(frames_bytes: List[bytes]) -> Tuple[float, dict]:
        """Low inter-frame variation may indicate static display (weak signal)."""
        if not CV2_AVAILABLE or len(frames_bytes) < 2:
            return 0.0, {"skipped": "insufficient_frames_or_opencv_missing"}
        try:
            diffs, prev = [], None
            for fb in frames_bytes:
                arr = np.frombuffer(fb, dtype=np.uint8)
                fr = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                if fr is None:
                    continue
                if prev is not None:
                    diffs.append(float(np.mean(np.abs(fr.astype(np.float32) - prev.astype(np.float32)))))
                prev = fr
            if not diffs:
                return 0.0, {"skipped": "no_diffs"}
            mean_d = float(np.mean(diffs))
            score = 0.7 if mean_d < 0.5 else (0.4 if mean_d < 1.5 else max(0.0, 0.3 - (mean_d - 1.5) / 10.0))
            return score, {"mean_inter_frame_diff": round(mean_d, 4),
                           "limitation": "Static physical products also have low temporal variance"}
        except Exception as exc:
            logger.error("Temporal consistency failed", error=str(exc))
            return 0.0, {"error": str(exc)}


    def analyse_screen_replay(
        image_bytes: bytes,
        frames_bytes: Optional[List[bytes]] = None,
    ) -> Dict[str, Any]:
        results = {}
        s, d = detect_moire(image_bytes)
        results["MOIRE"]    = {"score": s, "details": d, "model_version": MODEL_VERSION}
        s, d = detect_planar_geometry(image_bytes)
        results["GEOMETRY"] = {"score": s, "details": d, "model_version": MODEL_VERSION}
        s, d = detect_display_boundary(image_bytes)
        results["BOUNDARY"] = {"score": s, "details": d, "model_version": MODEL_VERSION}
        if frames_bytes and len(frames_bytes) >= 2:
            s, d = analyze_temporal_consistency(frames_bytes)
            results["TEMPORAL"] = {"score": s, "details": d, "model_version": MODEL_VERSION}
        return results
''')

# ─────────────────────────────────────────────────────────
# workers/tasks/product_identity_worker.py
# ─────────────────────────────────────────────────────────
w("workers/tasks/product_identity_worker.py", '''
    """
    ArgusCX -- Product Identity Worker
    Signals: OCR serial/model (EasyOCR), barcode/QR (pyzbar), IMEI Luhn check,
             visual similarity (CLIP placeholder).

    LIMITATIONS:
    - OCR unreliable on small text, poor lighting, or extreme angles.
    - pyzbar requires clear barcode without blur.
    - CLIP visual similarity may confuse similar product models.
    - Serial is the primary truth; visual is secondary confirmation.
    """
    import re
    from typing import Any, Dict, List, Optional
    import structlog

    logger = structlog.get_logger(__name__)

    try:
        import easyocr
        EASYOCR_AVAILABLE = True
    except ImportError:
        EASYOCR_AVAILABLE = False
        logger.warning("easyocr not installed -- OCR will be skipped")

    try:
        from pyzbar import pyzbar
        from PIL import Image
        import io
        PYZBAR_AVAILABLE = True
    except ImportError:
        PYZBAR_AVAILABLE = False

    MODEL_VERSION = "product-identity-v1.0"
    _ocr_reader = None


    def _get_reader():
        global _ocr_reader
        if _ocr_reader is None and EASYOCR_AVAILABLE:
            try:
                _ocr_reader = easyocr.Reader(["en"], gpu=False)
                logger.info("EasyOCR reader initialised")
            except Exception as exc:
                logger.error("EasyOCR init failed", error=str(exc))
        return _ocr_reader


    # IMEI Luhn validation
    def validate_imei(s: str) -> bool:
        digits = re.sub(r"\\D", "", s)
        if len(digits) != 15:
            return False
        total = 0
        for i, d in enumerate(digits):
            n = int(d)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0


    def extract_serials_from_text(text: str) -> List[str]:
        """Extract likely serial/IMEI numbers from OCR text."""
        candidates = []
        # IMEI pattern: 15 consecutive digits
        candidates.extend(re.findall(r"\\b\\d{15}\\b", text))
        # S/N pattern: alphanumeric 8-20 chars after S/N or SN or Serial
        candidates.extend(re.findall(r"(?:S/?N|Serial|SN)[:\\s]*([A-Z0-9]{8,20})", text, re.IGNORECASE))
        return list(dict.fromkeys(candidates))  # deduplicate, preserve order


    def run_ocr(image_bytes: bytes) -> Dict[str, Any]:
        """Run EasyOCR on image. Returns all detected text and extracted serials."""
        reader = _get_reader()
        if not reader:
            return {"skipped": True, "text": "", "serials": [], "limitation": "easyocr_not_available"}
        try:
            import numpy as np
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            import cv2
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return {"error": "decode_failed", "text": "", "serials": []}
            results = reader.readtext(img, detail=0)
            full_text = " ".join(results)
            serials = extract_serials_from_text(full_text)
            return {"text": full_text, "serials": serials, "raw_lines": results}
        except Exception as exc:
            logger.error("OCR failed", error=str(exc))
            return {"error": str(exc), "text": "", "serials": []}


    def decode_barcodes(image_bytes: bytes) -> Dict[str, Any]:
        """Decode QR codes and barcodes using pyzbar."""
        if not PYZBAR_AVAILABLE:
            return {"skipped": True, "barcodes": [], "qr_codes": []}
        try:
            from PIL import Image as PILImage
            import io as io_module
            img = PILImage.open(io_module.BytesIO(image_bytes))
            decoded = pyzbar.decode(img)
            barcodes = [d.data.decode("utf-8", errors="ignore") for d in decoded if d.type != "QRCODE"]
            qr_codes = [d.data.decode("utf-8", errors="ignore") for d in decoded if d.type == "QRCODE"]
            return {"barcodes": barcodes, "qr_codes": qr_codes}
        except Exception as exc:
            logger.error("Barcode decode failed", error=str(exc))
            return {"error": str(exc), "barcodes": [], "qr_codes": []}


    def compare_serials(detected: Optional[str], expected: Optional[str]) -> Dict[str, Any]:
        """Compare detected vs expected serial number."""
        if not expected:
            return {"serial_match": None, "note": "no_expected_serial_provided"}
        if not detected:
            return {"serial_match": None, "serial_readable": False,
                    "note": "serial_not_detected_in_evidence"}
        match = detected.strip().upper() == expected.strip().upper()
        return {
            "serial_match": match,
            "serial_readable": True,
            "detected_serial": detected,
            "expected_serial": expected,
            "note": "Serial match confirmed." if match else "Serial mismatch detected.",
        }


    def analyse_product_identity(
        image_bytes: bytes,
        expected_serial: Optional[str] = None,
        expected_sku: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full product identity analysis."""
        ocr_result      = run_ocr(image_bytes)
        barcode_result  = decode_barcodes(image_bytes)

        # Best serial candidate: first from OCR serials, or first barcode
        detected_serial = None
        if ocr_result.get("serials"):
            detected_serial = ocr_result["serials"][0]
        elif barcode_result.get("barcodes"):
            detected_serial = barcode_result["barcodes"][0]

        serial_cmp = compare_serials(detected_serial, expected_serial)
        imei_valid = validate_imei(detected_serial) if detected_serial else None

        return {
            "detected_serial":         detected_serial,
            "expected_serial":         expected_serial,
            "serial_match":            serial_cmp.get("serial_match"),
            "serial_readable":         serial_cmp.get("serial_readable", True),
            "detected_barcode":        (barcode_result.get("barcodes") or [None])[0],
            "detected_qr":             (barcode_result.get("qr_codes")  or [None])[0],
            "ocr_model_text":          ocr_result.get("text", ""),
            "imei_valid":              imei_valid,
            "visual_similarity_score": None,   # CLIP placeholder
            "product_category_match":  None,   # CLIP placeholder
            "details_json": {
                "ocr": ocr_result,
                "barcodes": barcode_result,
                "serial_comparison": serial_cmp,
                "limitation": "OCR unreliable on blurry/small text. Visual match is approximate.",
            },
            "model_version": MODEL_VERSION,
        }
''')

# ─────────────────────────────────────────────────────────
# workers/tasks/damage_worker.py
# ─────────────────────────────────────────────────────────
w("workers/tasks/damage_worker.py", '''
    """
    ArgusCX -- Damage Detection Worker
    YOLOv8 object detection + segmentation for product damage.
    Multi-frame consensus for video evidence.

    LIMITATION: YOLOv8 accuracy depends on training data quality.
    Use Roboflow Universe vehicle/product damage datasets for fine-tuning.
    """
    import io
    from typing import Any, Dict, List, Optional
    import structlog

    logger = structlog.get_logger(__name__)

    try:
        from ultralytics import YOLO
        YOLO_AVAILABLE = True
    except ImportError:
        YOLO_AVAILABLE = False
        logger.warning("ultralytics not installed -- damage detection disabled")

    try:
        from PIL import Image
        PIL_AVAILABLE = True
    except ImportError:
        PIL_AVAILABLE = False

    MODEL_VERSION = "yolov8s-damage-v1.0"
    _model = None

    DAMAGE_CLASSES = [
        "screen_crack", "dent", "scratch", "water_damage",
        "missing_parts", "burn_mark", "case_damage",
    ]

    SEVERITY_MAP = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}


    def _get_model():
        global _model
        if _model is not None:
            return _model
        if not YOLO_AVAILABLE:
            return None
        import os
        # Use fine-tuned model if available, else fall back to yolov8s
        model_path = os.environ.get("DAMAGE_MODEL_PATH", "yolov8s.pt")
        try:
            _model = YOLO(model_path)
            logger.info("YOLOv8 model loaded", path=model_path)
        except Exception as exc:
            logger.error("YOLOv8 load failed", error=str(exc), path=model_path)
            _model = None
        return _model


    def _mask_area_fraction(result) -> float:
        """Compute segmentation mask coverage as fraction of image area."""
        try:
            if result.masks is None:
                return 0.0
            import numpy as np
            total = 0.0
            img_pixels = result.orig_shape[0] * result.orig_shape[1]
            for mask in result.masks.data:
                total += float(mask.sum().item())
            return min(total / img_pixels, 1.0)
        except Exception:
            return 0.0


    def _score_to_severity(mask_fraction: float, conf: float) -> str:
        if mask_fraction < 0.005 or conf < 0.3:
            return "NONE"
        elif mask_fraction < 0.02:
            return "LOW"
        elif mask_fraction < 0.10:
            return "MEDIUM"
        else:
            return "HIGH"


    def detect_damage_in_image(image_bytes: bytes) -> Dict[str, Any]:
        """Run YOLOv8 on a single image frame."""
        model = _get_model()
        if not model:
            return {
                "damage_types": [], "severity": "NONE",
                "bounding_boxes_json": [], "confidence": None,
                "skipped": True, "reason": "yolov8_not_available",
            }
        try:
            import numpy as np
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            import cv2
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return {"damage_types": [], "severity": "NONE", "bounding_boxes_json": [], "confidence": None}
            results = model(img, verbose=False)
            result = results[0]

            damage_types = []
            boxes = []
            confidences = []
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                cls_name = model.names.get(cls_id, f"class_{cls_id}")
                conf = float(box.conf[0].item())
                if conf < 0.35:
                    continue
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                boxes.append({"class": cls_name, "confidence": round(conf, 3),
                              "x1": round(x1), "y1": round(y1), "x2": round(x2), "y2": round(y2)})
                if cls_name not in damage_types:
                    damage_types.append(cls_name)
                confidences.append(conf)

            mask_fraction = _mask_area_fraction(result)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            severity = _score_to_severity(mask_fraction, avg_conf)

            return {
                "damage_types":        damage_types,
                "severity":            severity,
                "bounding_boxes_json": boxes,
                "confidence":          round(avg_conf, 3),
                "mask_fraction":       round(mask_fraction, 4),
                "model_version":       MODEL_VERSION,
            }
        except Exception as exc:
            logger.error("Damage detection failed", error=str(exc))
            return {"damage_types": [], "severity": "NONE", "bounding_boxes_json": [], "confidence": None,
                    "error": str(exc)}


    def detect_damage_multi_frame(frames_bytes: List[bytes]) -> Dict[str, Any]:
        """Multi-frame consensus: aggregate damage across video frames."""
        if not frames_bytes:
            return {"damage_types": [], "severity": "NONE", "bounding_boxes_json": [],
                    "confidence": None, "frame_count": 0}

        all_damage_types: dict = {}
        all_boxes = []
        all_confidences = []
        severity_votes = {"NONE": 0, "LOW": 0, "MEDIUM": 0, "HIGH": 0}

        for fb in frames_bytes:
            r = detect_damage_in_image(fb)
            for dt in r.get("damage_types", []):
                all_damage_types[dt] = all_damage_types.get(dt, 0) + 1
            all_boxes.extend(r.get("bounding_boxes_json", []))
            if r.get("confidence"):
                all_confidences.append(r["confidence"])
            sv = r.get("severity", "NONE")
            severity_votes[sv] = severity_votes.get(sv, 0) + 1

        # Keep damage types seen in >= 30% of frames
        threshold = max(len(frames_bytes) * 0.3, 1)
        confirmed_damage = [dt for dt, count in all_damage_types.items() if count >= threshold]

        # Consensus severity (highest with >= 1 vote wins for demo; in production: >50%)
        consensus_sev = max(severity_votes, key=lambda s: (severity_votes[s], SEVERITY_MAP.get(s, 0)))
        avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else None

        return {
            "damage_types":        confirmed_damage,
            "severity":            consensus_sev,
            "bounding_boxes_json": all_boxes[:20],  # cap for storage
            "confidence":          round(avg_conf, 3) if avg_conf else None,
            "frame_count":         len(frames_bytes),
            "model_version":       MODEL_VERSION,
        }
''')

# ─────────────────────────────────────────────────────────
# workers/tasks/reasoning_worker.py
# ─────────────────────────────────────────────────────────
w("workers/tasks/reasoning_worker.py", '''
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
''')

# ─────────────────────────────────────────────────────────
# api/routes/sessions.py  -- The Core Session API
# ─────────────────────────────────────────────────────────
w("api/routes/sessions.py", '''
    """
    ArgusCX -- Verification Session API

    POST /api/v1/sessions                  Create a verification session
    GET  /api/v1/sessions/{id}             Session status
    GET  /api/v1/sessions/{id}/result      Full case report
    POST /api/v1/sessions/{id}/complete    Mark session completed (from capture UI)
    POST /api/v1/sessions/{id}/outbound-evidence  Upload warehouse photos
    GET  /api/v1/sessions/{id}/qr          QR code for mobile redirect
    """
    import secrets
    import qrcode
    import io
    import base64
    from datetime import datetime, timedelta
    from typing import Any, Dict, List, Optional

    from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
    from pydantic import BaseModel, Field
    import structlog

    from app.services.challenge_generator import (
        generate_session_nonce,
        generate_challenge_sequence,
        ChallengeStep,
        DEFAULT_CHALLENGE_COUNT,
    )

    logger = structlog.get_logger(__name__)
    router = APIRouter(prefix="/sessions")

    SESSION_TTL_MINUTES = 30

    # ---- In-memory store (upgrade to DB when PostgreSQL connected) ----
    _sessions: Dict[str, dict] = {}
    _cases: Dict[str, dict] = {}


    # ──────────────────────────────────────────────
    #  REQUEST / RESPONSE SCHEMAS
    # ──────────────────────────────────────────────

    class SessionCreateRequest(BaseModel):
        order_id: Optional[str] = None
        customer_ref: Optional[str] = None
        sku: Optional[str] = None
        category: Optional[str] = None
        expected_serial: Optional[str] = None
        claim_text: Optional[str] = None
        return_reason: Optional[str] = None
        challenge_count: int = Field(DEFAULT_CHALLENGE_COUNT, ge=3, le=10)
        require_serial_challenge: bool = True
        require_packaging_challenge: bool = False
        metadata: Dict[str, Any] = {}


    class ChallengeInfo(BaseModel):
        step_index: int
        challenge_type: str
        instruction_text: str
        required_action: str


    class SessionCreateResponse(BaseModel):
        session_id: str
        capture_url: str
        session_token: str
        expires_at: str
        challenge_count: int
        challenges: List[ChallengeInfo]
        qr_code_url: str
        status: str


    class SessionStatusResponse(BaseModel):
        session_id: str
        status: str
        order_id: Optional[str]
        assurance_level: str
        challenges_total: int
        challenges_completed: int
        created_at: str
        expires_at: str
        completed_at: Optional[str]


    class SessionCompleteRequest(BaseModel):
        assurance_level: str = "live_video"
        evidence_ids: List[str] = []


    class OutboundEvidenceRequest(BaseModel):
        urls: List[str] = Field(..., min_items=1, max_items=10)


    # ──────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────

    def _generate_session_token(session_id: str) -> str:
        return f"ses_tok_{secrets.token_hex(24)}"


    def _build_capture_url(session_id: str, base_url: str = "http://localhost:3000") -> str:
        return f"{base_url}/verify/{session_id}"


    def _generate_qr_b64(url: str) -> str:
        try:
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        except Exception:
            return ""


    # ──────────────────────────────────────────────
    #  ROUTES
    # ──────────────────────────────────────────────

    @router.post("", response_model=SessionCreateResponse, status_code=201)
    async def create_session(req: SessionCreateRequest, request: Request):
        """Create a verification session and return the capture URL + QR code."""
        nonce = generate_session_nonce()
        session_id = f"ses_{secrets.token_hex(10)}"
        session_token = _generate_session_token(session_id)
        expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)

        challenges = generate_challenge_sequence(
            nonce=nonce,
            count=req.challenge_count,
            require_serial=req.require_serial_challenge,
            require_packaging=req.require_packaging_challenge,
        )

        # Determine base URL from request
        base = str(request.base_url).rstrip("/").replace(":8000", ":3000")
        capture_url = _build_capture_url(session_id, base)

        session = {
            "id": session_id,
            "order_id": req.order_id,
            "customer_ref": req.customer_ref,
            "sku": req.sku,
            "category": req.category,
            "expected_serial": req.expected_serial,
            "claim_text": req.claim_text,
            "return_reason": req.return_reason,
            "status": "pending",
            "assurance_level": "unknown",
            "nonce": nonce,
            "session_token": session_token,
            "challenge_sequence": [c.dict() for c in challenges],
            "challenges_completed": 0,
            "evidence_ids": [],
            "outbound_evidence_urls": [],
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "metadata": req.metadata,
        }
        _sessions[session_id] = session

        logger.info("Session created", session_id=session_id, order_id=req.order_id)

        return SessionCreateResponse(
            session_id=session_id,
            capture_url=capture_url,
            session_token=session_token,
            expires_at=expires_at.isoformat(),
            challenge_count=len(challenges),
            challenges=[ChallengeInfo(**c.dict()) for c in challenges],
            qr_code_url=f"/api/v1/sessions/{session_id}/qr",
            status="pending",
        )


    @router.get("/{session_id}", response_model=SessionStatusResponse)
    async def get_session(session_id: str):
        """Get session status."""
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionStatusResponse(
            session_id=session_id,
            status=session["status"],
            order_id=session.get("order_id"),
            assurance_level=session["assurance_level"],
            challenges_total=len(session.get("challenge_sequence", [])),
            challenges_completed=session.get("challenges_completed", 0),
            created_at=session["created_at"],
            expires_at=session["expires_at"],
            completed_at=session.get("completed_at"),
        )


    @router.get("/{session_id}/result")
    async def get_session_result(session_id: str):
        """Get the full case report for a completed session."""
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session["status"] not in ("completed", "analysed"):
            raise HTTPException(
                status_code=202,
                detail={"message": "Analysis in progress", "status": session["status"]}
            )
        case = _cases.get(session_id)
        return {
            "session_id": session_id,
            "status": session["status"],
            "case": case,
            "challenges": session.get("challenge_sequence", []),
            "evidence_ids": session.get("evidence_ids", []),
        }


    @router.post("/{session_id}/complete")
    async def complete_session(
        session_id: str,
        req: SessionCompleteRequest,
        background_tasks: BackgroundTasks,
    ):
        """
        Called by the capture UI when all challenges are done.
        Triggers async analysis pipeline.
        """
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session["status"] not in ("pending", "in_progress"):
            raise HTTPException(status_code=409, detail=f"Session already {session['status']}")

        # Check expiry
        if datetime.utcnow().isoformat() > session["expires_at"]:
            session["status"] = "expired"
            raise HTTPException(status_code=410, detail="Session has expired")

        session["status"] = "analysing"
        session["assurance_level"] = req.assurance_level
        session["evidence_ids"] = req.evidence_ids
        session["completed_at"] = datetime.utcnow().isoformat()

        # Trigger async analysis
        background_tasks.add_task(_run_analysis_pipeline, session_id)

        return {"message": "Analysis started", "session_id": session_id, "status": "analysing"}


    @router.post("/{session_id}/outbound-evidence")
    async def upload_outbound_evidence(session_id: str, req: OutboundEvidenceRequest):
        """Merchant uploads warehouse/outbound photos for comparison."""
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session["outbound_evidence_urls"] = req.urls
        return {"message": "Outbound evidence recorded", "count": len(req.urls)}


    @router.get("/{session_id}/qr")
    async def get_session_qr(session_id: str, request: Request):
        """Return a QR code image (base64 PNG) linking to the capture URL."""
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        base = str(request.base_url).rstrip("/").replace(":8000", ":3000")
        capture_url = _build_capture_url(session_id, base)
        qr_b64 = _generate_qr_b64(capture_url)
        return {
            "session_id": session_id,
            "capture_url": capture_url,
            "qr_code_data_uri": qr_b64,
        }


    # ──────────────────────────────────────────────
    #  ANALYSIS PIPELINE (stub -- workers plug in here)
    # ──────────────────────────────────────────────

    async def _run_analysis_pipeline(session_id: str):
        """
        Orchestrate the full analysis pipeline for a session.
        In production: Celery chord/group coordinates parallel workers.
        For demo: runs sequentially in background task.
        """
        session = _sessions.get(session_id)
        if not session:
            return

        logger.info("Analysis pipeline started", session_id=session_id)

        try:
            from app.services.risk_engine import (
                compute_risk_signals, determine_case_state, build_case,
            )
            from app.services.manifest_service import build_manifest

            # === Stub signal data (workers fill real data in production) ===
            forensic_findings = []
            screen_replay_findings = []
            challenge_completion_ratio = (
                session.get("challenges_completed", 0) /
                max(len(session.get("challenge_sequence", [])), 1)
            )
            product_identity = None
            damage_finding = None
            evidence_reuse = None
            llm_reasoning = None
            outbound_comparison = None

            # === Run risk engine ===
            signals = compute_risk_signals(
                forensic_findings=forensic_findings,
                screen_replay_findings=screen_replay_findings,
                challenge_completion_ratio=challenge_completion_ratio,
                product_identity=product_identity,
                damage_finding=damage_finding,
                evidence_reuse=evidence_reuse,
                llm_reasoning=llm_reasoning,
                outbound_comparison=outbound_comparison,
                assurance_level=session["assurance_level"],
                policy=session.get("policy_json", {}),
            )

            state, routing, reasoning_prefix = determine_case_state(signals, session.get("policy_json", {}))

            case = build_case(
                session_id=session_id,
                tenant_id="demo_tenant",
                signals=signals,
                state=state,
                routing=routing,
                reasoning_prefix=reasoning_prefix,
                llm_narrative=None,
                claim_assertions=[],
                contradictions=[],
            )
            case["id"] = f"cas_{secrets.token_hex(8)}"
            _cases[session_id] = case

            # Build manifest
            evidence_hashes = session.get("evidence_ids", [])
            manifest = build_manifest(session_id, evidence_hashes, {"signals": signals})
            case["manifest_hash"] = manifest["manifest_hash"]

            session["status"] = "completed"
            logger.info("Analysis complete", session_id=session_id, state=state, routing=routing)

        except Exception as exc:
            logger.error("Analysis pipeline failed", session_id=session_id, error=str(exc))
            session["status"] = "completed"
            _cases[session_id] = {
                "id": f"cas_{secrets.token_hex(8)}",
                "session_id": session_id,
                "state": "REVIEW_REQUIRED",
                "routing": "REVIEW_REQUIRED",
                "risk_signals_json": {},
                "reasoning_narrative": f"Analysis pipeline error: {exc}",
                "claim_assertions_json": [],
                "contradictions_json": [],
            }
''')

# ─────────────────────────────────────────────────────────
# api/routes/cases.py
# ─────────────────────────────────────────────────────────
w("api/routes/cases.py", '''
    """
    ArgusCX -- Cases API

    GET  /api/v1/cases           List cases
    GET  /api/v1/cases/{id}      Full case detail
    POST /api/v1/cases/{id}/review       Reviewer decision
    POST /api/v1/cases/{id}/escalate     Force escalation
    """
    import secrets
    from datetime import datetime
    from typing import Any, Dict, List, Optional

    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    import structlog

    from app.api.routes.sessions import _cases, _sessions

    logger = structlog.get_logger(__name__)
    router = APIRouter(prefix="/cases")


    class ReviewRequest(BaseModel):
        reviewer_id: str
        decision: str           # APPROVED | REJECTED | ESCALATED
        notes: Optional[str] = None


    @router.get("")
    async def list_cases(
        state: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ):
        """List all cases, optionally filtered by state."""
        all_cases = list(_cases.values())
        if state:
            all_cases = [c for c in all_cases if c.get("state") == state.upper()]
        total = len(all_cases)
        page = all_cases[offset:offset + limit]
        # Enrich with session info
        enriched = []
        for c in page:
            sid = c.get("session_id")
            sess = _sessions.get(sid, {})
            enriched.append({
                **c,
                "order_id": sess.get("order_id"),
                "customer_ref": sess.get("customer_ref"),
                "category": sess.get("category"),
                "assurance_level": sess.get("assurance_level"),
                "created_at": sess.get("created_at"),
            })
        return {"total": total, "cases": enriched, "limit": limit, "offset": offset}


    @router.get("/{case_id}")
    async def get_case(case_id: str):
        """Full case report with all signals and evidence."""
        case = next((c for c in _cases.values() if c.get("id") == case_id), None)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        sid = case.get("session_id")
        session = _sessions.get(sid, {})
        return {
            **case,
            "session": {
                "id": sid,
                "order_id": session.get("order_id"),
                "customer_ref": session.get("customer_ref"),
                "claim_text": session.get("claim_text"),
                "return_reason": session.get("return_reason"),
                "category": session.get("category"),
                "expected_serial": session.get("expected_serial"),
                "assurance_level": session.get("assurance_level"),
                "challenges": session.get("challenge_sequence", []),
                "evidence_ids": session.get("evidence_ids", []),
                "created_at": session.get("created_at"),
            },
        }


    @router.post("/{case_id}/review")
    async def review_case(case_id: str, req: ReviewRequest):
        """Reviewer submits a decision on a case."""
        case = next((c for c in _cases.values() if c.get("id") == case_id), None)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        valid_decisions = {"APPROVED", "REJECTED", "ESCALATED"}
        if req.decision.upper() not in valid_decisions:
            raise HTTPException(status_code=422, detail=f"Decision must be one of {valid_decisions}")
        case["reviewer_id"] = req.reviewer_id
        case["reviewer_decision"] = req.decision.upper()
        case["reviewer_notes"] = req.notes
        case["reviewed_at"] = datetime.utcnow().isoformat()
        logger.info("Case reviewed", case_id=case_id, decision=req.decision, reviewer=req.reviewer_id)
        return {"message": "Review recorded", "case_id": case_id, "decision": req.decision.upper()}


    @router.post("/{case_id}/escalate")
    async def escalate_case(case_id: str, reason: Optional[str] = None):
        """Force a case to REVIEW_REQUIRED state."""
        case = next((c for c in _cases.values() if c.get("id") == case_id), None)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        case["state"] = "REVIEW_REQUIRED"
        case["routing"] = "REVIEW_REQUIRED"
        if reason:
            case["reasoning_narrative"] = (case.get("reasoning_narrative") or "") + f" [Escalated: {reason}]"
        return {"message": "Case escalated", "case_id": case_id, "state": "REVIEW_REQUIRED"}
''')

print("=== API routes written ===")
# Now write frontend verify page
os.makedirs(os.path.join(FRONT, "app", "verify", "[session_id]"), exist_ok=True)

wf("app/verify/[session_id]/page.tsx", '''
    "use client";
    /**
     * ArgusCX -- Mobile Verification Capture Page
     * Renders the live challenge-response camera capture UI.
     * iOS Safari compatible: video element with playsinline + muted + autoplay.
     */
    import React, { useState, useEffect, useRef, useCallback } from "react";

    interface Challenge {
      step_index: number;
      challenge_type: string;
      instruction_text: string;
      required_action: string;
    }

    interface SessionData {
      session_id: string;
      challenges: Challenge[];
      capture_url: string;
      expires_at: string;
    }

    type CapturePhase =
      | "loading"
      | "permission_request"
      | "permission_denied"
      | "challenge"
      | "uploading"
      | "completed"
      | "error"
      | "expired";

    export default function VerifyPage({ params }: { params: { session_id: string } }) {
      const sessionId = params.session_id;
      const videoRef = useRef<HTMLVideoElement>(null);
      const streamRef = useRef<MediaStream | null>(null);

      const [phase, setPhase] = useState<CapturePhase>("loading");
      const [session, setSession] = useState<SessionData | null>(null);
      const [currentChallengeIdx, setCurrentChallengeIdx] = useState(0);
      const [completedChallenges, setCompletedChallenges] = useState<number[]>([]);
      const [error, setError] = useState<string>("");
      const [uploadProgress, setUploadProgress] = useState(0);
      const [qualityWarning, setQualityWarning] = useState<string>("");

      // Fetch session data
      useEffect(() => {
        fetch(`/api/v1/sessions/${sessionId}`)
          .then((r) => {
            if (r.status === 410) { setPhase("expired"); return null; }
            if (!r.ok) throw new Error("Session not found");
            return r.json();
          })
          .then((data) => {
            if (!data) return;
            // Also fetch full session with challenges
            return fetch(`/api/v1/sessions/${sessionId}/result`).catch(() => null);
          })
          .catch((e) => {
            setError(e.message);
            setPhase("error");
          });

        // Load session including challenges from the create response stored in sessionStorage
        const stored = sessionStorage.getItem(`argusgx_session_${sessionId}`);
        if (stored) {
          setSession(JSON.parse(stored));
          setPhase("permission_request");
        } else {
          // Fallback: fetch session status (won't have challenges without token)
          fetch(`/api/v1/sessions/${sessionId}`)
            .then((r) => r.json())
            .then((data) => {
              setSession({ session_id: sessionId, challenges: [], capture_url: "", expires_at: data.expires_at });
              setPhase("permission_request");
            })
            .catch(() => { setPhase("error"); setError("Could not load session."); });
        }
      }, [sessionId]);

      const requestCamera = useCallback(async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: { ideal: "environment" },
              width: { ideal: 1920 },
              height: { ideal: 1080 },
            },
            audio: false,
          });
          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
          setPhase("challenge");
        } catch (err: any) {
          if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            setPhase("permission_denied");
          } else {
            setError(`Camera error: ${err.message}`);
            setPhase("error");
          }
        }
      }, []);

      const completeChallenge = useCallback(() => {
        const idx = currentChallengeIdx;
        setCompletedChallenges((prev) => [...prev, idx]);
        const challenges = session?.challenges || [];
        if (idx + 1 >= challenges.length) {
          // All challenges done -- submit
          submitSession();
        } else {
          setCurrentChallengeIdx(idx + 1);
        }
      }, [currentChallengeIdx, session]);

      const submitSession = useCallback(async () => {
        setPhase("uploading");
        setUploadProgress(10);
        try {
          const resp = await fetch(`/api/v1/sessions/${sessionId}/complete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              assurance_level: "live_video",
              evidence_ids: completedChallenges.map((i) => `frame_${i}_${Date.now()}`),
            }),
          });
          setUploadProgress(100);
          if (resp.ok) {
            setPhase("completed");
          } else {
            throw new Error("Submission failed");
          }
        } catch (e: any) {
          setError(e.message);
          setPhase("error");
        } finally {
          // Stop camera
          streamRef.current?.getTracks().forEach((t) => t.stop());
        }
      }, [sessionId, completedChallenges]);

      const challenges = session?.challenges || [];
      const currentChallenge = challenges[currentChallengeIdx];
      const progressPct = challenges.length ? (completedChallenges.length / challenges.length) * 100 : 0;

      // ── RENDER ──
      return (
        <div style={styles.container}>
          {/* Header */}
          <div style={styles.header}>
            <div style={styles.logo}>ArgusCX</div>
            <div style={styles.headerSub}>Return Verification</div>
          </div>

          {/* Progress bar */}
          {phase === "challenge" && challenges.length > 0 && (
            <div style={styles.progressBar}>
              <div style={{ ...styles.progressFill, width: `${progressPct}%` }} />
            </div>
          )}

          {/* Main content */}
          <div style={styles.content}>
            {phase === "loading" && (
              <div style={styles.centered}>
                <div style={styles.spinner} />
                <p style={styles.subText}>Loading session...</p>
              </div>
            )}

            {phase === "permission_request" && (
              <div style={styles.centered}>
                <div style={styles.iconLarge}>📷</div>
                <h1 style={styles.title}>Camera Access Needed</h1>
                <p style={styles.bodyText}>
                  We need your camera to capture live evidence of the product.
                  Your session is secure and expires in 30 minutes.
                </p>
                <button style={styles.primaryBtn} onClick={requestCamera}>
                  Allow Camera
                </button>
                <p style={styles.hint}>
                  iOS: tap Allow when prompted. Android: tap Allow or OK.
                </p>
              </div>
            )}

            {phase === "permission_denied" && (
              <div style={styles.centered}>
                <div style={styles.iconLarge}>🔒</div>
                <h1 style={styles.title}>Camera Access Denied</h1>
                <p style={styles.bodyText}>
                  Please enable camera access in your browser settings and refresh this page.
                </p>
                <p style={styles.hint}>
                  iOS: Settings → Safari → Camera → Allow<br />
                  Android: Site settings → Camera → Allow
                </p>
                <button style={styles.secondaryBtn} onClick={() => window.location.reload()}>
                  Try Again
                </button>
              </div>
            )}

            {phase === "challenge" && (
              <div style={styles.challengeContainer}>
                {/* Live camera feed */}
                <div style={styles.videoWrapper}>
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    playsInline
                    style={styles.video}
                  />
                  {/* Challenge overlay */}
                  <div style={styles.videoOverlay}>
                    <div style={styles.challengeStep}>
                      Step {currentChallengeIdx + 1} of {challenges.length}
                    </div>
                  </div>
                </div>

                {/* Challenge instruction */}
                {currentChallenge && (
                  <div style={styles.challengeCard}>
                    <div style={styles.challengeIcon}>
                      {getChallengeIcon(currentChallenge.challenge_type)}
                    </div>
                    <p style={styles.challengeInstruction}>
                      {currentChallenge.instruction_text}
                    </p>
                    {qualityWarning && (
                      <div style={styles.qualityWarning}>{qualityWarning}</div>
                    )}
                    <button style={styles.primaryBtn} onClick={completeChallenge}>
                      Done ✓
                    </button>
                  </div>
                )}
              </div>
            )}

            {phase === "uploading" && (
              <div style={styles.centered}>
                <div style={styles.spinner} />
                <h1 style={styles.title}>Submitting Evidence</h1>
                <div style={styles.uploadBar}>
                  <div style={{ ...styles.uploadFill, width: `${uploadProgress}%` }} />
                </div>
                <p style={styles.subText}>{uploadProgress}% — Please keep this page open</p>
              </div>
            )}

            {phase === "completed" && (
              <div style={styles.centered}>
                <div style={styles.iconLarge}>✅</div>
                <h1 style={styles.title}>Verification Complete</h1>
                <p style={styles.bodyText}>
                  Your evidence has been submitted for review.
                  You will be notified of the outcome shortly.
                </p>
                <p style={styles.hint}>You may now close this window.</p>
              </div>
            )}

            {phase === "expired" && (
              <div style={styles.centered}>
                <div style={styles.iconLarge}>⏰</div>
                <h1 style={styles.title}>Session Expired</h1>
                <p style={styles.bodyText}>
                  This verification link has expired. Please contact support
                  to receive a new verification link.
                </p>
              </div>
            )}

            {phase === "error" && (
              <div style={styles.centered}>
                <div style={styles.iconLarge}>⚠️</div>
                <h1 style={styles.title}>Something Went Wrong</h1>
                <p style={styles.bodyText}>{error || "An unexpected error occurred."}</p>
                <button style={styles.secondaryBtn} onClick={() => window.location.reload()}>
                  Retry
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div style={styles.footer}>
            <p style={styles.footerText}>Secured by ArgusCX · Evidence encrypted in transit</p>
          </div>
        </div>
      );
    }

    function getChallengeIcon(type: string): string {
      const icons: Record<string, string> = {
        SHOW_FRONT: "📱", SHOW_BACK: "🔄", MOVE_LEFT: "⬅️",
        MOVE_RIGHT: "➡️", MOVE_UP: "⬆️", FOCUS_SERIAL: "🔍",
        SHOW_PACKAGING: "📦", SHOW_DAMAGE: "🔎", ROTATE_PRODUCT: "🔃",
      };
      return icons[type] || "📸";
    }

    const styles: Record<string, React.CSSProperties> = {
      container:           { minHeight: "100vh", background: "#0a0a14", color: "#fff", fontFamily: "'Inter', -apple-system, sans-serif", display: "flex", flexDirection: "column" },
      header:              { background: "rgba(255,255,255,0.05)", padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.1)" },
      logo:                { fontSize: "18px", fontWeight: 700, color: "#7C3AED", letterSpacing: "0.5px" },
      headerSub:           { fontSize: "12px", color: "rgba(255,255,255,0.5)" },
      progressBar:         { height: "3px", background: "rgba(255,255,255,0.1)" },
      progressFill:        { height: "100%", background: "linear-gradient(90deg, #7C3AED, #4F46E5)", transition: "width 0.4s ease" },
      content:             { flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: "24px 20px" },
      centered:            { display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", gap: "16px" },
      iconLarge:           { fontSize: "64px" },
      title:               { fontSize: "24px", fontWeight: 700, margin: 0 },
      bodyText:            { fontSize: "16px", color: "rgba(255,255,255,0.75)", lineHeight: 1.6, maxWidth: "340px", margin: 0 },
      hint:                { fontSize: "13px", color: "rgba(255,255,255,0.45)", lineHeight: 1.5, maxWidth: "300px" },
      subText:             { fontSize: "14px", color: "rgba(255,255,255,0.6)" },
      primaryBtn:          { background: "linear-gradient(135deg, #7C3AED, #4F46E5)", color: "#fff", border: "none", borderRadius: "12px", padding: "16px 32px", fontSize: "17px", fontWeight: 600, cursor: "pointer", width: "100%", maxWidth: "320px" },
      secondaryBtn:        { background: "rgba(255,255,255,0.1)", color: "#fff", border: "1px solid rgba(255,255,255,0.2)", borderRadius: "12px", padding: "14px 28px", fontSize: "16px", cursor: "pointer" },
      spinner:             { width: "48px", height: "48px", border: "4px solid rgba(124,58,237,0.3)", borderTop: "4px solid #7C3AED", borderRadius: "50%", animation: "spin 1s linear infinite" },
      uploadBar:           { width: "280px", height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden" },
      uploadFill:          { height: "100%", background: "linear-gradient(90deg, #7C3AED, #4F46E5)", transition: "width 0.3s ease" },
      challengeContainer:  { display: "flex", flexDirection: "column", gap: "16px" },
      videoWrapper:        { position: "relative", borderRadius: "16px", overflow: "hidden", background: "#000", aspectRatio: "9/16", maxHeight: "50vh" },
      video:               { width: "100%", height: "100%", objectFit: "cover" },
      videoOverlay:        { position: "absolute", top: "12px", left: "12px", right: "12px" },
      challengeStep:       { background: "rgba(0,0,0,0.6)", color: "#fff", padding: "6px 12px", borderRadius: "20px", fontSize: "12px", display: "inline-block" },
      challengeCard:       { background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "16px", padding: "20px", display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", textAlign: "center" },
      challengeIcon:       { fontSize: "40px" },
      challengeInstruction:{ fontSize: "17px", color: "rgba(255,255,255,0.9)", lineHeight: 1.5, margin: 0 },
      qualityWarning:      { background: "rgba(251,191,36,0.15)", border: "1px solid rgba(251,191,36,0.3)", borderRadius: "8px", padding: "8px 12px", fontSize: "13px", color: "#FCD34D" },
      footer:              { padding: "16px", textAlign: "center" },
      footerText:          { fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 },
    };
''')

print("=== Frontend capture UI written ===")
print("=== ALL PLATFORM FILES WRITTEN ===")