import React, { useState, useEffect } from 'react';
import { 
  X, 
  Settings, 
  Key, 
  FolderGit2, 
  Sliders, 
  Volume2, 
  Layers, 
  Sparkles, 
  Check, 
  Cpu, 
  Shield, 
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Sun,
  Moon
} from 'lucide-react';

const FALLBACK_PROVIDERS = [
  {
    id: "gemini",
    name: "Google Gemini",
    default_model: "gemini-3.5-flash",
    configured: true,
    models: [
      { id: "gemini-3.5-flash", name: "Gemini 3.5 Flash (Recommended)", tag: "Active • Flagship 3.5" },
      { id: "gemini-3.5-flash-lite", name: "Gemini 3.5 Flash Lite", tag: "Active • Ultra-Low Latency" },
      { id: "gemini-3.6-flash", name: "Gemini 3.6 Flash", tag: "Active • High Precision" },
      { id: "gemini-3.7-flash", name: "Gemini 3.7 Flash", tag: "Active • Next-Gen" }
    ]
  },
  {
    id: "openai",
    name: "OpenAI",
    default_model: "gpt-4o-mini",
    configured: false,
    models: [
      { id: "gpt-4o-mini", name: "GPT-4o Mini (Recommended)", tag: "Fast & Accurate" },
      { id: "gpt-4o", name: "GPT-4o", tag: "Flagship" },
      { id: "o3-mini", name: "o3-mini", tag: "Code Reasoning" },
      { id: "o1-mini", name: "o1-mini", tag: "Reasoning" }
    ]
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    default_model: "claude-3-5-haiku-latest",
    configured: false,
    models: [
      { id: "claude-3-5-haiku-latest", name: "Claude 3.5 Haiku (Recommended)", tag: "Sub-300ms" },
      { id: "claude-3-5-sonnet-latest", name: "Claude 3.5 Sonnet", tag: "Top Quality" },
      { id: "claude-3-7-sonnet-latest", name: "Claude 3.7 Sonnet", tag: "Hybrid Reasoning" }
    ]
  }
];

