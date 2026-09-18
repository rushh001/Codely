import os
import io
import time
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import CodebaseDB
from indexer import CodebaseIndexer
from groq_service import GroqEngine
from audio_service import DualAudioCaptureService
from audio_loopback import list_audio_devices

app = FastAPI(title="Codely Live Codebase Context Engine API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
db = CodebaseDB()
indexer = CodebaseIndexer(db)
groq_engine = GroqEngine()
audio_service = DualAudioCaptureService(silence_duration=1.8, energy_threshold=0.016)

current_repo_path: Optional[str] = None


# Connection Manager for real-time WebSockets
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()
loop = asyncio.get_event_loop()


def send_log_sync(tag: str, message: str, level: str = "INFO", meta: Optional[Dict[str, Any]] = None):
    ts = time.strftime("%H:%M:%S")
    asyncio.run_coroutine_threadsafe(
        manager.broadcast({
            "type": "pipeline_log",
            "tag": tag,
            "level": level,
            "message": message,
            "timestamp": ts,
            "meta": meta or {}
        }),
        loop
    )


WHISPER_HALLUCINATIONS = {
    "thank you", "thank you.", "thank you very much", "thanks", "thanks for watching",
    "thank you for watching", "thank you for watching!", "thanks for watching!",
    "you", "bye", "bye bye", "goodbye", "hello", "hi", "so", "the end",
    "subtitles by", "translated by", "watching", "subscribe", "please subscribe",
    "i", "a", "an", "the", "thank", "thanks.", "thank you!", "you.", "you!", "thanks!"
}


def is_hallucinated_or_empty(text: str) -> bool:
    """
    Detects Whisper silence artifacts and empty/whitespace text to avoid false searches.
    """
    if not text:
        return True
    cleaned = text.strip().strip(".,!?:;\"'").lower()
    if not cleaned or len(cleaned) < 2:
        return True
    if cleaned in WHISPER_HALLUCINATIONS:
        return True
    if set(cleaned) <= set(" .-_!?,;:'\""):
        return True
    return False


def handle_speech_audio_chunk(wav_bytes: bytes, speaker: str = "you"):
    """
    Called asynchronously when local microphone or system audio detects a completed voice utterance.
    speaker: 'you' (microphone) or 'colleague' (meeting speaker loopback)
    """
    t_start = time.time()
    source_tag = "YOU" if speaker == "you" else "COLLEAGUE"
    send_log_sync("VAD", f"[{source_tag}] Voice utterance captured ({len(wav_bytes)/1024:.1f} KB). Processing...", "DEBUG")

    trans_res = groq_engine.transcribe_audio_bytes(wav_bytes)
    text = trans_res.get("text", "")
    stt_latency = trans_res.get("latency_ms", 0)

    if is_hallucinated_or_empty(text):
        send_log_sync("VAD", f"[{source_tag}] Ignored silence artifact (\"{text}\")", "DEBUG")
        return

    send_log_sync("STT", f"[{source_tag}] Transcribed in {stt_latency}ms: \"{text}\"", "SUCCESS")

    # Broadcast live transcription event with speaker identity
    asyncio.run_coroutine_threadsafe(
        manager.broadcast({
            "type": "transcription",
            "text": text,
            "speaker": speaker,
            "latency_ms": stt_latency
        }),
        loop
    )

    # Process code context retrieval
    send_log_sync("INTENT", f"[{source_tag}] Analyzing sentence intent & searching AST...", "INFO")
    retrieval_res = groq_engine.process_query_and_retrieve(text, db)
    total_latency = (time.time() - t_start) * 1000

    best_sym = retrieval_res.get("best_symbol")
    if best_sym:
        send_log_sync("MATCH", f"[{source_tag}] AST Match: {best_sym['name']} in {best_sym['relative_path']}:{best_sym['start_line']} (Total: {total_latency:.1f}ms)", "SUCCESS")
    else:
        send_log_sync("MATCH", f"[{source_tag}] Context generated (Total: {total_latency:.1f}ms)", "INFO")

    # Broadcast context result event with speaker identity
    asyncio.run_coroutine_threadsafe(
        manager.broadcast({
            "type": "context_result",
            "data": {
                **retrieval_res,
                "speaker": speaker,
                "transcription_latency_ms": stt_latency,
                "e2e_latency_ms": round(total_latency, 1)
            }
        }),
        loop
    )


audio_service.set_on_speech_callback(handle_speech_audio_chunk)


def save_env_variables(vars_dict: Dict[str, str]):
    try:
        env_path = Path(__file__).parent / ".env"
        existing_lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
                
        updated_keys = set()
        new_lines = []
        for line in existing_lines:
            line_stripped = line.strip()
            matched = False
            for k, v in vars_dict.items():
                if v is None:
                    continue
                if line_stripped.startswith(f"{k}=") or line_stripped.startswith(f"#{k}="):
                    new_lines.append(f"{k}={v}\n")
                    updated_keys.add(k)
                    matched = True
                    break
            if not matched:
                new_lines.append(line)
                
        for k, v in vars_dict.items():
            if v and k not in updated_keys:
                new_lines.append(f"{k}={v}\n")
                
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[Warning] Failed to update .env: {e}")


# Request schemas
class ConfigRequest(BaseModel):
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    active_provider: Optional[str] = None
    active_model: Optional[str] = None
    repo_path: Optional[str] = None


class AudioSettingsRequest(BaseModel):
    silence_duration: Optional[float] = None
    energy_threshold: Optional[float] = None


class IndexRequest(BaseModel):
    repo_path: str


class QueryRequest(BaseModel):
    query: str


@app.get("/api/providers")
def get_providers():
    return {
        "success": True,
        **groq_engine.get_providers_state()
    }


@app.get("/api/status")
def get_status():
    summary = db.get_indexed_summary()
    prov_state = groq_engine.get_providers_state()
    return {
        "status": "ready",
        "groq_configured": groq_engine.is_configured(),
        "is_listening": audio_service.is_listening,
        "silence_duration": audio_service.silence_duration,
        "energy_threshold": audio_service.energy_threshold,
        "current_repo": current_repo_path,
        "database_stats": summary,
        "active_provider": prov_state["active_provider"],
        "active_model": prov_state["active_model"],
        "providers_state": prov_state
    }


@app.get("/api/audio/devices")
def get_audio_devices():
    return {
        "success": True,
        "devices": list_audio_devices()
    }


@app.post("/api/config")
def update_config(config: ConfigRequest):
    global current_repo_path
    
    groq_engine.set_provider_config(
        active_provider=config.active_provider,
        active_model=config.active_model,
        gemini_api_key=config.gemini_api_key,
        openai_api_key=config.openai_api_key,
        anthropic_api_key=config.anthropic_api_key,
        groq_api_key=config.groq_api_key
    )

    env_updates = {}
    if config.groq_api_key is not None:
        env_updates["GROQ_API_KEY"] = config.groq_api_key
    if config.gemini_api_key is not None:
        env_updates["GEMINI_API_KEY"] = config.gemini_api_key
    if config.openai_api_key is not None:
        env_updates["OPENAI_API_KEY"] = config.openai_api_key
    if config.anthropic_api_key is not None:
        env_updates["ANTHROPIC_API_KEY"] = config.anthropic_api_key
    if config.active_provider is not None:
        env_updates["ACTIVE_AI_PROVIDER"] = config.active_provider
    if config.active_model is not None:
        env_updates["ACTIVE_AI_MODEL"] = config.active_model

    if env_updates:
        save_env_variables(env_updates)

    if config.repo_path is not None:
        current_repo_path = config.repo_path
        send_log_sync("CONFIG", f"Target repository path set to: {current_repo_path}", "INFO")

    prov_state = groq_engine.get_providers_state()
    send_log_sync("CONFIG", f"AI Provider set to {prov_state['active_provider'].upper()} ({prov_state['active_model']})", "SUCCESS")

    return {
        "success": True,
        "is_configured": groq_engine.is_configured(),
        "current_repo": current_repo_path,
        "providers_state": prov_state
    }


@app.post("/api/audio/settings")
def update_audio_settings(req: AudioSettingsRequest):
    audio_service.update_settings(
        silence_duration=req.silence_duration,
        energy_threshold=req.energy_threshold
    )
    send_log_sync("CONFIG", f"Voice Pause Duration set to {audio_service.silence_duration}s (Energy: {audio_service.energy_threshold})", "SUCCESS")
    return {
        "success": True,
        "silence_duration": audio_service.silence_duration,
        "energy_threshold": audio_service.energy_threshold
    }


@app.post("/api/index")
def index_repo(req: IndexRequest):
    global current_repo_path
    raw_path = req.repo_path.strip().strip('"').strip("'").strip()
    if not raw_path:
        return {"success": False, "error": "Target repository path or GitHub URL cannot be empty"}

    send_log_sync("INDEX", f"Starting AST scan & Macro Topology build on: {raw_path}", "INFO")
    t0 = time.time()
    try:
        summary = indexer.index_directory(raw_path)
        current_repo_path = summary.get("resolved_path", raw_path)
        elapsed = time.time() - t0
        send_log_sync("INDEX", f"Indexed {summary['total_symbols']} symbols across {summary['total_files']} files ({summary['topology_modules']} subsystems) in {elapsed:.2f}s", "SUCCESS")
        
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "index_completed",
                "stats": summary,
                "current_repo": current_repo_path
            }),
            loop
        )
        return {"success": True, "stats": summary, "current_repo": current_repo_path}
    except Exception as e:
        send_log_sync("INDEX", f"Indexing failed: {str(e)}", "ERROR")
        return {"success": False, "error": str(e)}


