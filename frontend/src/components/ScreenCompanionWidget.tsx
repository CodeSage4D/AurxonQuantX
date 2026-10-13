import React, { useState, useEffect, useRef } from 'react';
import {
  Eye,
  EyeOff,
  ShieldCheck,
  Sparkles,
  Send,
  Upload,
  RotateCcw,
} from 'lucide-react';

interface Props {
  onSelectSymbol: (symbol: string) => void;
}

interface TelemetryMetrics {
  sample_count: number;
  total_invocations: number;
  cache_hits: number;
  duplicates_skipped: number;
  p50_ms: number;
  p95_ms: number;
  ocr_binary_available: boolean;
  is_paused: boolean;
}

interface PipelineBreakdown {
  change_detection_ms?: number;
  preprocessing_ms?: number;
  ocr_execution_ms?: number;
  classification_ms?: number;
  total_pipeline_ms?: number;
  cache_saved?: boolean;
}

export const ScreenCompanionWidget: React.FC<Props> = ({ onSelectSymbol }) => {
  const [paused, setPaused] = useState(false);
  const [manualText, setManualText] = useState('');
  const [detectedSymbols, setDetectedSymbols] = useState<string[]>(['RELIANCE', 'TCS']);
  const [privacyOk, setPrivacyOk] = useState(true);
  const [isDuplicate, setIsDuplicate] = useState(false);
  const [lastTelemetry, setLastTelemetry] = useState<PipelineBreakdown | null>(null);
  const [metrics, setMetrics] = useState<TelemetryMetrics | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchTelemetry = async () => {
    try {
      const res = await fetch('/api/v1/companion/telemetry');
      if (res.ok) {
        setMetrics(await res.json());
      }
    } catch {
      // Offline fallback
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  const handleTogglePause = async () => {
    const nextState = !paused;
    setPaused(nextState);
    try {
      await fetch('/api/v1/companion/context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paused: nextState }),
      });
      fetchTelemetry();
    } catch {
      // Offline fallback
    }
  };

  const handleClear = async () => {
    try {
      await fetch('/api/v1/companion/clear', { method: 'POST' });
      setLastTelemetry(null);
      setIsDuplicate(false);
      fetchTelemetry();
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
      setIsDuplicate(data.is_duplicate ?? false);
      if (data.telemetry) setLastTelemetry(data.telemetry);
      setManualText('');
      fetchTelemetry();
    } catch {
      const matches = manualText.toUpperCase().match(/\b[A-Z]{3,10}\b/g) || [];
      setDetectedSymbols(matches.slice(0, 5));
      setManualText('');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    try {
      const res = await fetch('/api/v1/companion/upload', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        if (data.detected_symbols) setDetectedSymbols(data.detected_symbols);
        setPrivacyOk(data.privacy_guard_passed ?? true);
        setIsDuplicate(data.is_duplicate ?? false);
        if (data.telemetry) setLastTelemetry(data.telemetry);
        fetchTelemetry();
      }
    } catch (err) {
      console.error('Frame upload failed:', err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="glass-card" style={{ marginTop: '20px' }}>
      <div className="card-header">
        <div className="card-title">
          {paused ? (
            <EyeOff size={16} style={{ color: 'var(--status-uncertain)' }} />
          ) : (
            <Eye size={16} style={{ color: 'var(--accent-blue)' }} />
          )}
          <span>Live Market Companion & Fast OCR</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            className="chip-btn"
            onClick={handleClear}
            title="Reset OCR cache state"
            style={{ fontSize: '0.72rem', padding: '3px 8px' }}
          >
            <RotateCcw size={11} /> Reset
          </button>
          <button
            type="button"
            className="chip-btn"
            onClick={handleTogglePause}
            style={{
              borderColor: paused ? 'var(--status-uncertain)' : 'var(--status-verified)',
              color: paused ? 'var(--status-uncertain)' : 'var(--status-verified)',
              fontSize: '0.72rem',
              padding: '3px 10px',
            }}
          >
            {paused ? 'PAUSED' : 'ACTIVE / CAPTURING'}
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Privacy Banner */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '7px 12px',
            background: privacyOk ? 'var(--status-verified-bg)' : 'var(--status-contradicted-bg)',
            border: `1px solid ${privacyOk ? 'var(--status-verified)' : 'var(--status-contradicted)'}`,
            borderRadius: 'var(--radius-sm)',
            marginBottom: '12px',
            fontSize: '0.73rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: privacyOk ? 'var(--status-verified)' : 'var(--status-contradicted)' }}>
            <ShieldCheck size={13} />
            <span>Privacy Guard Active (OTPs & Credentials Sanitized)</span>
          </div>
          <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>TESSERACT 5 (LSTM)</span>
        </div>

        {/* Live Latency Telemetry Breakdown */}
        {lastTelemetry && (
          <div
            style={{
              padding: '8px 12px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '12px',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-dim)' }}>PIPELINE TELEMETRY:</span>
              <span style={{ color: isDuplicate ? 'var(--status-uncertain)' : 'var(--accent-blue)', fontWeight: 700 }}>
                {isDuplicate ? '⚡ CACHE HIT (DUPLICATE SKIPPED)' : `TOTAL: ${lastTelemetry.total_pipeline_ms} ms`}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
              <span>Hash: {lastTelemetry.change_detection_ms ?? 0}ms</span>
              <span>OCR: {lastTelemetry.ocr_execution_ms ?? 0}ms</span>
              <span>Classify: {lastTelemetry.classification_ms ?? 0}ms</span>
            </div>
          </div>
        )}

        {/* Aggregated Benchmarks */}
        {metrics && metrics.sample_count > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: '12px', fontFamily: 'var(--font-mono)' }}>
            <span>Rolling p50: <strong style={{ color: 'var(--text-main)' }}>{metrics.p50_ms}ms</strong></span>
            <span>p95: <strong style={{ color: 'var(--text-main)' }}>{metrics.p95_ms}ms</strong></span>
            <span>Cache Hits: <strong style={{ color: 'var(--accent-blue)' }}>{metrics.cache_hits}</strong></span>
          </div>
        )}

        {/* Detected Symbols */}
        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
            Detected Instruments in Active View:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {detectedSymbols.length > 0 ? (
              detectedSymbols.map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => onSelectSymbol(sym)}
                  className="companion-tag"
                  style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem' }}
                >
                  <Sparkles size={11} style={{ color: 'var(--accent-blue)' }} /> {sym}
                </button>
              ))
            ) : (
              <span style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>No symbols currently detected.</span>
            )}
          </div>
        </div>

        {/* Upload Frame or Manual Context */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <button
            type="button"
            className="chip-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={paused || isUploading}
            style={{ flexShrink: 0, padding: '7px 11px', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <Upload size={13} /> {isUploading ? 'OCR...' : 'Test Image'}
          </button>

          <form onSubmit={handleManualSubmit} style={{ display: 'flex', gap: '6px', flex: 1 }}>
            <input
              type="text"
              className="text-input"
              style={{ padding: '7px 10px', fontSize: '0.8rem' }}
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder="Paste text / symbol directly..."
              disabled={paused}
            />
            <button
              type="submit"
              className="chip-btn"
              style={{ padding: '0 12px', borderColor: 'var(--accent-blue)', color: 'var(--accent-blue)' }}
              disabled={paused || !manualText.trim()}
            >
              <Send size={13} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
