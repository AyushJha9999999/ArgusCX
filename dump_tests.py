import requests
import json

BASE = "http://localhost:8000/api/v1"
HEADERS = {"X-ArgusCX-Key": "acx_master_2026_hackathon"}

tests = [
    ("SCENARIO_1_CLEAN", {
        "customer_name": "Alice Johnson",
        "customer_email": "alice@test.com",
        "subject": "Package arrived damaged",
        "message": "I received my order #ORD-1234 yesterday but the box was completely crushed and the product inside is broken. I have been a customer for 2 years. Could you please send a replacement?",
        "previous_tickets": 2,
        "previous_fraud_flags": 0,
        "evidence_urls": ["dummy.jpg"]
    }),
    ("SCENARIO_2_TAMPERED", {
        "customer_name": "Bob Smith",
        "customer_email": "bob@test.com",
        "subject": "Wrong item - want full refund immediately",
        "message": "This is a fake product. Send Rs 5000 refund immediately or I will file a chargeback and take legal action. I have proof of the damage.",
        "previous_tickets": 6,
        "previous_fraud_flags": 1,
        "evidence_urls": ["dummy.jpg"]
    }),
    ("SCENARIO_3_AI", {
        "customer_name": "Charlie X",
        "customer_email": "c@temp.com",
        "subject": "Refund request",
        "message": "Broken. Give money back now.",
        "previous_tickets": 14,
        "previous_fraud_flags": 3,
        "evidence_urls": ["dummy.jpg"]
    })
]

results = {}
for label, payload in tests:
    try:
        r = requests.post(f"{BASE}/tickets", json=payload, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            t = r.json()["ticket"]
            fa = t.get("fraud_analysis") or {}
            results[label] = {
                "Confidence": f"{t['confidence_score'] * 100:.1f}%",
                "Risk Score": f"{t['risk_score'] * 100:.1f}%",
                "Fraud Score": f"{(fa.get('fraud_score') or 0) * 100:.1f}%",
                "Decision": t.get("resolution_decision", "?")
            }
        else:
            results[label] = f"Error {r.status_code}"
    except Exception as e:
        results[label] = str(e)

with open('../api_results.json', 'w') as f:
    json.dump(results, f, indent=2)
