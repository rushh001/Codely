# ⚡ Codely • Universal Desktop Overlay Context Engine

<div align="center">

![Codely Banner](https://raw.githubusercontent.com/rushh001/Codely/main/frontend/src-tauri/icons/128x128@2x.png)

### **Zero-Latency Live Codebase HUD for Technical Meetings, Standups & Architecture Reviews**

[![Tauri v2](https://img.shields.io/badge/Tauri-v2%20(Rust)-FFC131?style=for-the-badge&logo=tauri&logoColor=white)](https://tauri.app/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Stealth Mode](https://img.shields.io/badge/Stealth%20Mode-Invisible%20to%20Zoom-00F5A0?style=for-the-badge)](https://github.com/rushh001/Codely)
[![Gemini 3.5](https://img.shields.io/badge/Gemini-3.5%20Flash%20Lite-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq Whisper](https://img.shields.io/badge/Groq-Whisper%20Large%20v3-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
[![SQLite FTS5](https://img.shields.io/badge/SQLite-FTS5%20BM25-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

</div>

---

## 🌟 What is Codely?

**Codely** is an ultra-lightweight (**<30 MB RAM**), transparent desktop HUD overlay built with **Tauri (Rust) and React**. 

It floats seamlessly above **Zoom, Microsoft Teams, Google Meet, and VS Code**, listening to both your voice and your meeting participants' audio in real-time. When a teammate or client asks a technical question about the codebase, Codely queries a local AST topology map and flashes the exact answer, code signatures, and file paths on your screen **before you even begin speaking**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S SCREEN                                 │
│                                                                         │
│  ┌─────────────────────────┐     ┌───────────────────────────────────┐  │
│  │ Zoom / Teams / Meet     │     │    CLUELY HUD OVERLAY (Tauri)     │  │
│  │ (Video Call Window)     │     │    alwaysOnTop + transparent      │  │
│  │                         │     │                                   │  │
│  │  Colleague: "Where is   │────▶│  ⚡ BaseLLMJudge (class)           │  │
│  │  the rate-limiting      │     │  1. Inventory: Accuracy,          │  │
│  │  metric defined?"       │     │     Hallucination, Relevance      │  │
│  │                         │     │  2. Entry: app/evaluator/         │  │
│  └─────────────────────────┘     │     metrics/llm_judge/            │  │
│                                  └───────────────────────────────────┘  │
│                                                                         │
│  [System Audio Loopback] ────▶ [Dual Audio Engine] ────▶ [Whisper STT] │
│  [Microphone Input]      ────▶ [Gemini 3.5 Flash]  ────▶ [Local AST]   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🛡️ 1. Screen Capture Invisibility ("Stealth Mode")
- **100% Invisible on Screen Share:** Powered by the native Windows Desktop Window Manager API (`SetWindowDisplayAffinity(hwnd, 0x11)` / `WDA_EXCLUDEFROMCAPTURE`).
- **How it works:** Codely renders normally onto your physical monitor, but is **completely removed from video call captures, recordings, and screenshots** in **Zoom, Microsoft Teams, Google Meet, Discord, and OBS** — even during **Entire Screen (Full Desktop)** sharing!
- **Zero Artifacts:** Meeting participants see clean code editor windows or your desktop background without any black boxes or clipping.
- **Toggle Anytime:** Easily toggle on/off with the **`🛡️ STEALTH: ON`** button in the HUD header or Settings drawer.

### 🎙️ 2. Two-Way Meeting Audio (Dual Stream Loopback)
Captures both audio channels concurrently:
- **Stream 1 (Microphone / You):** Tracks your voice queries and displays answers with a `👤 YOU` badge.
- **Stream 2 (System Audio Loopback / Colleague):** Uses Windows **WASAPI Loopback / Stereo Mix** (or macOS BlackHole / Linux PulseAudio Monitor) to capture questions spoken by teammates over your headphones or speakers, flashing cards with an **amber glowing border and `❓ COLLEAGUE` badge**.

### ⚡ 3. Sub-Millisecond AST Topology Engine & Universal Ingestion
- **Flexible Codebase Sources:** Point Codely to any of the following targets — it handles the rest automatically:
  - 🌐 **Public GitHub URLs:** Enter links like `https://github.com/fastapi/fastapi` or `github.com/facebook/react`. Codely clones or streams the repository and indexes the full AST topology in seconds.
  - 🗜️ **`.ZIP` Archives & Explorer Paths:** Pass `.zip` files (e.g. `C:\downloads\project.zip` or virtual paths inside zipped folders); Codely automatically extracts and indexes the codebase.
  - 📁 **Local Directories:** Target any local codebase folder across Python, TypeScript, JavaScript, Rust, Go, C/C++, Java, etc.
- **Tree-Sitter Multi-Language AST Parsing:** Indexes full class signatures, method parameters, and docstrings into a **local SQLite FTS5 database** with BM25 ranking (`< 1.2ms` lookup).
- **100% Privacy:** Source code is analyzed locally on your machine and never uploaded to cloud vector databases.

### 🧠 4. Hybrid High-Speed AI Synthesis
- **Whisper Large-v3 (via Groq):** Sub-200ms voice transcription.
- **Google Gemini 3.5 Flash Lite:** 1M token context reasoning engine that analyzes the retrieved code symbols and produces two strictly decoupled bullets:
  - **Bullet 1 (Entity Inventory):** Concrete list of matching classes, functions, and file paths with backticks.
  - **Bullet 2 (Operational Mechanics):** Internal logic flow, invocation contracts, retry rules, and parameter signatures.

### 🖥️ 5. Native Desktop HUD Controls
- **Global Toggle Hotkey:** Press **`Ctrl + Shift + Space`** (Windows/Linux) or **`Cmd + Shift + Space`** (macOS) to instantly hide or show the HUD overlay from anywhere.
- **Position Modes:** 
  - **`DOCK`** (Right screen edge — default meeting HUD)
  - **`MINI`** (Compact floating card)
  - **`STRIP`** (Collapsed bottom bar)
- **Active IDE Auto-Repo Detection:** Rust background worker monitors foreground window titles. When you switch to VS Code, Cursor, PyCharm, or IntelliJ, it detects the active project and offers one-click re-indexing.
- **System Tray:** Minimize to taskbar with quick options to rescan repositories or adjust opacity.

---

## 📦 Installation & Releases

### Download Pre-Built Installers
Grab the latest release from the [GitHub Releases](https://github.com/rushh001/Codely/releases) tab:

| Operating System | Format | Package |
| :--- | :--- | :--- |
| **Windows** | `.msi` / `.exe` | `Codely_1.0.0_x64_en-US.msi` / `Codely_1.0.0_x64-setup.exe` |
| **macOS** | `.dmg` | `Codely_1.0.0_universal.dmg` (Apple Silicon & Intel) |
| **Linux** | `.AppImage` / `.deb` | `Codely_1.0.0_amd64.AppImage` |

---

## 🛠️ Developer Setup (Run from Source)

### Prerequisites
- **Node.js 18+** & **npm**
- **Python 3.10+**
- **Rust toolchain** (`rustc` & `cargo` — install via [rustup.rs](https://rustup.rs))

### 1. Clone & Setup Environment
```bash
git clone https://github.com/rushh001/Codely.git
cd Codely
```

### 2. Configure Backend (.env)
Create `backend/.env`:
```env
GROQ_API_KEY=gsk_your_groq_key_here
GEMINI_API_KEY=AIzaSy_your_gemini_key_here
```

### 3. Install Backend Dependencies & Start Server
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Start the Tauri Desktop Overlay
In a separate terminal:
```powershell
cd frontend
npm install
npm run tauri:dev
```

*Or launch the web browser version:*
```powershell
npm run dev
# Open http://localhost:5173
```

---

## 🏗️ Building One-Click Installers

### Step 1: Package the Backend Binary
```powershell
cd backend
.\build_backend.bat
```

### Step 2: Build the Tauri Desktop Bundle
```powershell
cd frontend
npm run tauri:build
```
The compiled installer will be copied directly to `dist-installers/msi/Codely_1.0.0_x64_en-US.msi`.

---

## 🎯 Benchmark Performance

Tested on production codebases (10,000+ AST symbols):
- **Local AST Indexing:** ~1.2s for 150+ source files.
- **SQLite FTS5 Symbol Match:** `0.85 ms`
- **Whisper Speech-to-Text:** `~180 ms`
- **Gemini Context Synthesis:** `~1.8s`
- **RAM Footprint:** `< 28 MB` (WebView2 / Tauri)

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
