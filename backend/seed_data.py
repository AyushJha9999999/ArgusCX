import requests

API_URL = "http://localhost:8000/api/v1/demo/seed"
KEY = "acx_master_2026_hackathon"

print(f"Seeding 10 demo scenarios via {API_URL}...")
response = requests.post(API_URL, headers={"X-ArgusCX-Key": KEY})

if response.status_code == 200:
    print("Success:", response.json())
else:
    print(f"Error {response.status_code}: {response.text}")
