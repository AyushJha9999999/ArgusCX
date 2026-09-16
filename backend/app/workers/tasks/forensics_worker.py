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
