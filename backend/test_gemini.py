import sys
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "AQ.Ab8RN6K6NrKskdzJyl79ddKHpi1kVC8mMgtYxhi0KyE-nHp7wg"

candidates = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash"
]

for model in candidates:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, return JSON: {\"model\": \"" + model + "\", \"status\": \"online\"}"}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    try:
        r = httpx.post(url, json=payload, timeout=15.0)
        print(f"[{model}] Status: {r.status_code}")
        if r.status_code == 200:
            print(" -> Response:", r.json()["candidates"][0]["content"]["parts"][0]["text"])
            break
        else:
            print(" -> Error:", r.text[:150])
    except Exception as e:
        print(f"[{model}] Exception: {e}")
