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

    # The configured evidence policy determines the final severity threshold.
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
