import os
import sys
import httpx
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

test_models = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemma-4-31b-it",
    "gemini-2.5-pro"
]

prompt = "Return valid JSON: {\"status\": \"ok\"}"

for m in test_models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json", "maxOutputTokens": 100}
    }
    try:
        r = httpx.post(url, json=payload, timeout=8.0)
        print(f"[{m}] Status: {r.status_code}")
        if r.status_code == 200:
            print("  -> Response:", r.json()["candidates"][0]["content"]["parts"][0]["text"].strip())
        else:
            print("  -> Error:", r.text[:150])
    except Exception as e:
        print(f"[{m}] Exception: {e}")
