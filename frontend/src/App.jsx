import React, { useState, useEffect, useRef } from 'react';
import Onboarding from './components/Onboarding';
import SettingsPanel from './components/SettingsPanel';

// Tauri invoke & event — safe no-op in browser dev mode
const tauriInvoke = async (cmd, args = {}) => {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    return await invoke(cmd, args);
  } catch {
    // Running in browser dev mode (not Tauri) — silently ignore
  }
};

const tauriListen = async (event, callback) => {
  try {
    const { listen } = await import('@tauri-apps/api/event');
    return await listen(event, callback);
  } catch {
    // Browser mode
  }
};
import { 
  Mic, 
  MicOff, 
  Search, 
  Settings, 
  Terminal, 
  Cpu, 
  Layers, 
  Zap, 
  Copy, 
  Check, 
  Code2, 
  ExternalLink,
  Minimize2,
  X,
  Volume2,
  FolderGit2,
  Sliders,
  ChevronRight,
  Radio,
  FileCode,
  Sparkles,
  Info,
  Clock,
  Trash2
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
const WS_BASE = "ws://127.0.0.1:8000/ws";

export default function App() {
  // State
  const [isListening, setIsListening] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [groqConfigured, setGroqConfigured] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showLogs, setShowLogs] = useState(true);
  const [opacityVal, setOpacityVal] = useState(0.95);
  const [silenceDuration, setSilenceDuration] = useState(1.8);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [positionMode, setPositionMode] = useState('right');
  const [showOnboarding, setShowOnboarding] = useState(() => localStorage.getItem('cluely_onboarded') !== 'true');
  const [detectedRepoToast, setDetectedRepoToast] = useState(null);

  // Repository & Search State
  const [currentRepo, setCurrentRepo] = useState('');
  const [repoPathInput, setRepoPathInput] = useState('C:\\Users\\mohdz\\Valiqor\\backend');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [lastLatency, setLastLatency] = useState(null);
  
  // Results & Logs
  const [resultsList, setResultsList] = useState([]);
  const [dbStats, setDbStats] = useState({ total_symbols: 0, total_files: 0, languages: {} });
  const [logs, setLogs] = useState([]);

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const logsEndRef = useRef(null);

  // Listen for Tauri active IDE window detection
  useEffect(() => {
    let unlisten;
    tauriListen('repo-detected', (event) => {
      if (event.payload && event.payload.project_hint) {
        setDetectedRepoToast(event.payload);
      }
    }).then(fn => { unlisten = fn; });

    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  // Helper to add structured pipeline logs
  const addLog = (tag, message, level = "INFO") => {
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [...prev.slice(-99), { tag, message, level, timestamp: ts }]);
  };

  // Scroll logs to bottom when updated
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Connect WebSocket
  useEffect(() => {
    let reconnectTimer;
    function connectWS() {
      const socket = new WebSocket(WS_BASE);
      wsRef.current = socket;

      socket.onopen = () => {
        setWsConnected(true);
        addLog("WS", "Connected to real-time backend pipeline", "SUCCESS");
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'init') {
            setGroqConfigured(msg.groq_configured);
            setIsListening(msg.is_listening);
            setCurrentRepo(msg.current_repo || '');
            if (msg.silence_duration) setSilenceDuration(msg.silence_duration);
            if (msg.database_stats) setDbStats(msg.database_stats);
            addLog("INIT", `Database ready: ${msg.database_stats?.total_symbols || 0} symbols indexed`, "INFO");
          } else if (msg.type === 'transcription') {
            setLiveTranscript(msg.text);
            addLog("STT", `Transcribed: "${msg.text}" (${msg.latency_ms}ms)`, "SUCCESS");
          } else if (msg.type === 'context_result') {
            setIsProcessing(false);
            if (msg.data) {
              setResultsList(prev => [msg.data, ...prev.slice(0, 15)]);
              if (msg.data.speech_text) setLiveTranscript(msg.data.speech_text);
              if (msg.data.e2e_latency_ms) setLastLatency(msg.data.e2e_latency_ms);
              const sym = msg.data.best_symbol;
              if (sym) {
                addLog("MATCH", `AST Match: ${sym.name} in ${sym.relative_path}:${sym.start_line} (${msg.data.e2e_latency_ms}ms total)`, "SUCCESS");
              } else {
                addLog("MATCH", `Context generated (${msg.data.e2e_latency_ms}ms total)`, "INFO");
              }
            }
          } else if (msg.type === 'pipeline_log') {
            addLog(msg.tag || "PIPE", msg.message, msg.level || "INFO");
          } else if (msg.type === 'index_completed') {
            if (msg.stats) {
              setDbStats(msg.stats);
              addLog("AST", `Indexed ${msg.stats.total_symbols} symbols from ${msg.stats.total_files} files in ${msg.stats.elapsed_seconds}s`, "SUCCESS");
            }
          }
        } catch (e) {
          console.error("WS Parse Error:", e);
        }
      };

      socket.onclose = () => {
        setWsConnected(false);
        addLog("WS", "Backend connection dropped. Reconnecting...", "WARN");
        reconnectTimer = setTimeout(connectWS, 2000);
      };

      socket.onerror = () => {
        socket.close();
      };
    }

    connectWS();
    fetchStatus();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      const data = await res.json();
      setGroqConfigured(data.groq_configured);
      setIsListening(data.is_listening);
      if (data.silence_duration) setSilenceDuration(data.silence_duration);
      if (data.current_repo) {
        setCurrentRepo(data.current_repo);
        setRepoPathInput(data.current_repo);
      }
      if (data.database_stats) {
        setDbStats(data.database_stats);
      }
    } catch (e) {
      console.error("Fetch status error:", e);
    }
  };

  // Toggle Live Microphone Listening
  const handleToggleMic = async () => {
    if (isListening) {
      try {
        await fetch(`${API_BASE}/api/mic/stop`, { method: 'POST' });
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
        setIsListening(false);
        addLog("MIC", "Microphone listening paused", "INFO");
      } catch (e) {
        console.error(e);
      }
    } else {
      try {
        const res = await fetch(`${API_BASE}/api/mic/start`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          setIsListening(true);
          addLog("MIC", `Native Sounddevice active (Pause threshold: ${silenceDuration}s)`, "SUCCESS");
        } else {
          startBrowserMicRecording();
        }
      } catch (e) {
        startBrowserMicRecording();
      }
    }
  };

  // Browser Fallback Audio Recording
  const startBrowserMicRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        
        const formData = new FormData();
        formData.append('file', audioBlob, 'mic.webm');
        try {
          setIsProcessing(true);
          addLog("UPLOAD", `Processing ${(audioBlob.size / 1024).toFixed(1)} KB voice recording...`, "DEBUG");
          const res = await fetch(`${API_BASE}/api/audio/upload`, {
            method: 'POST',
            body: formData
          });
          const data = await res.json();
          setIsProcessing(false);
          if (data.success) {
            setResultsList(prev => [data.result, ...prev.slice(0, 15)]);
            if (data.transcription) setLiveTranscript(data.transcription);
            if (data.result?.e2e_latency_ms) setLastLatency(data.result.e2e_latency_ms);
          }
        } catch (e) {
          setIsProcessing(false);
          addLog("ERROR", `Audio processing failed: ${e.message}`, "ERROR");
        }
      };

      recorder.start();
      setIsListening(true);
      addLog("MIC", "Web Audio active. Speak your question and toggle mic to finish!", "SUCCESS");
    } catch (e) {
      alert("Microphone access error: " + e.message);
      setIsListening(false);
    }
  };

  // Submit manual / simulated query
  const handleQuery = async (textToQuery) => {
    const query = (textToQuery || searchQuery).trim();
    if (!query) return;

    setIsProcessing(true);
    setLiveTranscript(query);
    addLog("QUERY", `Simulated voice prompt: "${query}"`, "INFO");

    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      setIsProcessing(false);
      if (data.success) {
        setResultsList(prev => [data.result, ...prev.slice(0, 15)]);
        if (data.result?.e2e_latency_ms) setLastLatency(data.result.e2e_latency_ms);
      }
    } catch (err) {
      setIsProcessing(false);
      addLog("ERROR", `Query failed: ${err.message}`, "ERROR");
    }
  };

  // Index a codebase
  const handleIndexRepo = async () => {
    if (!repoPathInput.trim()) return;
    try {
      setIsProcessing(true);
      addLog("AST", `Scanning repository: ${repoPathInput.trim()}`, "INFO");
      const res = await fetch(`${API_BASE}/api/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPathInput.trim() })
      });
      const data = await res.json();
      setIsProcessing(false);
      if (data.success) {
        setDbStats(data.stats);
        setCurrentRepo(repoPathInput.trim());
        addLog("AST", `Scan complete! ${data.stats.total_symbols} symbols indexed.`, "SUCCESS");
      } else {
        alert(data.error || "Failed to index repository");
        addLog("AST", `Indexing error: ${data.error}`, "ERROR");
      }
    } catch (e) {
      setIsProcessing(false);
      alert("Indexing error: " + e.message);
    }
  };

  // Save Settings
  const handleSaveConfig = async () => {
    try {
      await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          groq_api_key: apiKeyInput || undefined,
          repo_path: repoPathInput || undefined
        })
      });
      
      await fetch(`${API_BASE}/api/audio/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          silence_duration: silenceDuration
        })
      });

      fetchStatus();
      setIsSettingsOpen(false);
      addLog("CONFIG", "Settings and Voice Pause Duration updated", "SUCCESS");
    } catch (e) {
      console.error("Config error:", e);
    }
  };

  // Update Silence Pause Slider
  const handleSilenceChange = (val) => {
    setSilenceDuration(val);
  };

  // Copy code to clipboard
  const handleCopy = (code, index) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Clear Logs
  const handleClearLogs = () => {
    setLogs([]);
  };

  // Window Opacity — works in both Tauri and browser dev mode
  const handleOpacityChange = (val) => {
    setOpacityVal(val);
    tauriInvoke('cmd_set_opacity', { opacity: val });
  };

  // Position Mode Switcher
  const handleSetPositionMode = (mode) => {
    setPositionMode(mode);
    tauriInvoke('cmd_set_position_mode', { mode });
  };

  return (
    <div className="hud-container" style={{ opacity: opacityVal }}>
      {/* Top Cyberpunk Header Bar */}
      <header className="hud-header">
        <div className="hud-brand">
          <div className="brand-badge">
            <span className="badge-pulse"></span>
            CLUELY LIVE HUD
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Codebase Context Engine
          </span>
        </div>

        <div className="hud-status-bar">
          {/* Latency Telemetry */}
          {lastLatency !== null && (
            <div className="latency-badge" title="End-to-End AST Retrieval Latency">
              <Zap size={11} color="#00f5a0" />
              <span>{lastLatency}ms</span>
            </div>
          )}

          {/* Codebase Index Badge */}
          <div className="index-counter-badge" title="Symbols in SQLite FTS Index">
            <Layers size={11} color="#00f2fe" />
            <span>{dbStats.total_symbols} AST SYMBOLS</span>
          </div>

          {/* Model Status */}
          <div className="status-pill active">
            <span className="pill-dot"></span>
            <span>QWEN-3.6 / WHISPER</span>
          </div>

          {/* Toggle Logs Button */}
          <button 
            className={`btn-ghost ${showLogs ? 'active' : ''}`}
            onClick={() => setShowLogs(!showLogs)}
            title="Toggle Live Telemetry Logs Dock"
          >
            <Terminal size={14} />
            <span>LOGS</span>
          </button>

          {/* Settings Button */}
          <button className="icon-btn" title="Engine Settings" onClick={() => setIsSettingsOpen(true)}>
            <Settings size={15} />
          </button>

          {/* Position Mode Presets */}
          <div className="position-mode-group">
            <button 
              className={`mode-chip ${positionMode === 'right' ? 'active' : ''}`}
              onClick={() => handleSetPositionMode('right')}
              title="Dock to Right Screen Edge"
            >
              DOCK
            </button>
            <button 
              className={`mode-chip ${positionMode === 'compact' ? 'active' : ''}`}
              onClick={() => handleSetPositionMode('compact')}
              title="Compact Floating Card"
            >
              MINI
            </button>
            <button 
              className={`mode-chip ${positionMode === 'bottom' ? 'active' : ''}`}
              onClick={() => handleSetPositionMode('bottom')}
              title="Bottom Strip Bar"
            >
              STRIP
            </button>
          </div>

          {/* Window Controls */}
          <div className="window-controls">
            <button className="win-btn" onClick={() => tauriInvoke('cmd_minimize_window')}>
              <Minimize2 size={11} />
            </button>
            <button className="win-btn close" onClick={() => tauriInvoke('cmd_close_window')}>
              <X size={11} />
            </button>
          </div>
        </div>
      </header>

      {/* Main HUD Body */}
      <div className="hud-body-split">
        {/* Left / Center Context Stream */}
        <div className="hud-content">
          {/* Real-time Voice & Query Toolbar */}
          <div className="mic-banner">
            <button 
              className={`mic-button ${isListening ? 'listening' : ''}`}
              onClick={handleToggleMic}
              title={isListening ? "Pause Listening" : `Start Voice Capture (${silenceDuration}s pause window)`}
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
            </button>

            <div className="live-transcript-box">
              <div className="transcript-label">
                <span className="pulse-icon"></span>
                <span>{isListening ? `LISTENING (${silenceDuration}s PAUSE WINDOW)...` : "VOICE PROMPT OR QUERY"}</span>
              </div>
              <p className="transcript-text">
                {liveTranscript || (
                  <span style={{ color: 'var(--text-muted)' }}>
                    Speak naturally during your call or click a simulation prompt below...
                  </span>
                )}
              </p>
            </div>

            {isListening && (
              <div className="waveform-container" title="Audio VAD Capture Active">
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
              </div>
            )}
          </div>

          {/* Simulated Speech Test Chips */}
          <div className="simulation-chips">
            <span className="chips-label">SIMULATE VOICE:</span>
            <button 
              className="chip"
              onClick={() => handleQuery("the thing is i was talking about the metrics using LLM as a judge in our evaluator")}
            >
              LLM Judge Metrics
            </button>
            <button 
              className="chip"
              onClick={() => handleQuery("how do we authenticate and verify admin tokens in auth_v2?")}
            >
              Admin Auth Token
            </button>
            <button 
              className="chip"
              onClick={() => handleQuery("where are the attack vector templates seeded into the database?")}
            >
              Seed Attack Vectors
            </button>
            <button 
              className="chip"
              onClick={() => handleQuery("Where is the user token verified?")}
            >
              Verify Token
            </button>
          </div>

          {/* Search Input Bar */}
          <div className="search-bar">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              className="search-input"
              placeholder="Ask anything about the codebase (e.g. 'How does the evaluator calculate hallucination?')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            />
            <button 
              className="search-submit-btn" 
              onClick={() => handleQuery()}
              disabled={isProcessing}
            >
              {isProcessing ? <Sparkles size={14} className="spin" /> : "SEARCH"}
            </button>
          </div>

          {/* Context Cards Stream */}
          <div className="cards-stream">
            {resultsList.length === 0 ? (
              <div className="empty-state">
                <Code2 size={40} color="#00f2fe" style={{ opacity: 0.7, marginBottom: '12px' }} />
                <h3>Engine Ready & Standing By</h3>
                <p>
                  Start speaking or select a test question to see sub-second code context cards appear here in real-time.
                </p>
              </div>
            ) : (
              resultsList.map((res, idx) => {
                const sym = res.best_symbol;
                const isColleague = res.speaker === 'colleague';
                return (
                  <div key={idx} className={`context-card ${isColleague ? 'colleague-question' : 'user-speech'}`}>
                    {/* Header info */}
                    <div className="card-top">
                      <div className="symbol-info">
                        <span className={`speaker-source-badge ${isColleague ? 'colleague' : 'you'}`}>
                          {isColleague ? '❓ COLLEAGUE' : '👤 YOU'}
                        </span>
                        <span className={`symbol-type-badge ${sym?.symbol_type || 'concept'}`}>
                          {sym?.symbol_type?.toUpperCase() || 'CONCEPT'}
                        </span>
                        <h4 className="symbol-name">
                          {sym?.name || "Code Context"}
                        </h4>
                        {res.active_model && (
                          <span className="model-chip-pill">
                            ⚡ {res.active_model}
                          </span>
                        )}
                      </div>

                      <div className="file-location">
                        <FileCode size={12} />
                        <span>{sym?.relative_path || "Repository Reference"}:{sym?.start_line || 1}</span>
                      </div>
                    </div>

                    {/* Subsystem & Trigger tags */}
                    <div className="card-meta-tags">
                      {res.focused_modules && res.focused_modules.length > 0 && (
                        <div className="subsystem-pill">
                          <Layers size={10} color="#00f2fe" />
                          <span>Subsystem: <strong>{res.focused_modules.join(', ')}</strong></span>
                        </div>
                      )}
                      {res.speech_text && (
                        <div className={`spoken-trigger-pill ${isColleague ? 'colleague' : 'you'}`}>
                          <Volume2 size={11} />
                          <span>{isColleague ? 'Heard in meeting:' : 'Triggered by:'} "{res.speech_text}"</span>
                        </div>
                      )}
                    </div>

                    {/* Detected Goal */}
                    {res.intent_summary && (
                      <div className="intent-banner">
                        <span className="intent-icon">🎯</span>
                        <span className="intent-text">{res.intent_summary}</span>
                      </div>
                    )}

                    {/* High-Density Formatted Bullets */}
                    <div className="formatted-bullets-container">
                      {(res.bullets || []).map((bullet, bIdx) => (
                        <div key={bIdx} className="bullet-row">
                          <span className="bullet-indicator">{bIdx + 1}</span>
                          <div className="bullet-body" dangerouslySetInnerHTML={{ 
                            __html: bullet
                              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                              .replace(/`([^`]+)`/g, '<code class="hud-inline-code">$1</code>')
                              .replace(/\(([a-zA-Z0-9_\-\.\/]+:\d+)\)/g, '<span class="hud-path-pill">📂 $1</span>')
                              .replace(/\n-\s+/g, '<br/><span class="sub-bullet-dot">▸</span> ')
                              .replace(/\n\s*(\d+\.)\s+/g, '<br/><span class="sub-bullet-num">$1</span> ')
                          }} />
                        </div>
                      ))}
                    </div>

                    {/* Exact Code AST Snippet */}
                    {sym?.code_snippet && (
                      <div className="code-block-wrapper">
                        <div className="code-header">
                          <span className="code-lang">
                            {sym.language || 'python'} • lines {sym.start_line}-{sym.end_line}
                          </span>
                          <button 
                            className="copy-btn"
                            onClick={() => handleCopy(sym.code_snippet, idx)}
                            title="Copy code to clipboard"
                          >
                            {copiedIndex === idx ? (
                              <>
                                <Check size={12} color="#00f5a0" />
                                <span style={{ color: '#00f5a0' }}>Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy size={12} />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                        <pre className="code-content">
                          <code>{sym.code_snippet}</code>
                        </pre>
                      </div>
                    )}

                    {/* Card Footer Metrics */}
                    <div className="card-footer">
                      <div className="metric-chip highlight">
                        <Zap size={11} color="#00f5a0" />
                        <span>Total: {res.e2e_latency_ms || res.latency_breakdown?.total_ms || 0}ms</span>
                      </div>
                      {res.latency_breakdown?.router_ms !== undefined && (
                        <div className="metric-chip">
                          <Cpu size={11} color="#00f2fe" />
                          <span>Router: {res.latency_breakdown.router_ms}ms</span>
                        </div>
                      )}
                      {res.latency_breakdown?.db_ms !== undefined && (
                        <div className="metric-chip">
                          <Layers size={11} color="#4facfe" />
                          <span>AST DB: {res.latency_breakdown.db_ms}ms</span>
                        </div>
                      )}
                      {res.latency_breakdown?.reason_ms !== undefined && (
                        <div className="metric-chip">
                          <Sparkles size={11} color="#d8b4fe" />
                          <span>AI Reasoner: {res.latency_breakdown.reason_ms}ms</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Dock: Live Telemetry Logs */}
        {showLogs && (
          <aside className="logs-drawer">
            <div className="logs-header">
              <div className="logs-title">
                <Terminal size={14} color="#00f2fe" />
                <span>PIPELINE TELEMETRY LOGS</span>
              </div>
              <div className="logs-controls">
                <button 
                  className="icon-btn" 
                  title="Clear Logs" 
                  onClick={handleClearLogs}
                >
                  <Trash2 size={13} />
                </button>
                <button 
                  className="icon-btn" 
                  title="Close Logs Panel" 
                  onClick={() => setShowLogs(false)}
                >
                  <X size={13} />
                </button>
              </div>
            </div>

            <div className="logs-list">
              {logs.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
                  No logs recorded yet.
                </div>
              ) : (
                logs.map((l, i) => (
                  <div key={i} className="log-entry">
                    <span className="log-time">{l.timestamp}</span>
                    <span className={`log-tag ${l.level}`}>{l.tag}</span>
                    <span className="log-msg">{l.message}</span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </aside>
        )}
      </div>

      {/* Extracted Settings Panel Modal */}
      <SettingsPanel
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiBase={API_BASE}
        currentRepo={currentRepo || repoPathInput}
        onScanRepo={(path, stats) => {
          setCurrentRepo(path);
          if (stats) setDbStats(stats);
        }}
        opacityVal={opacityVal}
        onOpacityChange={handleOpacityChange}
        silenceDuration={silenceDuration}
        onSilenceDurationChange={handleSilenceChange}
      />

      {/* First-Run Setup Wizard */}
      {showOnboarding && (
        <Onboarding
          apiBase={API_BASE}
          onComplete={() => {
            localStorage.setItem('cluely_onboarded', 'true');
            setShowOnboarding(false);
          }}
          onScanRepo={(path, stats) => {
            setCurrentRepo(path);
            if (stats) setDbStats(stats);
          }}
        />
      )}

      {/* Auto-Detected Repo Toast */}
      {detectedRepoToast && (
        <div className="detected-repo-toast">
          <FolderGit2 size={15} color="#00f2fe" />
          <div className="toast-content">
            <span className="toast-title">Active IDE Detected: <strong>{detectedRepoToast.project_hint}</strong></span>
            <span className="toast-sub">{detectedRepoToast.window_title}</span>
          </div>
          <button 
            className="toast-action-btn"
            onClick={() => {
              setRepoPathInput(detectedRepoToast.project_hint);
              setIsSettingsOpen(true);
              setDetectedRepoToast(null);
            }}
          >
            Configure
          </button>
          <button className="toast-close-btn" onClick={() => setDetectedRepoToast(null)}>
            <X size={12} />
          </button>
        </div>
      )}
    </div>
  );
}