@app.post("/api/query")
def query_manual(req: QueryRequest):
    query_text = req.query.strip()
    if is_hallucinated_or_empty(query_text):
        return {"success": False, "error": "Query is empty or invalid"}

    t_start = time.time()
    send_log_sync("QUERY", f"Manual query: \"{query_text}\"", "INFO")
    
    retrieval_res = groq_engine.process_query_and_retrieve(query_text, db)
    total_latency = (time.time() - t_start) * 1000

    best_sym = retrieval_res.get("best_symbol")
    if best_sym:
        send_log_sync("MATCH", f"AST Match: {best_sym['name']} in {best_sym['relative_path']}:{best_sym['start_line']} ({total_latency:.1f}ms)", "SUCCESS")
    
    return {
        "success": True,
        "result": {
            **retrieval_res,
            "e2e_latency_ms": round(total_latency, 1)
        }
    }


@app.post("/api/mic/start")
def start_mic():
    res = audio_service.start_listening()
    if res.get("success"):
        send_log_sync("MIC", f"Microphone active (Pause threshold: {audio_service.silence_duration}s)", "SUCCESS")
    else:
        send_log_sync("MIC", f"Microphone error: {res.get('error')}", "WARN")
    return res


@app.post("/api/mic/stop")
def stop_mic():
    res = audio_service.stop_listening()
    send_log_sync("MIC", "Microphone stream stopped", "INFO")
    return res


