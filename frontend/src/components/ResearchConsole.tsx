import React, { useState } from 'react';
import { ResearchObjective, StreamEvent } from '../types';
import { Search, Play, Cpu, Layers, Sparkles } from 'lucide-react';

interface Props {
  onRunResearch: (objective: ResearchObjective, modelKey: string) => void;
  isLoading: boolean;
  activeEvent: StreamEvent | null;
}

const POPULAR_TICKERS = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'TATAMOTORS', 'ITC', 'BAJFINANCE'];

export const ResearchConsole: React.FC<Props> = ({ onRunResearch, isLoading, activeEvent }) => {
  const [ticker, setTicker] = useState('RELIANCE');
  const [query, setQuery] = useState('Analyze operating cash flow durability, retail capex, and intrinsic margin of safety.');
  const [horizon, setHorizon] = useState('long_term');
  const [riskTolerance, setRiskTolerance] = useState('moderate');
  const [modelKey, setModelKey] = useState('aurxon_offline:heuristic_evidence_v1');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim() || isLoading) return;

    onRunResearch(
      {
        ticker: ticker.trim().toUpperCase(),
        query,
        asset_class: 'equity',
        horizon,
        risk_tolerance: riskTolerance,
      },
      modelKey
    );
  };

  return (
    <div className="glass-card" style={{ height: 'fit-content' }}>
      <div className="card-header">
        <div className="card-title">
          <Search size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span>Evidence-Loop Research Console</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} style={{ color: 'var(--accent-gold)' }} />
          <span style={{ fontSize: '0.7rem', color: 'var(--accent-gold)', fontFamily: 'var(--font-mono)' }}>
            INDIAN MARKETS
          </span>
        </div>
      </div>

      <div className="card-body">
        <form onSubmit={handleSubmit}>
          {/* Ticker Input */}
          <div className="form-group">
            <label className="form-label">NSE / BSE Instrument Ticker</label>
            <div className="ticker-input-wrapper">
              <input
                type="text"
                className="text-input ticker-input"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="RELIANCE, TCS, INFY..."
                disabled={isLoading}
                required
              />
              <span className="suffix-tag">.NS / .BO</span>
            </div>
            {/* Quick Chips */}
            <div className="chips-row">
              {POPULAR_TICKERS.map((sym) => (
                <button
                  type="button"
                  key={sym}
                  className="chip-btn"
                  onClick={() => setTicker(sym)}
                  disabled={isLoading}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>

          {/* Research Query */}
          <div className="form-group">
            <label className="form-label">Research Hypothesis / Question</label>
            <textarea
              className="text-input"
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Formulate specific research objective..."
              disabled={isLoading}
              required
              style={{ resize: 'vertical' }}
            />
          </div>

          {/* Model Adapter */}
          <div className="form-group">
            <label className="form-label">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu size={14} /> Intelligence Model Adapter
              </span>
            </label>
            <select
              className="select-input"
              value={modelKey}
              onChange={(e) => setModelKey(e.target.value)}
              disabled={isLoading}
            >
              <option value="aurxon_offline:heuristic_evidence_v1">
                AURXON Heuristic Engine (100% Offline / Verified Deterministic)
              </option>
              <option value="groq:llama-3.3-70b-versatile">
                Groq Sub-Second Cloud (Llama 3.3 70B)
              </option>
              <option value="openai:gpt-4o">
                OpenAI GPT-4o (Deep Reasoning)
              </option>
            </select>
          </div>

          {/* Horizon & Risk */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label className="form-label">Investment Horizon</label>
              <select
                className="select-input"
                value={horizon}
                onChange={(e) => setHorizon(e.target.value)}
                disabled={isLoading}
              >
                <option value="short_term">Short Term (1-3 Mo)</option>
                <option value="medium_term">Medium Term (6-18 Mo)</option>
                <option value="long_term">Long Term (3-5+ Yrs)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Risk Tolerance</label>
              <select
                className="select-input"
                value={riskTolerance}
                onChange={(e) => setRiskTolerance(e.target.value)}
                disabled={isLoading}
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
          </div>

          {/* Action Button */}
          <button type="submit" className="btn-primary" disabled={isLoading}>
            {isLoading ? (
              <>
                <Layers size={16} className="animate-spin" />
                Executing Evidence-Loop...
              </>
            ) : (
              <>
                <Play size={16} /> Run Research Pipeline
              </>
            )}
          </button>
        </form>

        {/* Live SSE Stream Progression Indicator */}
        {isLoading && activeEvent && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              <span>STAGE: {activeEvent.step}</span>
              <span>{activeEvent.progress_pct}%</span>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar-fill" style={{ width: `${activeEvent.progress_pct}%` }} />
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: '4px' }}>
              {activeEvent.data?.status || 'Processing concurrent evidence queries...'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
