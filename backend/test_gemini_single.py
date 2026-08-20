import os
import sys
import time
import httpx
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

prompt = """Answer the developer's question directly in JSON.
Question: What security guardrails exist?
Return valid JSON:
{
  "selected_symbol_id": 14,
  "intent_summary": "List security guardrails",
  "bullet1": "Guardrails include Vulnerability enum and run_guardrail_check.",
  "bullet2": "Evaluated via ValiqorEvaluator.evaluate."
}
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={API_KEY}"
payload = {
    "system_instruction": {
        "parts": [{"text": "You are a senior codebase architect AI. You only output valid JSON. No conversational preamble."}]
    },
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 0.1,
        "responseMimeType": "application/json",
        "maxOutputTokens": 1000
    }
}

t0 = time.time()
try:
    r = httpx.post(url, json=payload, timeout=15.0)
    elapsed = (time.time() - t0) * 1000
    print(f"Status: {r.status_code} in {elapsed:.1f}ms")
    if r.status_code == 200:
        data = r.json()
        cand = data["candidates"][0]
        print("Finish Reason:", cand.get("finishReason"))
        print("Response Text:", cand["content"]["parts"][0]["text"])
    else:
        print("Error:", r.text)
except Exception as e:
    print("Exception:", e)
