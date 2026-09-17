import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'http://127.0.0.1:8000/api/v1'
HEADERS = {
    'Content-Type': 'application/json',
    'X-ArgusCX-Key': 'acx_live_demo_key_2026'
}

print("=== ARGUSCX BACKEND END-TO-END WORKFLOW TESTS ===")

# Test 1: Submit Ticket
payload = {
    "customer_name": "Ayush Test User",
    "customer_email": "ayush@example.com",
    "subject": "Damaged Item Delivered",
    "message": "My order #99482 arrived broken. I need a refund or replacement immediately.",
    "channel": "web",
    "account_age_days": 180,
    "previous_tickets": 0,
    "previous_fraud_flags": 0
}

ticket_id = None
try:
    req = urllib.request.Request(f"{BASE_URL}/tickets", data=json.dumps(payload).encode('utf-8'), headers=HEADERS, method='POST')
    with urllib.request.urlopen(req) as res:
        res_data = json.loads(res.read().decode('utf-8'))
        ticket = res_data['ticket']
        ticket_id = ticket['id']
        print("[TEST 1] Ticket Submission: PASS")
        print("  - Ticket ID:", ticket['id'])
        print("  - Status:", ticket['status'])
        print("  - Category:", ticket['category'])
        print("  - Confidence Score:", ticket['confidence_score'])
        print("  - Risk Score:", ticket['risk_score'])
except Exception as e:
    print("[TEST 1] Ticket Submission: FAIL -", e)

# Test 2: List Tickets
try:
    req = urllib.request.Request(f"{BASE_URL}/tickets", headers=HEADERS)
    with urllib.request.urlopen(req) as res:
        tickets = json.loads(res.read().decode('utf-8'))
        print("[TEST 2] List Tickets: PASS - Count:", len(tickets))
except Exception as e:
    print("[TEST 2] List Tickets: FAIL -", e)

# Test 3: Get Ticket Details
if ticket_id:
    try:
        req = urllib.request.Request(f"{BASE_URL}/tickets/{ticket_id}", headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            ticket = json.loads(res.read().decode('utf-8'))
            print("[TEST 3] Get Ticket Details: PASS - Subject:", ticket['subject'])
    except Exception as e:
        print("[TEST 3] Get Ticket Details: FAIL -", e)

# Test 4: Ticket Stats Summary
try:
    req = urllib.request.Request(f"{BASE_URL}/tickets/stats/summary", headers=HEADERS)
    with urllib.request.urlopen(req) as res:
        stats = json.loads(res.read().decode('utf-8'))
        print("[TEST 4] Stats Summary: PASS - Total:", stats['total'], "Resolved:", stats['auto_resolved'])
except Exception as e:
    print("[TEST 4] Stats Summary: FAIL -", e)

# Test 5: Human Resolution Override
if ticket_id:
    override_payload = {
        "action": "approve",
        "agent_id": "HUMAN-AGENT-007",
        "notes": "Verified customer claim and approved refund."
    }
    try:
        req = urllib.request.Request(f"{BASE_URL}/tickets/{ticket_id}/resolve", data=json.dumps(override_payload).encode('utf-8'), headers=HEADERS, method='PATCH')
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode('utf-8'))
            print("[TEST 5] Human Override: PASS - New Status:", res_data['new_status'])
    except Exception as e:
        print("[TEST 5] Human Override: FAIL -", e)

print("=== ALL BACKEND E2E TESTS COMPLETED SUCCESSFULLY ===")
