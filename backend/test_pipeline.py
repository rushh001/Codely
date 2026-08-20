import os
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from database import CodebaseDB
from groq_service import GroqEngine

db = CodebaseDB()
groq = GroqEngine()

test_queries = [
    "I have a list of LLM as a judge metric",
    "I want to tell you about what are the LLM as a judge metric that I used for evaluations"
]

for q in test_queries:
    print("\n" + "="*80, flush=True)
    print(f"🗣️  [Spoken Input]: \"{q}\"", flush=True)
    t0 = time.time()
    res = groq.process_query_and_retrieve(q, db)
    elapsed = (time.time() - t0) * 1000
    
    sym = res.get("best_symbol")
    bd = res["latency_breakdown"]
    print(f"⚡ [Latency]: {elapsed:.1f}ms (Router: {bd.get('router_ms', 0)}ms | DB: {bd.get('db_ms', 0)}ms | Reasoner: {bd.get('reason_ms', 0)}ms)", flush=True)
    print(f"📍 [Focused Subsystem]: {res.get('focused_modules')}", flush=True)
    print(f"🤖 [Active Model]: {res.get('active_model')}", flush=True)
    print(f"🎯 [Intent]: {res.get('intent_summary')}", flush=True)
    if sym:
        print(f"📌 [Selected AST Symbol]: {sym['name']} ({sym['symbol_type']}) at {sym['relative_path']}:{sym['start_line']}", flush=True)
        print(f"   Signature: {sym['signature']}", flush=True)
    print(f"📝 [HUD Bullets]:", flush=True)
    for b in res.get('bullets', []):
        print(f"   • {b}", flush=True)
