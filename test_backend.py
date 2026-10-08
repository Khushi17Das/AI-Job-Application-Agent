import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

print(f"Testing FastAPI server at {BASE_URL}...")

try:
    # Test Stats endpoint
    req = urllib.request.Request(f"{BASE_URL}/api/applications/stats")
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
            print("✅ FastAPI Server is UP and Running!")
            print(f"📊 Current Stats: Total Apps = {data.get('total_applications')}")
        else:
            print(f"⚠️ Received status code: {response.status}")

except Exception as e:
    print(f"❌ Server not reachable. Make sure Uvicorn is running (`uvicorn app.main:app --reload`).")
    print(f"Details: {e}")
