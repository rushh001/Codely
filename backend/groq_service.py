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

PROVIDER_CATALOG = {
    "gemini": {
        "id": "gemini",
        "name": "Google Gemini",
        "default_model": "gemini-3.5-flash",
        "key_env": "GEMINI_API_KEY",
        "models": [
            {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (Recommended)", "tag": "Live • Flagship 3.5"},
            {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite", "tag": "Live • Ultra-Low Latency"},
            {"id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash", "tag": "Live • High Precision"},
            {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash", "tag": "Live • Next-Gen"}
        ]
    },
    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "key_env": "OPENAI_API_KEY",
        "models": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Recommended)", "tag": "Fast & High Precision"},
            {"id": "gpt-4o", "name": "GPT-4o", "tag": "Flagship Intelligence"},
            {"id": "o3-mini", "name": "o3-mini", "tag": "Advanced Code Reasoning"},
            {"id": "o1-mini", "name": "o1-mini", "tag": "Reasoning Model"},
        ]
    },
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "default_model": "claude-3-5-haiku-latest",
        "key_env": "ANTHROPIC_API_KEY",
        "models": [
            {"id": "claude-3-5-haiku-latest", "name": "Claude 3.5 Haiku (Recommended)", "tag": "Sub-300ms Speed"},
            {"id": "claude-3-5-sonnet-latest", "name": "Claude 3.5 Sonnet", "tag": "Top Code Intelligence"},
            {"id": "claude-3-7-sonnet-latest", "name": "Claude 3.7 Sonnet", "tag": "Hybrid Reasoning"},
        ]
    }
}

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
    Robust JSON parser for LLM completions across all providers.
    Handles thinking tags, markdown code blocks, and partial strings.
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


