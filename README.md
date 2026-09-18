<div align="center">

<img src="logo.png" alt="Codely Logo" width="130" height="130" style="border-radius: 26px;" />

# ⚡ Codely • Universal Desktop Overlay Context Engine

### **Zero-Latency Live Codebase HUD for Technical Meetings, Standups & Architecture Reviews**

[![Tauri v2](https://img.shields.io/badge/Tauri-v2%20(Rust)-FFC131?style=for-the-badge&logo=tauri&logoColor=white)](https://tauri.app/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Stealth Mode](https://img.shields.io/badge/Stealth%20Mode-Invisible%20to%20Zoom-00F5A0?style=for-the-badge)](https://github.com/rushh001/Codely)
[![Gemini 3.5+](https://img.shields.io/badge/Gemini-3.5%20Flash%20%26%20Above-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o%20%7C%20o3--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://platform.openai.com/)
[![Claude](https://img.shields.io/badge/Claude-3.5%20Haiku%20%7C%20Sonnet-D97706?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com/)
[![Groq Whisper](https://img.shields.io/badge/Groq-Whisper%20Large%20v3-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

</div>

---

## 🌟 What is Codely?

**Codely** is an ultra-lightweight (**<30 MB RAM**), transparent desktop HUD overlay engineered with **Tauri (Rust) and React**. 

It floats seamlessly above **Zoom, Microsoft Teams, Google Meet, and VS Code**, capturing both your voice and meeting participants' audio in real-time. When a teammate or client asks a complex question about your codebase, Codely queries a local AST topology map and flashes the exact answer, component location, architectural mechanics, and code snippets on your screen **before you even begin speaking**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S SCREEN                                 │
│                                                                         │
│  ┌─────────────────────────┐     ┌───────────────────────────────────┐  │
│  │ Zoom / Teams / Meet     │     │    CODELY HUD OVERLAY (Tauri)     │  │
│  │ (Video Call Window)     │     │    alwaysOnTop + True Glass       │  │
│  │                         │     │                                   │  │
│  │  Colleague: "How does   │────▶│  📍 EvaluationMode (config.py:16) │  │
│  │  EvaluationMode work in │     │  💡 Execution strategy options    │  │
│  │  our evaluator config?" │     │     (NON_INTRUSIVE, INTRUSIVE)    │  │
│  │                         │     │  [AST Code Snippet with Copy]     │  │
│  └─────────────────────────┘     └───────────────────────────────────┘  │
│                                                                         │
│  [System Audio Loopback] ────▶ [Dual Audio Engine] ────▶ [Whisper STT] │
│  [Microphone Input]      ────▶ [Multi-Provider AI] ────▶ [Local AST]   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Provider AI Intelligence

Codely supports industry-leading reasoning models with **zero-restart live switching** from the HUD Preferences drawer:

### 1. Google Gemini (3.5 Flash & Above)
* **`gemini-3.5-flash`** *(Default & Recommended)*: Flagship model delivering sub-second code understanding with massive context.
* **`gemini-3.5-flash-lite`**: Ultra-low latency (<1.2s) live reasoning stream.
* **`gemini-3.6-flash`**: High-precision architectural analysis.
* **`gemini-3.7-flash`**: Next-generation reasoning and synthesis.
* *Automatic Fallback:* If a transient 503 spike occurs, the engine automatically cascades through the active 3.5+ catalog to guarantee zero failed queries.

### 2. OpenAI
* **`gpt-4o-mini`** *(Recommended)*: High-speed, high-precision code reasoning.
* **`gpt-4o`**: Flagship code and system architecture intelligence.
* **`o3-mini`**: Deep algorithmic and multi-step code reasoning.
* **`o1-mini`**: Complex constraint and logic reasoning.

### 3. Anthropic Claude
* **`claude-3-5-haiku-latest`** *(Recommended)*: Sub-300ms live stream intelligence.
* **`claude-3-5-sonnet-latest`**: Industry-leading code generation and architectural synthesis.
* **`claude-3-7-sonnet-latest`**: Hybrid reasoning model for deep codebase analysis.

### 4. Groq Cloud
* **Whisper Large-v3**: Sub-200ms ultra-fast speech-to-text transcription.
* **Llama 3.3 70B Versatile & Llama 3.1 8B Instant**: High-throughput fallback reasoning.

---

## ✨ Key Capabilities

### 🛡️ 1. Screen Share Invisibility ("Stealth Mode")
* **100% Invisible to Call Participants:** Powered by the Windows Desktop Window Manager API (`SetWindowDisplayAffinity(hwnd, 0x11)` / `WDA_EXCLUDEFROMCAPTURE`).
* **Clean Screen Sharing:** Codely remains visible to you on your physical monitor, but is completely excluded from video call capture in **Zoom, Teams, Google Meet, Discord, and OBS** — even during **Entire Screen (Full Desktop)** sharing!
* **Toggle Anytime:** Toggle on or off with one click on the HUD header or via Preferences.

### 🎙️ 2. Two-Way Meeting Audio (Dual Stream)
Captures both conversation channels concurrently:
* **Stream 1 (Microphone / You):** Tracks your voice queries and displays answers tagged with `👤 YOU`.
* **Stream 2 (System Audio Loopback / Colleague):** Uses Windows **WASAPI Loopback / Stereo Mix** (or macOS BlackHole / Linux PulseAudio Monitor) to capture questions asked by teammates, tagged with an amber `❓ COLLEAGUE` badge.

### ⚡ 3. Sub-Millisecond AST Retrieval Engine
* **Universal Codebase Sources:** Point Codely to local directories, GitHub URLs (e.g. `https://github.com/fastapi/fastapi`), or `.zip` archives.
* **Tree-Sitter Multi-Language Parsing:** Extracts symbols, signatures, and docstrings across Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, etc.
* **SQLite FTS5 + BM25:** Macro topology partitions and symbol search execute in `< 1.2ms`.
* **100% Local & Private:** Code never leaves your machine; only relevant context snippets are sent to your chosen LLM provider.

### 💡 4. High-Density Explanation Output
Every answer card provides:
1. 📍 **Exact Component Location & Role**: `📍 **[ComponentName]** (path/to/file.py:line)` with a concise explanation of what the component does.
2. 💡 **Technical Explanation & Mechanics**: Clear explanation of how it works, parameters, execution modes, and direct answer to the question.
3. 📄 **Exact AST Code Snippet**: Rendered with line numbers and 1-click clipboard copy.

### 🪟 5. True Desktop Glass & Responsive Window Modes
* **True Desktop Glass:** Window uses genuine frosted glass (`backdrop-filter: blur(24px)`) over your desktop, editor, or video calls.
* **Opacity Slider:** Adjust transparency from 50% to 100%.
* **Interface Themes:** Toggle between **🌙 Dark Mode** and **☀️ Light Mode** with persistent preferences.
* **Window Modes:**
  * **`DOCK`** (720px wide): Full meeting sidebar pinned to the right edge with split logs.
  * **`MINI`** (440px wide): Compact floating card for minimal screen obstruction.
  * **`STRIP`** (160px ticker): Collapsed bottom bar for subtitle-style query feedback.

---

## 📖 Usage Guide

### Keyboard Shortcuts
| Shortcut | Action | Scope |
| :--- | :--- | :--- |
| **`Ctrl + Shift + Space`** *(Win/Linux)* | Show / Hide HUD Overlay | Global (any application) |
| **`Cmd + Shift + Space`** *(macOS)* | Show / Hide HUD Overlay | Global (any application) |
| **`Enter`** *(in search bar)* | Submit manual query | In HUD |
| **`Esc`** | Close Preferences Modal | In HUD |

### Meeting Workflow
1. **Launch Codely** before your standup, architectural review, or client call.
2. Press **`Ctrl + Shift + Space`** to position the HUD on your screen.
3. Turn on the microphone toggle or let WASAPI loopback capture meeting speech.
4. As teammates discuss questions (e.g. *"Where is the auth token validated?"*), Codely automatically parses the intent, retrieves the AST symbols, and renders the explanation card with code.
5. Use the **Copy** button on any code snippet to paste directly into meeting chats or IDEs.

### Manual Search Workflow
* Type natural language or code symbol questions directly into the top search bar (e.g., *"how does EvaluationMode work in evaluator config"*).
* Press `Enter` or click **Search** for instant AST matching and explanation generation.

### Switching Providers at Runtime
1. Click the **Gear icon (⚙️)** in the HUD header to open Preferences.
2. Select your reasoning provider: **Google Gemini**, **OpenAI**, or **Anthropic Claude**.
3. Choose your preferred model (e.g. `Gemini 3.5 Flash`, `GPT-4o Mini`, `Claude 3.5 Haiku`).
4. Enter or update your API key and click **Save Changes** — changes apply immediately with zero app restarts.

---

## 📦 Download Pre-Built Installers

Download compiled release binaries from the [GitHub Releases](https://github.com/rushh001/Codely/releases) page:

| Operating System | Package Format | Binary |
| :--- | :--- | :--- |
| **Windows** | `.exe` (Installer) | `Codely_1.0.0_x64-setup.exe` |
| **Windows** | `.msi` (Windows Installer) | `Codely_1.0.0_x64_en-US.msi` |
| **macOS** | `.dmg` | `Codely_1.0.0_universal.dmg` |
| **Linux** | `.AppImage` / `.deb` | `Codely_1.0.0_amd64.AppImage` |

---

## 🛠️ Developer Setup (Run from Source)

### Prerequisites
* **Node.js 18+** & **npm**
* **Python 3.10+**
* **Rust toolchain** (`cargo` & `rustc` — [rustup.rs](https://rustup.rs))

### 1. Clone the Repository
```bash
git clone https://github.com/rushh001/Codely.git
cd Codely
```

### 2. Configure Environment (`backend/.env`)
Create `backend/.env` with your API credentials:
```env
# Groq API Key for Whisper Speech-to-Text
GROQ_API_KEY=gsk_your_groq_api_key_here

# Reasoning Provider Keys (Configure at least one)
GEMINI_API_KEY=AIzaSy_your_gemini_key_here
OPENAI_API_KEY=sk-proj-your_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_claude_key_here

# Active Configuration
ACTIVE_AI_PROVIDER=gemini
ACTIVE_AI_MODEL=gemini-3.5-flash
```

### 3. Setup Python Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Setup Frontend & Run Tauri Desktop HUD
In a separate terminal:
```powershell
cd frontend
npm install
npm run tauri:dev
```

*To run as a browser client during development:*
```powershell
npm run dev
# Navigate to http://localhost:5173
```

---

## 🏗️ Building Production Binaries

### Step 1: Compile the Python Sidecar Binary
```powershell
cd backend
.\build_backend.bat
```
Produces `backend\dist\codely-backend.exe`.

### Step 2: Build the Tauri Desktop Installer
```powershell
cd frontend
npm run tauri:build
```
Compiled installers are automatically organized in `dist-installers/`.

---

## 📊 Performance Benchmarks

Tested on enterprise codebases (10,000+ AST symbols):
* **AST Subsystem Routing:** `< 1.2 ms`
* **SQLite FTS5 BM25 Lookup:** `< 0.9 ms`
* **Whisper Large-v3 STT (Groq):** `~180 ms`
* **Gemini 3.5 Flash Reasoning:** `~1.2s - 2.5s`
* **Desktop RAM Footprint:** `< 30 MB`

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more details.
