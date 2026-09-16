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
    digits = re.sub(r"\D", "", s)
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
    candidates.extend(re.findall(r"\b\d{15}\b", text))
    # S/N pattern: alphanumeric 8-20 chars after S/N or SN or Serial
    candidates.extend(re.findall(r"(?:S/?N|Serial|SN)[:\s]*([A-Z0-9]{8,20})", text, re.IGNORECASE))
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