def deduplicate_and_enrich_bullets(bullet1: str, bullet2: str, best_sym: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Guarantees that bullet1 and bullet2 are distinct, non-repetitive, and informative.
    If the LLM repeats bullet1 in bullet2, replaces bullet2 with concrete AST code facts.
    """
    b1 = (bullet1 or "").strip()
    b2 = (bullet2 or "").strip()

    if not b1 and not b2:
        return []
    if not b1:
        return [b2]
    if not b2:
        return [b1]

    is_repetitive = False
    if b1 == b2 or b1 in b2 or b2 in b1:
        is_repetitive = True
    else:
        words1 = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', b1.lower())) - STOP_WORDS
        words2 = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', b2.lower())) - STOP_WORDS
        if words1 and words2:
            overlap = len(words1 & words2)
            similarity = overlap / min(len(words1), len(words2))
            if similarity >= 0.60:
                is_repetitive = True

    if is_repetitive:
        if best_sym:
            if best_sym.get("docstring"):
                doc_first_line = best_sym["docstring"].strip().split("\n")[0].strip()
                b2 = f"**Implementation Detail**: `{best_sym.get('name')}` ({best_sym.get('symbol_type')}) — {doc_first_line} in `{best_sym.get('relative_path')}:{best_sym.get('start_line')}`"
            elif best_sym.get("signature"):
                b2 = f"**Signature & Entry Point**: `{best_sym.get('signature')}` in `{best_sym.get('relative_path')}:{best_sym.get('start_line')}`"
            else:
                return [b1]
        else:
            return [b1]

    return [b1, b2]


class GroqEngine:
    """
    Multi-Provider High-Performance AI Engine supporting:
    - Google Gemini (Gemini 2.5 Flash / Flash Lite)
    - OpenAI (GPT-4o, GPT-4o Mini, o3-mini)
    - Anthropic Claude (Claude 3.5 Haiku / Sonnet, 3.7 Sonnet)
    - Groq Cloud (Whisper Large-v3 STT + LPU open models)
    """
    def __init__(self, api_key: Optional[str] = None):
        from dotenv import dotenv_values
        from pathlib import Path
        env_file = Path(__file__).parent / ".env"
        project_env = dotenv_values(str(env_file)) if env_file.exists() else {}

        raw_key = api_key or project_env.get("GROQ_API_KEY", "")
        self.api_key = raw_key.strip() if raw_key else ""
        self.gemini_api_key = (project_env.get("GEMINI_API_KEY", "") or "").strip()
        self.openai_api_key = (project_env.get("OPENAI_API_KEY", "") or "").strip()
        self.anthropic_api_key = (project_env.get("ANTHROPIC_API_KEY", "") or "").strip()

        # Active provider & model (strictly Gemini, OpenAI, or Claude)
        self.active_provider = (project_env.get("ACTIVE_AI_PROVIDER", "") or "gemini").strip().lower()
        if self.active_provider not in PROVIDER_CATALOG:
            self.active_provider = "gemini"
        
        default_model = PROVIDER_CATALOG[self.active_provider]["default_model"]
        self.active_model = (project_env.get("ACTIVE_AI_MODEL", "") or default_model).strip()
        if not self.active_model:
            self.active_model = default_model

        self.client = None
        if self.api_key and len(self.api_key) > 10:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize Groq client: {e}")
                self.client = None

    def is_configured(self) -> bool:
        """Returns true if active reasoning provider has a valid key."""
        if self.active_provider == "openai":
            return bool(self.openai_api_key and len(self.openai_api_key) > 8)
        elif self.active_provider == "anthropic":
            return bool(self.anthropic_api_key and len(self.anthropic_api_key) > 8)
        else:
            return bool(self.gemini_api_key and len(self.gemini_api_key) > 8)

    def is_groq_configured(self) -> bool:
        """Returns true if Groq Whisper STT has a valid key."""
        return bool(self.api_key and len(self.api_key) > 8)

    def get_providers_state(self) -> Dict[str, Any]:
        """Returns the current state of supported AI reasoning engines and their models."""
        providers_info = []
        for p_id, p_info in PROVIDER_CATALOG.items():
            is_cfg = False
            if p_id == "gemini":
                is_cfg = bool(self.gemini_api_key and len(self.gemini_api_key) > 8)
            elif p_id == "openai":
                is_cfg = bool(self.openai_api_key and len(self.openai_api_key) > 8)
            elif p_id == "anthropic":
                is_cfg = bool(self.anthropic_api_key and len(self.anthropic_api_key) > 8)

            providers_info.append({
                "id": p_id,
                "name": p_info["name"],
                "default_model": p_info["default_model"],
                "configured": is_cfg,
                "models": p_info["models"]
            })

        return {
            "active_provider": self.active_provider,
            "active_model": self.active_model,
            "is_configured": self.is_configured(),
            "groq_configured": self.is_groq_configured(),
            "providers": providers_info
        }

    def set_provider_config(
        self,
        active_provider: Optional[str] = None,
        active_model: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None
    ):
        """Updates provider keys and active selection at runtime."""
        if groq_api_key is not None:
            self.set_api_key(groq_api_key)
        if gemini_api_key is not None:
            self.set_gemini_key(gemini_api_key)
        if openai_api_key is not None:
            self.set_openai_key(openai_api_key)
        if anthropic_api_key is not None:
            self.set_anthropic_key(anthropic_api_key)

        if active_provider and active_provider.lower() in PROVIDER_CATALOG:
            self.active_provider = active_provider.lower()
            os.environ["ACTIVE_AI_PROVIDER"] = self.active_provider

        if active_model:
            self.active_model = active_model.strip()
            os.environ["ACTIVE_AI_MODEL"] = self.active_model
        elif active_provider:
            self.active_model = PROVIDER_CATALOG[self.active_provider]["default_model"]
            os.environ["ACTIVE_AI_MODEL"] = self.active_model

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
        self.gemini_api_key = gemini_key.strip() if gemini_key else ""
        os.environ["GEMINI_API_KEY"] = self.gemini_api_key

    def set_openai_key(self, openai_key: str):
        self.openai_api_key = openai_key.strip() if openai_key else ""
        os.environ["OPENAI_API_KEY"] = self.openai_api_key

    def set_anthropic_key(self, anthropic_key: str):
        self.anthropic_api_key = anthropic_key.strip() if anthropic_key else ""
        os.environ["ANTHROPIC_API_KEY"] = self.anthropic_api_key

    def transcribe_audio_bytes(self, wav_bytes: bytes) -> Dict[str, Any]:
        """
        Transcribes audio buffer:
        1. Groq Whisper (Sub-200ms ultra-fast inference)
        2. OpenAI Whisper API (as fallback if Groq not available)
        """
        start_time = time.time()

        # Try Groq Whisper STT
        if self.client:
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
                        "model": f"groq/{model_name}",
                        "error": None
                    }
                except Exception:
                    continue

        # Fallback to OpenAI Whisper if OpenAI key is present
        if self.openai_api_key and len(self.openai_api_key) > 10:
            try:
                url = "https://api.openai.com/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {self.openai_api_key}"}
                files = {"file": ("speech.wav", io.BytesIO(wav_bytes), "audio/wav")}
                data = {"model": "whisper-1", "language": "en"}
                r = httpx.post(url, headers=headers, files=files, data=data, timeout=12.0)
                if r.status_code == 200:
                    elapsed = (time.time() - start_time) * 1000
                    raw_text = r.json().get("text", "").strip()
                    norm_text = clean_and_normalize_speech(raw_text)
                    return {
                        "text": norm_text,
                        "latency_ms": round(elapsed, 1),
                        "model": "openai/whisper-1",
                        "error": None
                    }
            except Exception as e:
                print(f"[OpenAI Whisper fallback error]: {e}")

        elapsed = (time.time() - start_time) * 1000
        return {
            "text": "",
            "latency_ms": round(elapsed, 1),
            "error": "Transcription failed. Please configure Groq or OpenAI API Key."
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

    def _call_gemini_synthesis(self, prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Google Gemini Flash reasoning with live models and automatic fallback."""
        if not self.gemini_api_key or len(self.gemini_api_key) < 8:
            return None

        live_gemini_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"]
        models_to_try = []
        if model and model in live_gemini_models:
            models_to_try.append(model)
        for m in live_gemini_models:
            if m not in models_to_try:
                models_to_try.append(m)

        for m in models_to_try:
            if not m:
                continue
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.gemini_api_key}"
            payload = {
                "system_instruction": {
                    "parts": [{"text": "You are a senior codebase architect AI. You only output valid JSON matching the requested schema. No conversational preamble."}]
                },
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 2000
                }
            }
            try:
                r = httpx.post(url, json=payload, timeout=16.0)
                if r.status_code == 200:
                    data = r.json()
                    cand = data.get("candidates", [{}])[0]
                    raw_text = cand.get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed = parse_llm_json(raw_text)
                    if parsed and parsed.get("bullet1"):
                        parsed["_model_used"] = f"gemini/{m}"
                        return parsed
                else:
                    print(f"[Gemini HTTP {r.status_code} on {m}]: {r.text[:200]}")
            except Exception as e:
                print(f"[Gemini Exception on {m}]: {e}")
                continue

        return None

    def _call_openai_synthesis(self, prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """OpenAI (GPT-4o, GPT-4o-mini, o3-mini) reasoning."""
        if not self.openai_api_key or len(self.openai_api_key) < 8:
            return None

        model_name = model or PROVIDER_CATALOG["openai"]["default_model"]
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a senior codebase architect AI. You only output valid JSON matching the requested schema. No conversational preamble."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        # Handling reasoning models (o1/o3-mini) which do not support custom temperature or system role in standard completions
        if model_name.startswith("o1") or model_name.startswith("o3"):
            payload["messages"] = [
                {"role": "user", "content": f"You are a senior codebase architect AI. You only output valid JSON. No preamble.\n\n{prompt}"}
            ]
        else:
            payload["temperature"] = 0.1

        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=20.0)
            if r.status_code == 200:
                data = r.json()
                raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = parse_llm_json(raw_text)
                if parsed and parsed.get("bullet1"):
                    parsed["_model_used"] = f"openai/{model_name}"
                    return parsed
            else:
                print(f"[OpenAI HTTP {r.status_code} on {model_name}]: {r.text[:200]}")
        except Exception as e:
            print(f"[OpenAI Exception on {model_name}]: {e}")

        return None

    def _call_anthropic_synthesis(self, prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Anthropic Claude (Claude 3.5 Haiku, Claude 3.5 Sonnet, Claude 3.7 Sonnet) reasoning."""
        if not self.anthropic_api_key or len(self.anthropic_api_key) < 8:
            return None

        model_name = model or PROVIDER_CATALOG["anthropic"]["default_model"]
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": model_name,
            "system": "You are a senior codebase architect AI. You only output valid JSON matching the requested schema. No conversational preamble.",
            "messages": [
                {"role": "user", "content": prompt + "\n\nCRITICAL: Respond ONLY with a valid JSON object matching the requested schema."}
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=20.0)
            if r.status_code == 200:
                data = r.json()
                content_blocks = data.get("content", [])
                raw_text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                parsed = parse_llm_json(raw_text)
                if parsed and parsed.get("bullet1"):
                    parsed["_model_used"] = f"anthropic/{model_name}"
                    return parsed
            else:
                print(f"[Anthropic HTTP {r.status_code} on {model_name}]: {r.text[:200]}")
        except Exception as e:
            print(f"[Anthropic Exception on {model_name}]: {e}")

        return None

    def _call_groq_synthesis(self, prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Groq LPU open source models reasoning."""
        if not self.client:
            return None

        models_to_try = [model] if model else ([PRIMARY_REASONER_MODEL] + FALLBACK_REASONER_MODELS)
        for model_name in models_to_try:
            if not model_name:
                continue
            try:
                synth_comp = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a senior codebase architect AI. Always answer questions directly with concrete code elements. Never repeat content between bullet1 and bullet2. Respond ONLY with a valid JSON object."},
                        {"role": "user", "content": prompt}
                    ],
                    model=model_name,
                    temperature=0.1,
                    max_tokens=600
                )
                final_res = parse_llm_json(synth_comp.choices[0].message.content)
                if final_res and final_res.get("bullet1"):
                    final_res["_model_used"] = f"groq/{model_name}"
                    return final_res
            except Exception as e:
                print(f"[Groq synthesis error on {model_name}]: {e}")
                continue

        return None

    def synthesize_ast_answer(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Synthesizes code context reasoning using the user-selected active provider and model,
        with automated multi-provider fallbacks if the primary engine encounters issues.
        """
        provider = self.active_provider
        model = self.active_model

        # 1. Primary Attempt: User-Selected Provider
        res = None
        if provider == "openai":
            res = self._call_openai_synthesis(prompt, model)
        elif provider == "anthropic":
            res = self._call_anthropic_synthesis(prompt, model)
        elif provider == "groq":
            res = self._call_groq_synthesis(prompt, model)
        else:
            res = self._call_gemini_synthesis(prompt, model)

        if res and res.get("bullet1"):
            return res

        # 2. Resilient Multi-Provider Fallbacks (if primary fails)
        fallback_order = ["gemini", "openai", "anthropic", "groq"]
        for fb_provider in fallback_order:
            if fb_provider == provider:
                continue
            fb_res = None
            if fb_provider == "gemini" and self.gemini_api_key:
                fb_res = self._call_gemini_synthesis(prompt)
            elif fb_provider == "openai" and self.openai_api_key:
                fb_res = self._call_openai_synthesis(prompt)
            elif fb_provider == "anthropic" and self.anthropic_api_key:
                fb_res = self._call_anthropic_synthesis(prompt)
            elif fb_provider == "groq" and self.client:
                fb_res = self._call_groq_synthesis(prompt)

            if fb_res and fb_res.get("bullet1"):
                return fb_res

        return None

    def process_query_and_retrieve(self, speech_text: str, db) -> Dict[str, Any]:
        """
        Hierarchical Progressive Zoom Context Engine:
        1. Sub-millisecond Subsystem Routing (<2ms).
        2. Deep Hybrid AST Retrieval: Focused Subsystems + Global FTS (<2ms).
        3. Multi-Provider Synthesis: Active Provider/Model (Gemini / OpenAI / Claude / Groq)
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
        active_model_name = f"{self.active_provider}/{self.active_model}"

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

DIRECTIVES:
1. "bullet1" (Exact Component Location & Purpose):
   - Format: "📍 **ComponentName** (`path/to/file.py:line`): [1-2 clear sentences stating what this component is and its core role in the codebase relating to the developer's question]."
   - Example: "📍 **EvaluationMode** (`app/evaluator/config.py:16`): Defines execution strategy options for evaluation metrics judging model responses."

2. "bullet2" (Technical Explanation & Mechanics):
   - Format: "💡 **How it works & Explanation**: [1-2 technical sentences explaining how this component functions, its key options/parameters/modes, internal logic, or execution flow, directly answering the query]."
   - Provide concrete technical details (e.g. `NON_INTRUSIVE`, `INTRUSIVE`, helper methods, or attributes) so the developer can immediately understand and talk about the architecture.
   - DO NOT repeat bullet1; provide the deep technical mechanics.

3. Select the best symbol:
   - Set "selected_symbol_id" to the id number of the primary component from the retrieved list.

Return ONLY valid JSON:
{{
  "selected_symbol_id": <id number from retrieved list>,
  "intent_summary": "<1-sentence summary of developer's technical goal>",
  "bullet1": "📍 **ComponentName** (`file:line`): Explanation of component role...",
  "bullet2": "💡 **How it works & Explanation**: Detailed mechanics of how it answers the query..."
}}
"""
            llm_res = self.synthesize_ast_answer(synth_prompt)
            if llm_res and llm_res.get("bullet1"):
                active_model_name = llm_res.get("_model_used", f"{self.active_provider}/{self.active_model}")
                if llm_res.get("intent_summary"):
                    intent_summary = llm_res["intent_summary"]
                selected_id = llm_res.get("selected_symbol_id")
                matched = next((s for s in candidate_symbols if s["id"] == selected_id), None)
                if matched:
                    best_symbol = matched
                bullets = deduplicate_and_enrich_bullets(llm_res.get("bullet1"), llm_res.get("bullet2"), best_symbol)

        reason_time = (time.time() - reason_start) * 1000

        # Step 4: Fallback if no LLM bullets
        if not bullets:
            if best_symbol:
                doc_summary = ""
                if best_symbol.get("docstring"):
                    doc_summary = best_symbol["docstring"].strip().split("\n")[0].strip()

                sym_name = best_symbol.get("name", "Component")
                sym_type = best_symbol.get("symbol_type", "component")
                rel_path = best_symbol.get("relative_path", "")
                start_l = best_symbol.get("start_line", 1)
                end_l = best_symbol.get("end_line", start_l)
                sig = best_symbol.get("signature") or sym_name
                fallback_desc = f"Defined as {sym_type} in the {rel_path} subsystem."

                bullets = [
                    f"📍 **{sym_name}** (`{rel_path}:{start_l}`): {doc_summary or fallback_desc}",
                    f"💡 **Explanation & Signature**: `{sig}`. Implements the core {sym_type} logic at lines {start_l}-{end_l}."
                ]
            else:
                bullets = [
                    f"📍 **Query Reference**: \"{speech_clean}\"",
                    f"💡 **Status**: Scanned codebase subsystems but found no direct AST match."
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