export default function SettingsPanel({ 
  isOpen, 
  onClose, 
  apiBase = "http://127.0.0.1:8000",
  currentRepo,
  onScanRepo,
  opacityVal,
  onOpacityChange,
  silenceDuration,
  onSilenceDurationChange,
  stealthMode,
  onToggleStealth,
  onProviderChange,
  theme = 'dark',
  onThemeChange
}) {
  const [providers, setProviders] = useState(FALLBACK_PROVIDERS);
  const [activeProvider, setActiveProvider] = useState("gemini");
  const [activeModel, setActiveModel] = useState("gemini-3.5-flash");
  const [isGroqConfigured, setIsGroqConfigured] = useState(true);
  const [showAllKeys, setShowAllKeys] = useState(false);

  // API Key Inputs
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [groqKey, setGroqKey] = useState('');

  const [repoPath, setRepoPath] = useState(currentRepo || 'C:\\Users\\mohdz\\Valiqor\\backend');
  const [audioDevices, setAudioDevices] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load providers and audio devices on open
  useEffect(() => {
    if (isOpen) {
      fetch(`${apiBase}/api/providers`)
        .then(res => res.json())
        .then(data => {
          if (data.providers) setProviders(data.providers);
          if (data.active_provider) setActiveProvider(data.active_provider);
          if (data.active_model) setActiveModel(data.active_model);
          if (data.groq_configured !== undefined) setIsGroqConfigured(data.groq_configured);
        })
        .catch(console.error);

      fetch(`${apiBase}/api/audio/devices`)
        .then(res => res.json())
        .then(data => {
          if (data.devices) setAudioDevices(data.devices);
        })
        .catch(console.error);
    }
  }, [isOpen, apiBase]);

  if (!isOpen) return null;

  const currentProviderObj = providers.find(p => p.id === activeProvider) || providers[0];
  const availableModels = currentProviderObj?.models || [];

  const handleProviderSelect = (provId) => {
    setActiveProvider(provId);
    const targetProv = providers.find(p => p.id === provId);
    if (targetProv && targetProv.default_model) {
      setActiveModel(targetProv.default_model);
    }
  };

  const handleSaveConfig = async () => {
    try {
      const payload = {
        active_provider: activeProvider,
        active_model: activeModel,
        repo_path: repoPath || undefined
      };

      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();
      if (anthropicKey.trim()) payload.anthropic_api_key = anthropicKey.trim();
      if (groqKey.trim()) payload.groq_api_key = groqKey.trim();

      const res = await fetch(`${apiBase}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const resData = await res.json();
      if (resData.providers_state?.providers) {
        setProviders(resData.providers_state.providers);
        if (resData.providers_state.groq_configured !== undefined) {
          setIsGroqConfigured(resData.providers_state.groq_configured);
        }
      }

      if (silenceDuration) {
        await fetch(`${apiBase}/api/audio/settings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ silence_duration: silenceDuration })
        });
      }

      if (onProviderChange) {
        onProviderChange(activeProvider, activeModel);
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e) {
      console.error("Save config error:", e);
    }
  };

  const handleScan = async () => {
    if (!repoPath) return;
    setIsScanning(true);
    setScanError(null);
    setScanResult(null);
    try {
      const res = await fetch(`${apiBase}/api/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath })
      });
      const data = await res.json();
      if (data.success) {
        setScanResult(data.stats);
        const resolved = data.current_repo || data.stats?.resolved_path || repoPath;
        setRepoPath(resolved);
        if (onScanRepo) onScanRepo(resolved, data.stats);
      } else {
        setScanError(data.error || "Indexing failed. Please check the path.");
      }
    } catch (e) {
      setScanError(`Connection error: ${e.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  const getProviderIcon = (id) => {
    switch (id) {
      case "gemini":
        return <Sparkles size={13} />;
      case "openai":
        return <Cpu size={13} />;
      case "anthropic":
        return <Layers size={13} />;
      default:
        return <Sparkles size={13} />;
    }
  };

  return (
    <div className="settings-modal-backdrop" onClick={onClose}>
      <div className="settings-modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <Settings size={18} color="#00f2fe" />
            <h3>Cluely Engine Preferences</h3>
          </div>
          <button className="icon-btn close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          {/* Section 1: AI Reasoning Engine Selection */}
          <div className="settings-section">
            <div className="section-title">
              <Sparkles size={14} color="#00f2fe" />
              <span>Reasoning Engine</span>
            </div>

            {/* Clean Segmented 3-Way Selector */}
            <div className="engine-tabs">
              {providers.map(p => {
                const isActive = activeProvider === p.id;
                return (
                  <button 
                    key={p.id}
                    type="button"
                    className={`engine-tab ${isActive ? 'active' : ''}`}
                    onClick={() => handleProviderSelect(p.id)}
                  >
                    {getProviderIcon(p.id)}
                    <span>{p.name}</span>
                  </button>
                );
              })}
            </div>

            {/* Model Dropdown */}
            <div className="form-row" style={{ marginTop: '8px' }}>
              <label>Model</label>
              <select 
                className="model-select"
                value={activeModel}
                onChange={e => setActiveModel(e.target.value)}
              >
                {availableModels.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Section 2: API Credentials */}
          <div className="settings-section">
            <div className="section-title">
              <Key size={14} color="#00f2fe" />
              <span>API Credentials</span>
            </div>

            {/* 1. Groq (Mandatory for Voice) */}
            <div className="form-row">
              <div className="key-status-label">
                <label>
                  Groq API Key <span style={{ color: '#ff6b4a', fontSize: '10px' }}>(Required for Whisper Voice STT)</span>
                </label>
                {isGroqConfigured ? (
                  <span className="clean-tag ready">Set</span>
                ) : (
                  <span className="clean-tag required">Required</span>
                )}
              </div>
              <input 
                type="password" 
                placeholder="gsk_... (Whisper Large-v3 speech recognition)"
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
              />
            </div>

            {/* 2. Active Reasoning Key (User Choice) */}
            <div className="form-row">
              <div className="key-status-label">
                <label>
                  {currentProviderObj.name} API Key <span style={{ color: '#00f2fe', fontSize: '10px' }}>(Active Reasoner)</span>
                </label>
                {currentProviderObj.configured && (
                  <span className="clean-tag ready">Set</span>
                )}
              </div>
              <input 
                type="password" 
                placeholder={
                  activeProvider === 'gemini' 
                    ? "AIzaSy... (Google Gemini)" 
                    : activeProvider === 'openai' 
                      ? "sk-proj-... (OpenAI)" 
                      : "sk-ant-... (Anthropic Claude)"
                }
                value={
                  activeProvider === 'gemini' 
                    ? geminiKey 
                    : activeProvider === 'openai' 
                      ? openaiKey 
                      : anthropicKey
                }
                onChange={e => {
                  if (activeProvider === 'gemini') setGeminiKey(e.target.value);
                  else if (activeProvider === 'openai') setOpenaiKey(e.target.value);
                  else setAnthropicKey(e.target.value);
                }}
              />
            </div>

            {/* Optional other keys toggle */}
            <div style={{ marginTop: '2px' }}>
              <button 
                type="button"
                onClick={() => setShowAllKeys(!showAllKeys)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#64748b',
                  fontSize: '11px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '2px 0'
                }}
              >
                {showAllKeys ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                <span>{showAllKeys ? "Hide other engine keys" : "+ Configure other engine keys (optional)"}</span>
              </button>
            </div>

            {showAllKeys && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                {providers.filter(p => p.id !== activeProvider).map(p => (
                  <div key={p.id} className="form-row">
                    <div className="key-status-label">
                      <label style={{ color: '#94a3b8', fontSize: '11px' }}>{p.name} API Key (Optional)</label>
                      {p.configured && <span className="clean-tag ready">Set</span>}
                    </div>
                    <input 
                      type="password"
                      placeholder={p.id === 'gemini' ? 'AIzaSy...' : p.id === 'openai' ? 'sk-proj-...' : 'sk-ant-...'}
                      value={p.id === 'gemini' ? geminiKey : p.id === 'openai' ? openaiKey : anthropicKey}
                      onChange={e => {
                        if (p.id === 'gemini') setGeminiKey(e.target.value);
                        else if (p.id === 'openai') setOpenaiKey(e.target.value);
                        else setAnthropicKey(e.target.value);
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 3: Codebase Indexer */}
          <div className="settings-section">
            <div className="section-title">
              <FolderGit2 size={14} color="#00f5a0" />
              <span>Codebase Repository Target</span>
            </div>

            <div className="form-row">
              <label>Local Path, .ZIP File, or Public GitHub URL</label>
              <div className="input-btn-group">
                <input 
                  type="text" 
                  value={repoPath}
                  onChange={e => setRepoPath(e.target.value)}
                  placeholder="e.g. C:\project, project.zip, or https://github.com/owner/repo"
                />
                <button 
                  className="btn-primary" 
                  onClick={handleScan}
                  disabled={isScanning}
                >
                  {isScanning ? <Sparkles size={13} className="spin" /> : "RE-SCAN"}
                </button>
              </div>
            </div>

            {scanError && (
              <div className="scan-error-pill">
                <AlertCircle size={13} color="#ef4444" />
                <span>{scanError}</span>
              </div>
            )}

            {scanResult && (
              <div className="scan-success-pill">
                <Check size={12} color="#00f5a0" />
                <span>Indexed {scanResult.total_symbols} symbols from {scanResult.total_files} files ({scanResult.elapsed_seconds}s)</span>
              </div>
            )}
          </div>

          {/* Section 4: Dual Audio Capture & Devices */}
          <div className="settings-section">
            <div className="section-title">
              <Volume2 size={14} color="#fbbf24" />
              <span>Audio Pause & Devices</span>
            </div>

            <div className="form-row">
              <label>Speech Pause Window: <strong>{silenceDuration}s</strong></label>
              <input 
                type="range" 
                min="0.8" 
                max="3.5" 
                step="0.1" 
                value={silenceDuration}
                onChange={e => onSilenceDurationChange(parseFloat(e.target.value))}
              />
            </div>

            <div className="form-row">
              <label>Audio Devices</label>
              <div className="device-list-box">
                {audioDevices.filter(d => d.max_input_channels > 0).map(d => (
                  <div key={d.id} className="device-item">
                    <span className="device-dot">●</span>
                    <span className="device-name">[{d.id}] {d.name}</span>
                    <span className="device-api">{d.host_api}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 5: Overlay Appearance & Stealth */}
          <div className="settings-section">
            <div className="section-title">
              <Shield size={14} color="#00f5a0" />
              <span>Screen Sharing Invisibility (Stealth)</span>
            </div>

            <div className="form-row">
              <div className="stealth-toggle-row">
                <div className="stealth-toggle-info">
                  <label>Hide Window from Screen Sharing: <strong>{stealthMode ? "ENABLED" : "DISABLED"}</strong></label>
                  <span className="form-hint">
                    Cluely remains visible to you, but invisible to Zoom, Teams & Google Meet.
                  </span>
                </div>
                <button 
                  className={`btn-stealth-switch ${stealthMode ? 'active' : ''}`}
                  onClick={onToggleStealth}
                >
                  {stealthMode ? "STEALTH ON" : "STEALTH OFF"}
                </button>
              </div>
            </div>
          </div>

          {/* Section 6: Interface Theme */}
          <div className="settings-section">
            <div className="section-title">
              {theme === 'dark' ? <Moon size={14} color="#38bdf8" /> : <Sun size={14} color="#f59e0b" />}
              <span>Interface Theme</span>
            </div>

            <div className="form-row">
              <label>Appearance Mode</label>
              <div className="theme-toggle-group">
                <button 
                  className={`theme-btn ${theme === 'dark' ? 'active' : ''}`}
                  onClick={() => onThemeChange && onThemeChange('dark')}
                  type="button"
                >
                  <Moon size={13} />
                  <span>Dark Mode</span>
                </button>
                <button 
                  className={`theme-btn ${theme === 'light' ? 'active' : ''}`}
                  onClick={() => onThemeChange && onThemeChange('light')}
                  type="button"
                >
                  <Sun size={13} />
                  <span>Light Mode</span>
                </button>
              </div>
            </div>
          </div>

          {/* Section 7: Overlay Transparency */}
          <div className="settings-section">
            <div className="section-title">
              <Sliders size={14} color="#d8b4fe" />
              <span>Window Transparency</span>
            </div>

            <div className="form-row">
              <label>Window Transparency: <strong>{Math.round(opacityVal * 100)}%</strong></label>
              <input 
                type="range" 
                min="0.3" 
                max="1.0" 
                step="0.05" 
                value={opacityVal}
                onChange={e => onOpacityChange(parseFloat(e.target.value))}
              />
              <span className="form-hint">
                Real see-through window glass over other desktop applications and code editors.
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          {saveSuccess && (
            <span className="save-success-msg">
              <Check size={14} color="#00f5a0" /> Saved!
            </span>
          )}
          <button className="btn-ghost" onClick={onClose}>Close</button>
          <button className="btn-primary" onClick={handleSaveConfig}>Save Changes</button>
        </div>
      </div>
    </div>
  );
}
