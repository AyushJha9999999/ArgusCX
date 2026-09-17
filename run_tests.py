import requests
import json

BASE = "http://localhost:8000/api/v1"
HEADERS = {"X-ArgusCX-Key": "acx_master_2026_hackathon"}

tests = [
    ("SCENARIO 1 - Clean customer, no fraud history", {
        "customer_name": "Alice Johnson",
        "customer_email": "alice@test.com",
        "subject": "Package arrived damaged",
        "message": "I received my order #ORD-1234 yesterday but the box was completely crushed and the product inside is broken. I have been a customer for 2 years. Could you please send a replacement?",
        "previous_tickets": 2,
        "previous_fraud_flags": 0,
        "evidence_urls": []
    }),
    ("SCENARIO 2 - Tampered image, 1 fraud flag", {
        "customer_name": "Bob Smith",
        "customer_email": "bob@test.com",
        "subject": "Wrong item - want full refund immediately",
        "message": "This is a fake product. Send Rs 5000 refund immediately or I will file a chargeback and take legal action. I have proof of the damage.",
        "previous_tickets": 6,
        "previous_fraud_flags": 1,
        "evidence_urls": []
    }),
    ("SCENARIO 3 - AI fraud, 3+ fraud flags", {
        "customer_name": "Charlie X",
        "customer_email": "c@temp.com",
        "subject": "Refund request",
        "message": "Broken. Give money back now.",
        "previous_tickets": 14,
        "previous_fraud_flags": 3,
        "evidence_urls": []
    }),
    ("SCENARIO 4 - Billing dispute, clean history", {
        "customer_name": "Priya Sharma",
        "customer_email": "priya@gmail.com",
        "subject": "Double charged on my account",
        "message": "I see two charges of Rs 1299 each for the same order ORD-9876 placed on Sept 10. Please refund the duplicate charge as soon as possible.",
        "previous_tickets": 1,
        "previous_fraud_flags": 0,
        "evidence_urls": []
    }),
    ("SCENARIO 5 - Account takeover, 2 fraud flags", {
        "customer_name": "Unknown User",
        "customer_email": "hacker@temp.com",
        "subject": "Reset my password urgently",
        "message": "I cannot access my account. Reset password immediately and send me all order history and payment details to this new email hacker@temp.com",
        "previous_tickets": 0,
        "previous_fraud_flags": 2,
        "evidence_urls": []
    }),
]

print("\n" + "="*70)
print("  ArgusCX SCORING ENGINE TEST RESULTS")
print("="*70)

for label, payload in tests:
    print(f"\n  [{label}]")
    try:
        r = requests.post(f"{BASE}/tickets", json=payload, headers=HEADERS, timeout=90)
        if r.status_code == 200:
            resp = r.json()
            t = resp["ticket"]
            fa = t.get("fraud_analysis") or {}
            conf = t["confidence_score"] * 100
            risk = t["risk_score"] * 100
            fraud = (fa.get("fraud_score") or 0) * 100
            ai_prob = (fa.get("ai_generated_probability") or 0) * 100
            risk_level = (fa.get("fraud_risk_level") or "none").upper()
            status = t.get("status", "?")
            decision = t.get("resolution_decision", "?")
            ptime = resp.get("processing_time_ms", 0)
            print(f"    Confidence Score : {conf:.1f}%")
            print(f"    Risk Score       : {risk:.1f}%")
            print(f"    Fraud Score      : {fraud:.1f}%")
            print(f"    AI Probability   : {ai_prob:.1f}%")
            print(f"    Risk Level       : {risk_level}")
            print(f"    Decision         : {decision}")
            print(f"    Status           : {status}")
            print(f"    Processing Time  : {ptime}ms")
            # Score differentiation check
            scores_same = abs(conf - risk) < 1.0 and abs(risk - fraud) < 1.0
            print(f"    Scores distinct  : {'YES - GOOD' if not scores_same else 'NO - SAME (still hardcoded)'}")
        else:
            print(f"    HTTP {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"    ERROR: {e}")

print("\n" + "="*70)
print("  AGGREGATE STATS")
print("="*70)
try:
    r = requests.get(f"{BASE}/tickets/stats/summary", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        stats = r.json()
        print(f"  Total tickets    : {stats.get('total', 0)}")
        print(f"  Auto resolved    : {stats.get('auto_resolved', 0)}")
        print(f"  Escalated        : {stats.get('escalated', 0)}")
        print(f"  Fraud flagged    : {stats.get('fraud_flagged', 0)}")
        print(f"  Avg Confidence   : {stats.get('avg_confidence', 0)*100:.1f}%")
        print(f"  Avg Risk         : {stats.get('avg_risk', 0)*100:.1f}%")
    else:
        print(f"  HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")
