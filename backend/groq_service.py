import os
import io
import time
import json
import re
from typing import Dict, Any, List, Optional
import httpx
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash"]

FAST_ANALYZER_MODEL = "openai/gpt-oss-120b"
PRIMARY_REASONER_MODEL = "openai/gpt-oss-120b"
FALLBACK_REASONER_MODELS = ["qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
PRIMARY_STT_MODEL = "whisper-large-v3"

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "you", "your", "he", "she",
    "it", "they", "them", "what", "which", "who", "whom", "this", "that", "these",
    "those", "am", "is", "are", "was", "were", "be", "being", "have", "has",
    "had", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
    "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "s", "t", "can", "will", "just", "don", "should", "now", "talking", "discussing",
    "speaking", "codebase", "thing", "like", "know", "mean", "tell", "show", "our",
    "backend", "frontend", "project", "code", "file", "files", "various", "different",
    "that", "is", "are", "want", "list", "being", "used", "use", "using", "work",
    "worked", "working", "basically", "also", "her", "him", "his", "has", "it"
}

STT_REPLACEMENTS = [
    (r'\blln\b', 'llm'),
    (r'\bguard\s+rails\b', 'guardrails'),
    (r'\bguard\s+rail\b', 'guardrail'),
    (r'\bred\s+teaming\b', 'redteam'),
    (r'\bred\s+team\b', 'redteam'),
    (r'\bevals\b', 'evaluator'),
    (r'\beval\b', 'evaluator'),
]


def clean_and_normalize_speech(raw_speech: str) -> str:
    cleaned = raw_speech.strip()
    for pattern, repl in STT_REPLACEMENTS:
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned


