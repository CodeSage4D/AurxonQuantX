import React, { useState } from 'react';
import { Eye, EyeOff, ShieldCheck, Sparkles, Send } from 'lucide-react';

interface Props {
  onSelectSymbol: (symbol: string) => void;
}

export const ScreenCompanionWidget: React.FC<Props> = ({ onSelectSymbol }) => {
  const [paused, setPaused] = useState(false);
  const [manualText, setManualText] = useState('');
  const [detectedSymbols, setDetectedSymbols] = useState<string[]>(['RELIANCE', 'TCS']);
  const [privacyOk, setPrivacyOk] = useState(true);

  const handleTogglePause = async () => {
    const nextState = !paused;
    setPaused(nextState);
    try {
      await fetch('/api/v1/companion/context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paused: nextState }),
      });
    } catch {
      // Offline fallback
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualText.trim()) return;

    try {
      const res = await fetch('/api/v1/companion/context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manual_text: manualText, paused }),
      });
      const data = await res.json();
      if (data.detected_symbols) {
        setDetectedSymbols(data.detected_symbols);
      }
      setPrivacyOk(data.privacy_guard_passed ?? true);
      setManualText('');
    } catch {
      // Fallback symbol extraction
      const matches = manualText.toUpperCase().match(/\b[A-Z]{3,10}\b/g) || [];
      setDetectedSymbols(matches.slice(0, 5));
      setManualText('');
    }
  };

  return (
    <div className="glass-card" style={{ marginTop: '20px' }}>
      <div className="card-header">
        <div className="card-title">
          {paused ? (
            <EyeOff size={18} style={{ color: 'var(--status-uncertain)' }} />
          ) : (
            <Eye size={18} style={{ color: 'var(--accent-cyan)' }} />
          )}
          <span>Live Market Companion (OCR / Context)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            className="chip-btn"
            onClick={handleTogglePause}
            style={{
              borderColor: paused ? 'var(--status-uncertain)' : 'var(--status-verified)',
              color: paused ? 'var(--status-uncertain)' : 'var(--status-verified)',
            }}
          >
            {paused ? 'PAUSED' : 'ACTIVE / CAPTURING'}
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Privacy Banner */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: privacyOk ? 'hsla(145, 80%, 42%, 0.1)' : 'hsla(0, 85%, 60%, 0.1)', border: `1px solid ${privacyOk ? 'var(--status-verified)' : 'var(--status-contradicted)'}`, borderRadius: 'var(--radius-sm)', marginBottom: '14px', fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: privacyOk ? 'var(--status-verified)' : 'var(--status-contradicted)' }}>
            <ShieldCheck size={14} />
            <span>Zero-Credential Ingestion Guard Active (OTPs & PII Auto-Redacted)</span>
          </div>
          <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>TESSERACT 5 READY</span>
        </div>

        {/* Detected Symbols */}
        <div style={{ marginBottom: '14px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
            Detected Instruments in View (Click to Research):
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {detectedSymbols.length > 0 ? (
              detectedSymbols.map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => onSelectSymbol(sym)}
                  className="companion-tag"
                  style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Sparkles size={11} /> {sym}
                </button>
              ))
            ) : (
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>No symbols currently detected.</span>
            )}
          </div>
        </div>

        {/* Manual Context Input */}
        <form onSubmit={handleManualSubmit} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            className="text-input"
            style={{ padding: '8px 10px', fontSize: '0.8rem' }}
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            placeholder="Paste text/symbol when site blocks OCR..."
            disabled={paused}
          />
          <button
            type="submit"
            className="chip-btn"
            style={{ padding: '0 14px', borderColor: 'var(--accent-cyan)', color: 'var(--accent-cyan)' }}
            disabled={paused || !manualText.trim()}
          >
            <Send size={14} />
          </button>
        </form>
      </div>
    </div>
  );
};
