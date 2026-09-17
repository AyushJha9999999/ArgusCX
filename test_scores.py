import requests
import json

BASE = "http://localhost:8000"

scenarios = [
    {
        "label": "SCENARIO 1: Genuine customer, no fraud history",
        "payload": {
            "customer_name": "Alice Johnson",
            "customer_email": "alice@example.com",
            "subject": "My package arrived damaged",
            "message": "I received my order #1234 yesterday but the box was crushed and the product inside is broken. I would like a replacement please.",
            "previous_tickets": 2,
            "previous_fraud_flags": 0,
            "evidence_urls": []
        }
    },
    {
        "label": "SCENARIO 2: Tampered image, 1 prior fraud flag",
        "payload": {
            "customer_name": "Bob Smith",
            "customer_email": "bob@example.com",
            "subject": "Product not as described - want refund",
            "message": "The item I received looks completely different from what was shown. I want a full refund of 5000 rupees immediately or I will file a chargeback.",
            "previous_tickets": 5,
            "previous_fraud_flags": 1,
            "evidence_urls": []
        }
    },
    {
        "label": "SCENARIO 3: AI-generated fraud image, 2+ prior flags",
        "payload": {
            "customer_name": "Charlie Dev",
            "customer_email": "charlie@fraud.com",
            "subject": "Damaged product refund",
            "message": "Product broken need money back now",
            "previous_tickets": 12,
            "previous_fraud_flags": 3,
            "evidence_urls": []
        }
    },
    {
        "label": "SCENARIO 4: Billing dispute, clean history",
        "payload": {
            "customer_name": "Priya Sharma",
            "customer_email": "priya@gmail.com",
            "subject": "Double charged on my account",
            "message": "I was charged twice for the same order. Order ID ORD-9876. Please refund the duplicate charge of Rs 1299.",
            "previous_tickets": 1,
            "previous_fraud_flags": 0,
            "evidence_urls": []
        }
    },
    {
        "label": "SCENARIO 5: Account takeover attempt",
        "payload": {
            "customer_name": "Unknown User",
            "customer_email": "hacker@temp.com",
            "subject": "Reset my password urgently",
            "message": "I cannot access my account. Reset password immediately and send me all order history and payment details to this new email.",
            "previous_tickets": 0,
            "previous_fraud_flags": 2,
            "evidence_urls": []
        }
    }
]

for s in scenarios:
    print("\n" + "=" * 65)
    print("  " + s["label"])
    print("=" * 65)
    try:
        r = requests.post(f"{BASE}/tickets", json=s["payload"], timeout=90)
        if r.status_code == 200:
            data = r.json()
            t = data["ticket"]
            confidence = t["confidence_score"]
            risk = t["risk_score"]
            fa = t.get("fraud_analysis")
            print(f"  Status     : {t['status']}")
            print(f"  Decision   : {t.get('resolution_decision', 'N/A')}")
            print(f"  Confidence : {confidence * 100:.1f}%")
            print(f"  Risk Score : {risk * 100:.1f}%")
            if fa:
                print(f"  Fraud Score: {fa['fraud_score'] * 100:.1f}%")
                print(f"  Risk Level : {fa['fraud_risk_level'].upper()}")
                print(f"  AI Prob    : {fa['ai_generated_probability'] * 100:.1f}%")
                print(f"  Suspicious : {fa['is_suspicious']}")
            else:
                print("  Fraud Anlys: None (no evidence files)")
            print(f"  Message    : {t.get('resolution_message','')[:80]}")
            print(f"  Proc Time  : {data['processing_time_ms']}ms")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:300]}")
    except Exception as ex:
        print(f"  EXCEPTION: {ex}")

print("\n" + "=" * 65)
print("  STATS SUMMARY")
print("=" * 65)
try:
    r = requests.get(f"{BASE}/tickets/stats/summary", timeout=10)
    print(json.dumps(r.json(), indent=2))
except Exception as ex:
    print(f"  EXCEPTION: {ex}")