def parse_llm_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Robust JSON parser for LLM completions.
    """
    if not raw_text:
        return None
    clean_text = re.sub(r'<think>[\s\S]*?</think>', '', raw_text).strip()
    clean_text = re.sub(r'```(?:json)?', '', clean_text).strip()
    try:
        return json.loads(clean_text)
    except Exception:
        pass
    
    match = re.search(r'\{[\s\S]*\}', clean_text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
        
        b1_match = re.search(r'"bullet1"\s*:\s*"(.*?)(?<!\\)"', clean_text, re.DOTALL)
        b2_match = re.search(r'"bullet2"\s*:\s*"(.*?)(?<!\\)"', clean_text, re.DOTALL)
        sym_match = re.search(r'"selected_symbol_id"\s*:\s*(\d+)', clean_text)
        res = {}
        if b1_match:
            res["bullet1"] = b1_match.group(1).replace('\\"', '"').replace('\\n', ' ').strip()
        if b2_match:
            res["bullet2"] = b2_match.group(1).replace('\\"', '"').replace('\\n', ' ').strip()
        if sym_match:
            res["selected_symbol_id"] = int(sym_match.group(1))
        if res:
            return res

    return None


class GroqEngine:
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv(override=True)
        raw_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.api_key = raw_key.strip() if raw_key else ""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        
        if self.api_key and len(self.api_key) > 10:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize Groq client: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return bool((self.client and self.api_key and len(self.api_key) > 10) or (self.gemini_api_key and len(self.gemini_api_key) > 10))

    def set_api_key(self, api_key: str):
        self.api_key = api_key.strip() if api_key else ""
        os.environ["GROQ_API_KEY"] = self.api_key
        if self.api_key and len(self.api_key) > 10:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Groq init error: {e}")
                self.client = None
        else:
            self.client = None

    def set_gemini_key(self, gemini_key: str):
        self.gemini_api_key = gemini_key.strip()
        os.environ["GEMINI_API_KEY"] = self.gemini_api_key

    def transcribe_audio_bytes(self, wav_bytes: bytes) -> Dict[str, Any]:
        if not self.client:
            return {"text": "", "error": "Groq API key not configured for Whisper STT", "latency_ms": 0}

        start_time = time.time()
        for model_name in [PRIMARY_STT_MODEL, "whisper-large-v3-turbo"]:
            try:
                audio_file = ("speech.wav", wav_bytes, "audio/wav")
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=model_name,
                    response_format="json",
                    language="en",
                    temperature=0.0
                )
                elapsed = (time.time() - start_time) * 1000
                raw_text = transcription.text.strip()
                norm_text = clean_and_normalize_speech(raw_text)
                return {
                    "text": norm_text,
                    "latency_ms": round(elapsed, 1),
                    "model": model_name,
                    "error": None
                }
            except Exception:
                continue

        elapsed = (time.time() - start_time) * 1000
        return {
            "text": "",
            "latency_ms": round(elapsed, 1),
            "error": "Transcription failed"
        }

    def _extract_heuristic_keywords(self, speech_text: str) -> List[str]:
        tokens = re.findall(r'[a-zA-Z0-9_]+', speech_text)
        meaningful = []
        for t in tokens:
            low = t.lower()
            if low not in STOP_WORDS and len(low) > 2:
                meaningful.append(low)
                if "_" in low:
                    meaningful.extend([part for part in low.split("_") if part not in STOP_WORDS and len(part) > 2])
        return list(dict.fromkeys(meaningful))

    def _route_to_subsystems_fast(self, speech_clean: str, topology: List[Dict[str, Any]]) -> List[str]:
        """
        Fast Macro Topology Router using token-exact scoring (<2ms).
        """
        speech_lower = speech_clean.lower()
        words = set(re.findall(r'[a-zA-Z0-9_]+', speech_lower)) - STOP_WORDS
        
        scored_modules = []
        for mod in topology:
            score = 0
            mod_path_tokens = set(re.findall(r'[a-z0-9_]+', mod["module_path"].lower()))
            summary_tokens = set(re.findall(r'[a-z0-9_]+', mod["summary"].lower()))
            key_sym_tokens = set()
            for s in mod.get("key_symbols", []):
                for part in re.findall(r'[a-z0-9_]+', s.lower()):
                    if part not in STOP_WORDS and len(part) > 2:
                        key_sym_tokens.add(part)

            for w in words:
                if len(w) < 3:
                    continue
                if w in mod_path_tokens:
                    score += 25
                if w in key_sym_tokens:
                    score += 15
                if w in summary_tokens:
                    score += 8

            if score > 0:
                scored_modules.append((score, mod["module_path"]))

        scored_modules.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in scored_modules[:4]]

    def _call_gemini_synthesis(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Ultra-fast Gemini Flash reasoning with 1M tokens/min and 1,500 req/day quota.
        """
        if not self.gemini_api_key or len(self.gemini_api_key) < 10:
            return None

        for model in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
            payload = {
                "system_instruction": {
                    "parts": [{"text": "You are a senior codebase architect AI. You only output valid JSON. No conversational preamble."}]
                },
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 2000
                }
            }
            try:
                r = httpx.post(url, json=payload, timeout=15.0)
                if r.status_code == 200:
                    data = r.json()
                    cand = data.get("candidates", [{}])[0]
                    raw_text = cand.get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed = parse_llm_json(raw_text)
                    if parsed and parsed.get("bullet1"):
                        parsed["_model_used"] = model
                        return parsed
                else:
                    print(f"[Gemini HTTP {r.status_code} on {model}]: {r.text[:200]}")
            except Exception as e:
                print(f"[Gemini Exception on {model}]: {e}")
                continue

        return None

    def process_query_and_retrieve(self, speech_text: str, db) -> Dict[str, Any]:
        """
        Hierarchical Progressive Zoom Context Engine:
        1. Sub-millisecond Subsystem Routing (<2ms).
        2. Deep Hybrid AST Retrieval: Focused Subsystems + Global FTS (<2ms).
        3. Full-Context Synthesis: Gemini Flash with 1M token budget (~350ms).
        """
        overall_start = time.time()
        speech_clean = clean_and_normalize_speech(speech_text)

        if not speech_clean:
            return {
                "intent": "empty",
                "bullets": ["Please speak a question or select a simulation prompt."],
                "best_symbol": None,
                "candidate_symbols": [],
                "speech_text": speech_text,
                "latency_breakdown": {"router_ms": 0, "db_ms": 0, "reason_ms": 0, "total_ms": 0}
            }

        # Step 1: Fast Subsystem Routing (<2ms)
        router_start = time.time()
        topology = db.get_topology()
        focused_modules = self._route_to_subsystems_fast(speech_clean, topology)
        router_time = (time.time() - router_start) * 1000

        # Step 2: Deep Hybrid AST Retrieval (Subsystem Partitions + Global FTS)
        db_start = time.time()
        candidate_symbols = []
        seen_ids = set()

        if focused_modules:
            module_matches = db.get_symbols_by_modules(focused_modules, limit=45)
            for m in module_matches:
                if m["id"] not in seen_ids:
                    seen_ids.add(m["id"])
                    candidate_symbols.append(m)

        heuristic_keywords = self._extract_heuristic_keywords(speech_clean)
        for term in [speech_clean] + heuristic_keywords[:8]:
            clean_term = term.replace("/", " ").replace("_", " ").replace("-", " ").strip()
            if not clean_term:
                continue
            fts_matches = db.search_symbols(clean_term, limit=12)
            for m in fts_matches:
                if m["id"] not in seen_ids:
                    seen_ids.add(m["id"])
                    candidate_symbols.append(m)

        db_time = (time.time() - db_start) * 1000

        # Step 3: Deep Context Synthesis & Direct Answer
        reason_start = time.time()
        bullets = []
        best_symbol = candidate_symbols[0] if candidate_symbols else None
        intent_summary = speech_clean
        active_model_name = "local-ast-fts"

        if candidate_symbols:
            symbols_summary = []
            for s in candidate_symbols[:45]:
                symbols_summary.append({
                    "id": s["id"],
                    "name": s["name"],
                    "type": s["symbol_type"],
                    "file": s["relative_path"],
                    "line": s["start_line"],
                    "signature": s["signature"],
                    "docstring": s["docstring"][:400] if s.get("docstring") else "",
                    "snippet_preview": s["code_snippet"][:750] if s.get("code_snippet") else ""
                })

            topo_preview = [{"path": t["module_path"], "summary": t["summary"]} for t in topology[:15]]

            synth_prompt = f"""You are Cluely Live Codebase Context Engine assisting a software engineer in a live technical meeting.

Spoken Query: "{speech_clean}"
Focused Subsystems: {focused_modules if focused_modules else 'Whole Repository'}
Codebase Subsystems Overview:
{json.dumps(topo_preview, indent=2)}

Retrieved Codebase Evidence (AST Symbols, Full Signatures, Docstrings & Code Snippets):
{json.dumps(symbols_summary, indent=2)}

Directives:
1. Answer the developer's question DIRECTLY and COMPREHENSIVELY using the code evidence:
   - When asked for a LIST/INVENTORY (e.g. guardrails, metrics, attacks, models, options):
     * "bullet1": DIRECTLY name and list ALL relevant items/classes/functions found in the code with markdown backticks and source paths.
     * "bullet2": Explain their execution/registration flow (citing the primary function/class with signature).
     * Set "selected_symbol_id" to the primary orchestrator, base class, or entry point.
   - When asked about a SPECIFIC function/endpoint:
     * "bullet1": State its exact location (file:line) and purpose.
     * "bullet2": Detail signature, parameters, return type, and operational logic.
     * Set "selected_symbol_id" to that exact symbol.

Return ONLY valid JSON:
{{
  "selected_symbol_id": <id number from retrieved list>,
  "intent_summary": "<1-sentence summary of developer's technical goal>",
  "bullet1": "<First high-density bullet directly answering query>",
  "bullet2": "<Second high-density bullet with technical implementation details>"
}}
"""
            # Provider 1: Google Gemini Flash (Expanded 1M token budget)
            gemini_res = self._call_gemini_synthesis(synth_prompt)
            if gemini_res and gemini_res.get("bullet1"):
                active_model_name = gemini_res.get("_model_used", "gemini-3.5-flash-lite")
                if gemini_res.get("intent_summary"):
                    intent_summary = gemini_res["intent_summary"]
                selected_id = gemini_res.get("selected_symbol_id")
                matched = next((s for s in candidate_symbols if s["id"] == selected_id), None)
                if matched:
                    best_symbol = matched
                bullets.append(gemini_res["bullet1"])
                if gemini_res.get("bullet2"):
                    bullets.append(gemini_res["bullet2"])

            # Provider 2: Groq Fallback Models
            elif self.client:
                models_to_try = [PRIMARY_REASONER_MODEL] + FALLBACK_REASONER_MODELS
                for model_name in models_to_try:
                    try:
                        synth_comp = self.client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": "You are a senior codebase architect AI. Always answer questions directly with concrete code elements. Respond ONLY with a valid JSON object."},
                                {"role": "user", "content": synth_prompt}
                            ],
                            model=model_name,
                            temperature=0.1,
                            max_tokens=600
                        )
                        final_res = parse_llm_json(synth_comp.choices[0].message.content)
                        if final_res and final_res.get("bullet1"):
                            active_model_name = model_name
                            if final_res.get("intent_summary"):
                                intent_summary = final_res["intent_summary"]
                            selected_id = final_res.get("selected_symbol_id")
                            matched = next((s for s in candidate_symbols if s["id"] == selected_id), None)
                            if matched:
                                best_symbol = matched

                            bullets.append(final_res["bullet1"])
                            if final_res.get("bullet2"):
                                bullets.append(final_res["bullet2"])
                            break
                    except Exception as e:
                        print(f"[Synthesis error on {model_name}]: {e}")
                        continue

        reason_time = (time.time() - reason_start) * 1000

        # Step 4: Fallback if no LLM bullets
        if not bullets:
            if best_symbol:
                bullets = [
                    f"**{best_symbol['name']}** ({best_symbol['symbol_type']}) at `{best_symbol['relative_path']}:{best_symbol['start_line']}`",
                    f"Signature: `{best_symbol['signature'] or 'N/A'}`"
                ]
            else:
                bullets = [
                    f"Referenced: \"{speech_clean}\"",
                    f"Scanned codebase but found no direct AST match."
                ]

        total_latency = (time.time() - overall_start) * 1000

        return {
            "speech_text": speech_clean,
            "intent_summary": intent_summary,
            "bullets": bullets,
            "best_symbol": best_symbol,
            "candidate_symbols": candidate_symbols[:8],
            "focused_modules": focused_modules,
            "active_model": active_model_name,
            "latency_breakdown": {
                "router_ms": round(router_time, 1),
                "db_ms": round(db_time, 1),
                "reason_ms": round(reason_time, 1),
                "total_ms": round(total_latency, 1)
            },
            "e2e_latency_ms": round(total_latency, 1)
        }
