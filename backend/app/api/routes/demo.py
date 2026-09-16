import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter
from app.api.routes.sessions import _cases, _sessions

router = APIRouter(prefix="/demo")

def make_session_and_case(
    scenario_id, title, claim, state, routing, 
    risk_score, signals, reasoning, evidence_ids
):
    session_id = f"ses_demo_{scenario_id}"
    case_id = f"cas_{scenario_id}"
    
    # Generate session
    _sessions[session_id] = {
        "id": session_id,
        "order_id": f"ORD-DEMO-{scenario_id}",
        "customer_ref": f"CUST-{scenario_id}",
        "category": "Electronics",
        "expected_serial": f"SN-{scenario_id}XXXX",
        "claim_text": claim,
        "return_reason": "Damaged",
        "status": "completed",
        "assurance_level": "live_video",
        "challenge_sequence": [{"step": 1}],
        "challenges_completed": 1,
        "evidence_ids": evidence_ids,
        "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Generate case
    _cases[session_id] = {
        "id": case_id,
        "session_id": session_id,
        "state": state,
        "routing": routing,
        "risk_score": risk_score,
        "signals": signals,
        "reasoning_narrative": reasoning,
        "reviewed_at": None,
        "created_at": datetime.utcnow().isoformat()
    }

@router.post("/seed")
async def seed_data():
    """Seed the 10 demo scenarios into memory."""
    _cases.clear()
    _sessions.clear()

    # 1. The Perfect Return
    make_session_and_case(
        "01_PERFECT", "The Perfect Return", 
        "Device arrived scratched on the back.", 
        "VERIFIED", "AUTO_APPROVED", 0.05,
        {"YOLOv8": {"confidence": 0.95, "findings": "Scratches detected. Structural integrity 100%."}, "ELA": {"confidence": 0.99, "findings": "No manipulation."}},
        "Evidence aligns perfectly with the claim. No anomalies detected.",
        ["demo_img_1"]
    )

    # 2. Blatant Photoshop
    make_session_and_case(
        "02_PHOTOSHOP", "Image Manipulation", 
        "The screen is cracked.", 
        "SUSPICIOUS", "AUTO_REJECTED", 0.92,
        {"ELA": {"confidence": 0.98, "findings": "High pixel variance anomaly detected along the 'crack' line. JPEG resave artifacts present."}, "YOLOv8": {"confidence": 0.4, "findings": "Irregular depth mask."}},
        "Error Level Analysis strongly indicates the crack was digitally added post-capture.",
        ["demo_img_2"]
    )

    # 3. Monitor Spoof
    make_session_and_case(
        "03_SPOOF", "Screen Replay", 
        "Phone won't turn on.", 
        "SUSPICIOUS", "AUTO_REJECTED", 0.88,
        {"MoireDetector": {"confidence": 0.96, "findings": "FFT analysis found high-frequency grid patterns matching an LCD/OLED monitor."}, "DepthNet": {"confidence": 0.8, "findings": "Flat planar geometry detected."}},
        "Evidence appears to be a photograph of a computer screen displaying a broken device, not a live capture.",
        ["demo_img_3"]
    )

    # 4. IMEI Mismatch
    make_session_and_case(
        "04_IMEI", "Product Identity", 
        "Sending back the broken tablet.", 
        "REVIEW_REQUIRED", "HUMAN_REVIEW", 0.65,
        {"EasyOCR": {"confidence": 0.92, "findings": "Extracted IMEI: 359483749. Expected: 994837211."}},
        "The device in the photo is broken, but the IMEI extracted via OCR does not match the purchased serial number.",
        ["demo_img_4"]
    )

    # 5. Serial Returner
    make_session_and_case(
        "05_DUPLICATE", "Serial Returner", 
        "Box arrived completely crushed.", 
        "SUSPICIOUS", "AUTO_REJECTED", 0.99,
        {"pHash": {"confidence": 1.0, "findings": "Image hash collision with claim CAS_88321 from 4 months ago."}},
        "This exact image was used in a previous refund claim by a different account.",
        ["demo_img_5"]
    )

    # 6. LLM Contradiction
    make_session_and_case(
        "06_LLM", "Reasoning Contradiction", 
        "The screen is shattered into a million pieces.", 
        "REVIEW_REQUIRED", "HUMAN_REVIEW", 0.75,
        {"YOLOv8": {"confidence": 0.9, "findings": "Minor bezel scratch. Screen glass is intact."}},
        "The customer claims the screen is shattered, but computer vision models confirm the screen glass is fully intact.",
        ["demo_img_6"]
    )

    # 7. YOLOv8 Confirmed
    make_session_and_case(
        "07_YOLO", "Valid Severe Damage", 
        "Battery is swollen and blew off the back glass.", 
        "VERIFIED", "AUTO_APPROVED", 0.1,
        {"YOLOv8": {"confidence": 0.97, "findings": "Battery swelling detected. Back glass detached."}},
        "Visual evidence strongly corroborates the severe damage claim. No spoofing detected.",
        ["demo_img_7"]
    )

    # 8. Missing EXIF
    make_session_and_case(
        "08_EXIF", "Missing Metadata", 
        "Dead pixels on delivery.", 
        "REVIEW_REQUIRED", "HUMAN_REVIEW", 0.55,
        {"Metadata": {"confidence": 0.8, "findings": "EXIF data completely stripped. C2PA credentials absent."}},
        "The image metadata has been scrubbed, which is anomalous for a live camera capture. Review required.",
        ["demo_img_8"]
    )

    # 9. Lighting Trick
    make_session_and_case(
        "09_GLARE", "Glare Masking", 
        "Camera lens is broken.", 
        "REVIEW_REQUIRED", "HUMAN_REVIEW", 0.5,
        {"ImageQuality": {"confidence": 0.9, "findings": "Severe overexposure/glare obscuring the target area."}},
        "The image is too overexposed for the vision models to confidently assess the damage.",
        ["demo_img_9"]
    )

    # 10. Challenge Failure
    make_session_and_case(
        "10_CHALLENGE", "Sequence Mismatch", 
        "Here is the photo.", 
        "SUSPICIOUS", "AUTO_REJECTED", 0.85,
        {"ChallengeValidator": {"confidence": 0.99, "findings": "Nonce 8F32 mismatch. Expected 'tilt left', received static frontal."}},
        "The user failed the cryptographic challenge-response sequence, indicating possible pre-recorded video injection.",
        ["demo_img_10"]
    )

    return {"message": "10 Demo scenarios successfully seeded into memory.", "count": len(_cases)}
