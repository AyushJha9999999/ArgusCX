import uvicorn
from fastapi import FastAPI, Request
import hmac
import hashlib
import json
import structlog

# This script simulates a merchant's backend (like Shopify or Zendesk)
# receiving the verdict from ArgusCX.

app = FastAPI(title="Merchant Webhook Receiver")
logger = structlog.get_logger(__name__)

WEBHOOK_SECRET = b"demo_webhook_secret_key"

@app.post("/webhook/arguscx")
async def receive_webhook(request: Request):
    signature = request.headers.get("x-arguscx-signature", "")
    body = await request.body()
    
    # Verify cryptographic signature
    expected_mac = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_mac, signature):
        logger.warning("Webhook received with INVALID signature! Rejecting.")
        return {"status": "error", "message": "Invalid signature"}

    payload = json.loads(body)
    
    event_type = payload.get("event")
    data = payload.get("data", {})
    case_id = data.get("case_id")
    state = data.get("state")
    
    if state == "VERIFIED":
        logger.info(f"✅ [Shopify Integration] Case {case_id} VERIFIED. Triggering automatic refund.")
    elif state == "REJECTED":
        logger.info(f"🚨 [Shopify Integration] Case {case_id} REJECTED due to fraud. Locking customer account.")
    else:
        logger.info(f"⚖️ [Zendesk Integration] Case {case_id} requires human review. Creating Zendesk ticket.")

    return {"status": "success", "message": "Webhook processed successfully"}

if __name__ == "__main__":
    print("======================================================")
    print("🚀 Merchant Webhook Receiver running on port 8080")
    print("======================================================")
    uvicorn.run(app, host="0.0.0.0", port=8080)
