import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

models = ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
for m in models:
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": "Return JSON: {\"test\": 1}"}],
            model=m,
            max_tokens=50
        )
        print(f"[OK] {m}: Success -> {res.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"[ERROR] {m}: Error -> {e}")
