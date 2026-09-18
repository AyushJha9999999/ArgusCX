import httpx
import time
import json
import uuid
import os

API_URL = os.environ.get("ARGUSCX_API_URL", "").rstrip("/")
API_KEY = os.environ.get("ARGUSCX_API_KEY", "")
HEADERS = {"Content-Type": "application/json", **({"X-ArgusCX-Key": API_KEY} if API_KEY else {})}

def run_test():
    print("=== ArgusCX Integration Test ===")
    if not API_URL or not API_KEY:
        raise RuntimeError("Set ARGUSCX_API_URL and ARGUSCX_API_KEY before running this integration test.")
    
    # 1. Create a verification session
    print("\n1. Creating verification session...")
    payload = {
        "order_id": f"ORD-{uuid.uuid4().hex[:6].upper()}",
        "customer_ref": "CUST-5555",
        "sku": "MACBOOK-M3-PRO",
        "category": "electronics",
        "expected_serial": "MBP-998877",
        "claim_text": "The screen has a huge crack down the middle and won't turn on.",
        "return_reason": "DAMAGED_IN_TRANSIT",
        "assurance_level": "live_video"
    }
    
    resp = httpx.post(f"{API_URL}/sessions", headers=HEADERS, json=payload)
    if resp.status_code != 201:
        print(f"Failed to create session: {resp.status_code}")
        print(resp.text)
        return
        
    data = resp.json()
    session_id = data["session_id"]
    print(f"Session Created: {session_id}")
    print(f"   Nonce: {data.get('session_nonce')}")
    print(f"   Challenges: {[c['challenge_type'] for c in data.get('challenges', [])]}")
    
    # 2. Get the session status
    print(f"\n2. Fetching session status for {session_id}...")
    resp = httpx.get(f"{API_URL}/sessions/{session_id}", headers=HEADERS)
    print(f"Status Code: {resp.status_code}")
    print(f"   State: {resp.json().get('status')}")
    
    # 3. Complete the session (Simulate user submitting all evidence)
    print("\n3. Completing session (Triggering Risk Engine)...")
    resp = httpx.post(f"{API_URL}/sessions/{session_id}/complete", headers=HEADERS)
    print(f"Status Code: {resp.status_code}")
    print(f"   Message: {resp.json().get('message')}")
    
    # 4. Wait for Celery/Risk Engine to process the case
    print("\n4. Polling for final result...")
    for _ in range(5):
        time.sleep(2)
        resp = httpx.get(f"{API_URL}/sessions/{session_id}/result", headers=HEADERS)
        if resp.status_code == 200:
            result = resp.json()
            print("\nFinal Case Result:")
            print(json.dumps(result, indent=2))
            break
        else:
            print(f"   Waiting... ({resp.status_code})")

if __name__ == "__main__":
    run_test()
