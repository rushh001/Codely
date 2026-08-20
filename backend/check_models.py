import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
models = [m.id for m in client.models.list().data if "whisper" not in m.id]
print("Active Groq models for routing & synthesis:")
for m in sorted(models):
    print(" -", m)