@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    t_start = time.time()
    audio_bytes = await file.read()
    send_log_sync("AUDIO", f"Received audio buffer upload ({len(audio_bytes)/1024:.1f} KB)", "DEBUG")

    trans_res = groq_engine.transcribe_audio_bytes(audio_bytes)
    text = trans_res.get("text", "")
    stt_latency = trans_res.get("latency_ms", 0)

    if is_hallucinated_or_empty(text):
        err = "No meaningful speech detected (ambient silence)"
        send_log_sync("STT", f"Ignored silence / artifact: \"{text}\"", "DEBUG")
        return {
            "success": False,
            "error": err,
            "latency_ms": stt_latency
        }

    send_log_sync("STT", f"Transcribed: \"{text}\" in {stt_latency}ms", "SUCCESS")
    retrieval_res = groq_engine.process_query_and_retrieve(text, db)
    total_latency = (time.time() - t_start) * 1000

    best_sym = retrieval_res.get("best_symbol")
    if best_sym:
        send_log_sync("MATCH", f"AST Match: {best_sym['name']} in {total_latency:.1f}ms", "SUCCESS")

    return {
        "success": True,
        "transcription": text,
        "result": {
            **retrieval_res,
            "transcription_latency_ms": stt_latency,
            "e2e_latency_ms": round(total_latency, 1)
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    send_log_sync("WS", "Client connected to real-time telemetry stream", "INFO")
    try:
        summary = db.get_indexed_summary()
        prov_state = groq_engine.get_providers_state()
        await websocket.send_json({
            "type": "init",
            "groq_configured": groq_engine.is_configured(),
            "is_listening": audio_service.is_listening,
            "silence_duration": audio_service.silence_duration,
            "energy_threshold": audio_service.energy_threshold,
            "current_repo": current_repo_path,
            "database_stats": summary,
            "active_provider": prov_state["active_provider"],
            "active_model": prov_state["active_model"],
            "providers_state": prov_state
        })

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "query":
                query_text = data.get("text", "").strip()
                if is_hallucinated_or_empty(query_text):
                    continue
                t_start = time.time()
                res = groq_engine.process_query_and_retrieve(query_text, db)
                total_latency = (time.time() - t_start) * 1000
                await websocket.send_json({
                    "type": "context_result",
                    "data": {
                        **res,
                        "e2e_latency_ms": round(total_latency, 1)
                    }
                })

            elif msg_type == "index":
                repo_path = data.get("repo_path", "").strip()
                if os.path.exists(repo_path):
                    summary = indexer.index_directory(repo_path)
                    await manager.broadcast({
                        "type": "index_completed",
                        "stats": summary
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
