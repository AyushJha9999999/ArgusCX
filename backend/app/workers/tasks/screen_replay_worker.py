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
