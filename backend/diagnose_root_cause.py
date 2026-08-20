import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from database import CodebaseDB
from groq_service import GroqEngine

db = CodebaseDB()
groq = GroqEngine()

print("--- 1. TOPOLOGY CHECK ---")
topology = db.get_topology()
for t in topology:
    print(f"Subsystem: {t['module_path']} | Symbols: {t['symbol_count']} | Key Symbols: {t['key_symbols'][:4]}")
    if "eval" in t['module_path'].lower() or "judge" in t['module_path'].lower() or "seed" in t['module_path'].lower():
        print(f"   Summary: {t['summary']}")

print("\n--- 2. ROUTER SCORE FOR 'I have a list of LLM as a judge metric' ---")
query = "I have a list of LLM as a judge metric"
focused = groq._route_to_subsystems_fast(query, topology)
print(f"Focused Subsystems for query '{query}': {focused}")

print("\n--- 3. BM25 / FTS SEARCH FOR 'LLM as a judge metric' ---")
heuristic = groq._extract_heuristic_keywords(query)
print("Heuristic terms:", heuristic)
for term in [query] + heuristic:
    matches = db.search_symbols(term, limit=4)
    print(f"Term '{term}' -> {len(matches)} matches:")
    for m in matches:
        print(f"   - {m['name']} ({m['symbol_type']}) at {m['relative_path']}:{m['start_line']}")
