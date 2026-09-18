import React, { useState } from 'react';
import { 
  Key, 
  FolderGit2, 
  Mic, 
  Volume2, 
  Keyboard, 
  Sparkles, 
  Check, 
  ArrowRight, 
  X,
  Layers
} from 'lucide-react';

export default function Onboarding({ onComplete, onScanRepo, apiBase = "http://127.0.0.1:8000" }) {
  const [step, setStep] = useState(1);
  const [activeProvider, setActiveProvider] = useState('gemini');
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [groqKey, setGroqKey] = useState('');
  const [repoPath, setRepoPath] = useState('C:\\Users\\mohdz\\Valiqor\\backend');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const handleSaveKeys = async () => {
    try {
      const payload = {
        active_provider: activeProvider
      };
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();
      if (anthropicKey.trim()) payload.anthropic_api_key = anthropicKey.trim();
      if (groqKey.trim()) payload.groq_api_key = groqKey.trim();

      await fetch(`${apiBase}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setStep(2);
    } catch {
      setStep(2);
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
    <div className="onboarding-backdrop">
      <div className="onboarding-modal">
        {/* Header Progress */}
        <div className="onboarding-progress-header">
          <div className="onboarding-title">
            <Sparkles size={16} color="#00f2fe" />
            <span>Welcome to Cluely — Setup Wizard</span>
          </div>
          <div className="step-dots">
            {[1, 2, 3, 4, 5].map(s => (
              <span key={s} className={`dot ${step === s ? 'active' : ''} ${step > s ? 'done' : ''}`}>
                {step > s ? '✓' : s}
              </span>
            ))}
          </div>
        </div>

        {/* Step 1: API Keys */}
        {step === 1 && (
          <div className="onboarding-step">
            <div className="step-badge">STEP 1 OF 5</div>
            <h3>Configure AI Intelligence</h3>
            <p>Choose your preferred AI Reasoning Engine and configure API credentials.</p>

            <div className="input-group">
              <label>Select Reasoning Engine (User Choice)</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', margin: '4px 0 10px 0' }}>
                {[
                  { id: 'gemini', label: 'Google Gemini' },
                  { id: 'openai', label: 'OpenAI' },
                  { id: 'anthropic', label: 'Anthropic Claude' }
                ].map(item => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setActiveProvider(item.id)}
                    style={{
                      padding: '6px 4px',
                      fontSize: '11px',
                      fontWeight: '700',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      border: activeProvider === item.id ? '1px solid #00f2fe' : '1px solid rgba(255, 255, 255, 0.1)',
                      background: activeProvider === item.id ? 'rgba(0, 242, 254, 0.15)' : 'rgba(0, 0, 0, 0.3)',
                      color: activeProvider === item.id ? '#00f2fe' : '#94a3b8',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
            
            {activeProvider === 'gemini' && (
              <div className="input-group">
                <label>Google Gemini API Key (1M Token Reasoning)</label>
                <input 
                  type="password" 
                  placeholder="AIzaSy... (Gemini 2.5 Flash)" 
                  value={geminiKey}
                  onChange={e => setGeminiKey(e.target.value)}
                />
              </div>
            )}

            {activeProvider === 'openai' && (
              <div className="input-group">
                <label>OpenAI API Key (GPT-4o, o3-mini)</label>
                <input 
                  type="password" 
                  placeholder="sk-proj-..." 
                  value={openaiKey}
                  onChange={e => setOpenaiKey(e.target.value)}
                />
              </div>
            )}

            {activeProvider === 'anthropic' && (
              <div className="input-group">
                <label>Anthropic Claude API Key (Claude 3.5 Haiku / Sonnet)</label>
                <input 
                  type="password" 
                  placeholder="sk-ant-..." 
                  value={anthropicKey}
                  onChange={e => setAnthropicKey(e.target.value)}
                />
              </div>
            )}

            <div className="input-group">
              <label>Groq API Key (Powers Whisper Voice STT &lt;200ms)</label>
              <input 
                type="password" 
                placeholder="gsk_..." 
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
              />
            </div>

            <div className="step-actions">
              <button className="btn-primary" onClick={handleSaveKeys}>
                <span>Save & Continue</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Codebase Scan */}
        {step === 2 && (
          <div className="onboarding-step">
            <div className="step-badge">STEP 2 OF 5</div>
            <h3>Index Your Codebase</h3>
            <p>Cluely builds a 3-level hierarchical AST topology map for instant zero-latency retrieval.</p>

            <div className="input-group">
              <label>Local Repository Absolute Path</label>
              <input 
                type="text" 
                value={repoPath}
                onChange={e => setRepoPath(e.target.value)}
                placeholder="e.g. C:\Users\name\my-project"
              />
            </div>

            <button 
              className="btn-scan" 
              onClick={handleScan}
              disabled={isScanning}
            >
              {isScanning ? (
                <>
                  <Sparkles size={14} className="spin" />
                  <span>Parsing AST Tree & Symbols...</span>
                </>
              ) : (
                <>
                  <Layers size={14} />
                  <span>Scan & Compile Topology</span>
                </>
              )}
            </button>

            {scanResult && (
              <div className="scan-success-pill">
                <Check size={14} color="#00f5a0" />
                <span>Indexed <strong>{scanResult.total_symbols}</strong> AST symbols across {scanResult.total_files} files ({scanResult.elapsed_seconds}s)</span>
              </div>
            )}

            <div className="step-actions">
              <button className="btn-ghost" onClick={() => setStep(1)}>Back</button>
              <button className="btn-primary" onClick={() => setStep(3)}>
                <span>Continue to Audio</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Dual Audio Setup */}
        {step === 3 && (
          <div className="onboarding-step">
            <div className="step-badge">STEP 3 OF 5</div>
            <h3>Two-Way Meeting Audio</h3>
            <p>Cluely captures both your microphone and meeting speakers so you get answers when teammates ask questions.</p>

            <div className="audio-feature-grid">
              <div className="audio-card">
                <div className="audio-card-header">
                  <Mic size={16} color="#00f2fe" />
                  <h4>Microphone (You)</h4>
                </div>
                <p>Captures your questions with real-time Whisper transcription & AST mapping.</p>
                <div className="tag-pill active">Auto-Detected Default Mic</div>
              </div>

              <div className="audio-card">
                <div className="audio-card-header">
                  <Volume2 size={16} color="#fbbf24" />
                  <h4>Meeting Speakers (Colleague)</h4>
                </div>
                <p>Captures Zoom, Teams, and Google Meet audio via WASAPI Loopback / Stereo Mix.</p>
                <div className="tag-pill active">WASAPI Loopback Active</div>
              </div>
            </div>

            <div className="step-actions">
              <button className="btn-ghost" onClick={() => setStep(2)}>Back</button>
              <button className="btn-primary" onClick={() => setStep(4)}>
                <span>Next: Global Hotkey</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Hotkey Demonstration */}
        {step === 4 && (
          <div className="onboarding-step">
            <div className="step-badge">STEP 4 OF 5</div>
            <h3>Instant Global Toggle</h3>
            <p>During meetings, you can instantly toggle Cluely overlay visibility from anywhere.</p>

            <div className="hotkey-demo-box">
              <div className="key-cap">Ctrl</div>
              <span className="plus">+</span>
              <div className="key-cap">Shift</div>
              <span className="plus">+</span>
              <div className="key-cap space">Space</div>
            </div>

            <p className="hint-text">
              Press this combination anytime to show or hide the HUD — even when Zoom or Teams is focused!
            </p>

            <div className="step-actions">
              <button className="btn-ghost" onClick={() => setStep(3)}>Back</button>
              <button className="btn-primary" onClick={() => setStep(5)}>
                <span>Got It!</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Ready */}
        {step === 5 && (
          <div className="onboarding-step ready-step">
            <div className="check-ring">
              <Check size={28} color="#00f5a0" />
            </div>
            <h3>Cluely Is Ready & Standing By</h3>
            <p>Start your meeting or code review. As you or your teammates discuss architecture, context cards will appear automatically.</p>

            <div className="step-actions center">
              <button className="btn-launch" onClick={onComplete}>
                <Sparkles size={16} />
                <span>Launch Desktop HUD Overlay</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
