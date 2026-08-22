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
  Radio,
  Cpu
} from 'lucide-react';

export default function SettingsPanel({ 
  isOpen, 
  onClose, 
  apiBase = "http://127.0.0.1:8000",
  currentRepo,
  onScanRepo,
  opacityVal,
  onOpacityChange,
  silenceDuration,
  onSilenceDurationChange
}) {
  const [groqKey, setGroqKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [repoPath, setRepoPath] = useState(currentRepo || 'C:\\Users\\mohdz\\Valiqor\\backend');
  const [audioDevices, setAudioDevices] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Fetch audio devices from backend
      fetch(`${apiBase}/api/audio/devices`)
        .then(res => res.json())
        .then(data => {
          if (data.devices) setAudioDevices(data.devices);
        })
        .catch(console.error);
    }
  }, [isOpen, apiBase]);

  if (!isOpen) return null;

  const handleSaveConfig = async () => {
    try {
      if (groqKey) {
        await fetch(`${apiBase}/api/config`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ groq_api_key: groqKey, repo_path: repoPath })
        });
      }
      if (silenceDuration) {
        await fetch(`${apiBase}/api/audio/settings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ silence_duration: silenceDuration })
        });
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e) {
      console.error(e);
    }
  };

  const handleScan = async () => {
    if (!repoPath) return;
    setIsScanning(true);
    try {
      const res = await fetch(`${apiBase}/api/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath })
      });
      const data = await res.json();
      if (data.success) {
        setScanResult(data.stats);
        if (onScanRepo) onScanRepo(repoPath, data.stats);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsScanning(false);
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
          {/* Section 1: AI Provider Keys */}
          <div className="settings-section">
            <div className="section-title">
              <Key size={14} color="#00f2fe" />
              <span>AI Provider Configuration</span>
            </div>

            <div className="form-row">
              <label>Google Gemini API Key (1M Token Context & Reasoning)</label>
              <input 
                type="password" 
                placeholder="AQ.Ab8RN6... (Saved in backend/.env)"
                value={geminiKey}
                onChange={e => setGeminiKey(e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Groq API Key (High-Speed Whisper Voice Transcription)</label>
              <input 
                type="password" 
                placeholder="gsk_... (Saved in backend/.env)"
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
              />
            </div>
          </div>

          {/* Section 2: Codebase Indexer */}
          <div className="settings-section">
            <div className="section-title">
              <FolderGit2 size={14} color="#00f5a0" />
              <span>Codebase Repository Target</span>
            </div>

            <div className="form-row">
              <label>Local Repository Path</label>
              <div className="input-btn-group">
                <input 
                  type="text" 
                  value={repoPath}
                  onChange={e => setRepoPath(e.target.value)}
                  placeholder="C:\path\to\codebase"
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

            {scanResult && (
              <div className="scan-success-pill">
                <Check size={12} color="#00f5a0" />
                <span>Indexed {scanResult.total_symbols} symbols from {scanResult.total_files} files ({scanResult.elapsed_seconds}s)</span>
              </div>
            )}
          </div>

          {/* Section 3: Dual Audio Capture & Devices */}
          <div className="settings-section">
            <div className="section-title">
              <Volume2 size={14} color="#fbbf24" />
              <span>Dual Audio Capture & Loopback</span>
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
              <span className="form-hint">Time to wait after speaking before querying the AST index.</span>
            </div>

            <div className="form-row">
              <label>Available Audio Input / Loopback Devices</label>
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

          {/* Section 4: Overlay Appearance */}
          <div className="settings-section">
            <div className="section-title">
              <Sliders size={14} color="#d8b4fe" />
              <span>HUD Overlay Appearance</span>
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
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          {saveSuccess && (
            <span className="save-success-msg">
              <Check size={14} color="#00f5a0" /> Settings updated!
            </span>
          )}
          <button className="btn-ghost" onClick={onClose}>Close</button>
          <button className="btn-primary" onClick={handleSaveConfig}>Save Changes</button>
        </div>
      </div>
    </div>
  );
}
