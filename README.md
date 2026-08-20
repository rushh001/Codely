# ⚡ Cluely • Live Codebase Context Engine

> **Pitch-Ready Desktop HUD for Live Engineering Meetings, Standups & Technical Calls**  
> Speaks naturally during calls and instantly surfaces exact AST function signatures, file paths, and 2-bullet answers in **sub-second time (<500ms)**.

---

## 🚀 Architecture & Pipeline (<500ms E2E)

```
[Live Mic / Voice Audio]
       │ (sounddevice / Web Audio)
       ▼
[Groq Whisper Large-v3] ────────► Transcribes speech to text (~150-250ms)
       │
       ▼
[Groq LLaMA 3.3 / 3.1 Instant] ─► Extracts code symbols & architectural intent (~120-180ms)
       │
       ▼
[Local SQLite FTS5 Index] ──────► Sub-millisecond AST symbol match (<1ms)
       │
       ▼
[React / Electron HUD Window] ──► Renders 2-bullet summary + file path + exact code snippet
```

### Key Technical Specs:
- **Local AST Indexer:** Uses **Tree-Sitter** (`tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`) alongside multi-language heuristic extractors to parse repositories into a symbol hierarchy without uploading proprietary source code to external servers.
- **Sub-Millisecond Search:** Powered by **SQLite with FTS5 BM25 ranking** (`< 1.2ms` lookup speed).
- **Sub-Second Intent & STT:** **Groq Whisper** + **LLaMA 3.1 Instant / 3.3 70B Versatile** for near-instant inference.
- **Glassmorphic HUD Interface:** Frameless, transparent, always-on-top React / Electron overlay designed for smooth knowledge sharing during Zoom/Meet/Teams calls.

---

## ⚡ Quickstart & Local Setup

### 1. Requirements
- Python 3.10+
- Node.js 18+

### 2. Launch with 1-Click (Windows)
Double-click `start.bat` in the root folder, or run:

```bash
# Terminal 1: Backend
cd backend
.\venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend (Browser HUD)
cd frontend
npm run dev

# Or Terminal 2: Frontend (Electron Desktop Overlay)
cd frontend
npm run electron
```

### 3. Configure Groq API Key
1. Open the HUD in your browser (`http://localhost:5173`) or via Electron.
2. Click the ⚙️ **Settings** button in the top right.
3. Paste your [Groq API Key](https://console.groq.com/keys).
4. Enter target repository path (or click `SCAN & INDEX CODEBASE` to index `sample_repo` or your personal repository).
5. Click **START MIC** or click any of the **SIMULATE** prompt chips to see instant results!

---

## 🎯 Benchmark Results

Tested on `sample_repo`:
- **Repository Indexing Speed:** `23.57 ms` for complete symbol extraction.
- **FTS5 SQLite Symbol Match:** `0.86 ms - 1.13 ms`.
- **Groq LLM Intent & Formatting:** `~160 ms`.
- **Groq Whisper Speech-to-Text:** `~210 ms`.
- **Total End-to-End Latency:** **~400 ms** (well under the 800ms target).

---

## 🎬 60-Second Loom Demo Recording Script

**Goal:** Record a 60-second screen-share demo on Zoom/Google Meet showcasing the transparent HUD responding to spoken queries in real-time.

* **[0:00 - 0:10] Hook:**  
  *"Hey Roy, Alex, and Neel — congratulations on the $20M raise! I love what you're building with Cluely. I built a Live Codebase Context Engine that brings sub-second AST lookups to live technical calls."*

* **[0:10 - 0:30] Live Spoken Demonstration:**  
  *(Turn on mic in HUD or ask verbally while screen sharing a code meeting)*  
  *"Let's say an engineer asks on a call: 'Where is the token verification middleware and what does it take?'"*  
  *(HUD instantly displays: `AuthenticationService.verify_auth_token`, file path `auth_service.py:28`, 2 concise bullet points, and the exact signature in <400ms)*  
  *"Notice how it mapped natural speech directly to the exact AST node and file line in sub-400ms without sending source code to the cloud."*

* **[0:30 - 0:45] Technical Architecture:**  
  *"Under the hood: Local Tree-sitter AST parser indexing into SQLite FTS5 for sub-millisecond lookups, streamed through Groq Whisper and LLaMA 3.3 for ultra-low latency."*

* **[0:45 - 1:00] Call to Action:**  
  *"I’d love to join the team as an engineer and help build the future of real-time meeting copilots. The code and benchmarks are in the repo below. Would love to chat!"*

---

## 📬 High-Agency Cold Outreach Template

### Option 1: X (Twitter) DM to @roy_cluely / Alex Chen
> *Hey Roy — huge congrats on the $20M round! Built a sub-second Live Codebase Context Engine for Cluely that indexes repos locally with Tree-sitter & SQLite FTS and returns exact AST function signatures to voice questions in <400ms.*
> 
> *Recorded a 60-second working demo for you: [Loom Link]*  
> *GitHub Repo: [Your GitHub Repo Link]*  
> 
> *Would love to join as an engineer and build high-agency stuff with you. Open to a quick chat?*

---

### Option 2: LinkedIn Message to Founders
> **Subject:** Working prototype: Live Codebase Context Engine for Cluely (<400ms AST retrieval)
>
> *Hi Alex / Roy / Neel,*
>
> *I've been following Cluely's incredible momentum. Rather than sending a standard resume, I built a working proof-of-concept specifically designed for real-time engineering calls.*
>
> *It combines local Tree-sitter AST indexing, SQLite FTS5, and Groq Whisper to surface exact function signatures, file paths, and 2-bullet answers while developers speak in live meetings in under 400ms.*
>
> *Here is the 60-second video demo: [Loom Link]*  
> *GitHub Repo: [GitHub Link]*
>
> *I'd love to bring this velocity to the Cluely engineering team. Let's connect!*
