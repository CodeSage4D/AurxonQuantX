import React, { useState } from 'react';
import {
  ResearchFinding,
  ResearchObjective,
  StreamEvent,
} from './types';
import { ResearchConsole } from './components/ResearchConsole';
import { ValuationCard } from './components/ValuationCard';
import { EvidenceFeed } from './components/EvidenceFeed';
import { ScreenCompanionWidget } from './components/ScreenCompanionWidget';
import { AuditLedgerModal } from './components/AuditLedgerModal';
import {
  Activity,
  Shield,
  FileCheck2,
  Lock,
  Compass,
  AlertOctagon,
  Scale,
} from 'lucide-react';

export const App: React.FC = () => {
  const [finding, setFinding] = useState<ResearchFinding | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeEvent, setActiveEvent] = useState<StreamEvent | null>(null);
  const [showLedger, setShowLedger] = useState(false);

  const handleRunResearch = async (objective: ResearchObjective, modelKey: string) => {
    setIsLoading(true);
    setActiveEvent(null);

    try {
      const response = await fetch(`/api/v1/research/stream?model_key=${encodeURIComponent(modelKey)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(objective),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const chunk of lines) {
            const dataLine = chunk
              .split('\n')
              .find((l) => l.startsWith('data: '));

            if (dataLine) {
              const jsonStr = dataLine.replace('data: ', '').trim();
              try {
                const parsed: StreamEvent = JSON.parse(jsonStr);
                setActiveEvent(parsed);

                if (parsed.step === 'RESEARCH_COMPLETE' && parsed.data?.finding) {
                  setFinding(parsed.data.finding as ResearchFinding);
                }
              } catch {
                // Ignore parse errors on keep-alives
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('Research streaming failed, attempting sync fallback:', err);
      try {
        const syncRes = await fetch(`/api/v1/research/sync?model_key=${encodeURIComponent(modelKey)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(objective),
        });
        if (syncRes.ok) {
          const syncData = await syncRes.json();
          setFinding(syncData);
        }
      } catch (syncErr) {
        console.error('Sync fallback failed:', syncErr);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectSymbol = (symbol: string) => {
    // Populate research console ticker and run
    handleRunResearch(
      {
        ticker: symbol,
        query: `Analyze operating margin durability and intrinsic DCF margin of safety for ${symbol}.`,
        asset_class: 'equity',
        horizon: 'long_term',
        risk_tolerance: 'moderate',
      },
      'aurxon_offline:heuristic_evidence_v1'
    );
  };

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <header className="top-nav">
        <div className="brand-section">
          <div className="brand-logo">
            <Activity size={20} color="#ffffff" />
          </div>
          <div>
            <div className="brand-title">AURXON</div>
          </div>
          <span className="brand-badge">EVIDENCE-FIRST HUB</span>
        </div>

        <div className="nav-controls">
          <div className="nav-pill active">
            <div className="nav-pill-dot" />
            <span>CORE BACKEND READY</span>
          </div>

          <div className="nav-pill" style={{ borderColor: 'hsla(0, 85%, 60%, 0.3)', color: 'hsl(0, 85%, 70%)' }}>
            <Lock size={12} />
            <span>REAL ORDERS: LOCKED</span>
          </div>

          <button
            type="button"
            className="chip-btn"
            onClick={() => setShowLedger(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px' }}
          >
            <FileCheck2 size={14} /> Audit Ledger
          </button>
        </div>
      </header>

      {/* Main Dashboard Grid */}
      <main className="dashboard-grid">
        {/* Left Column: Console & Live Screen Companion */}
        <section>
          <ResearchConsole
            onRunResearch={handleRunResearch}
            isLoading={isLoading}
            activeEvent={activeEvent}
          />

          <ScreenCompanionWidget onSelectSymbol={handleSelectSymbol} />
        </section>

        {/* Right Column: Research Dossier & Evidence */}
        <section>
          {finding ? (
            <div>
              {/* Recommendation Banner */}
              <div className={`recommendation-banner rec-${finding.recommendation}`}>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em' }}>
                    AURXON EVIDENCE DECISION
                  </div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '2px' }}>
                    {finding.recommendation} — {finding.objective.ticker}
                  </div>
                </div>

                <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                  <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>EVIDENCE QUALITY</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                    {Math.round(finding.overall_evidence_score * 100)}%
                  </div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.75 }}>
                    UNCERTAINTY: {finding.uncertainty_level}
                  </div>
                </div>
              </div>

              {/* Narrative Synthesis */}
              <div className="glass-card" style={{ marginBottom: '20px' }}>
                <div className="card-header">
                  <div className="card-title">
                    <Compass size={18} style={{ color: 'var(--accent-cyan)' }} />
                    <span>Executive Research Synthesis</span>
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    AUDIT ID: {finding.audit_id}
                  </div>
                </div>
                <div className="card-body">
                  <p style={{ fontSize: '0.92rem', lineHeight: 1.6, color: 'var(--text-main)' }}>
                    {finding.synthesis_summary}
                  </p>
                </div>
              </div>

              {/* Adversarial Bear Case */}
              <div className="adversarial-box">
                <div className="adversarial-title">
                  <AlertOctagon size={16} /> Adversarial Interrogation & Bear-Case Stress Test
                </div>
                <div style={{ fontSize: '0.85rem', color: '#ffb3b3', marginBottom: '10px' }}>
                  {finding.counter_thesis.bear_case_summary}
                </div>
                <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {finding.counter_thesis.key_vulnerabilities.map((v, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {v}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Deterministic Valuation Card */}
              <ValuationCard valuation={finding.valuation} />

              {/* Evidence Claims Feed */}
              <EvidenceFeed claims={finding.claims} />
            </div>
          ) : (
            <div className="glass-card" style={{ padding: '60px 40px', textAlign: 'center' }}>
              <Scale size={48} style={{ margin: '0 auto 16px', color: 'var(--accent-cyan)', opacity: 0.7 }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>
                AURXON Quantitative & Evidence Research Engine
              </h2>
              <p style={{ color: 'var(--text-muted)', maxWidth: '540px', margin: '0 auto 24px', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Founder-operated research hub for Indian markets. Select a company ticker from the left console or companion context to initiate the 10-step Evidence-Loop.
              </p>
              <div style={{ display: 'inline-flex', gap: '12px' }}>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ width: 'auto', padding: '10px 20px' }}
                  onClick={() => handleSelectSymbol('RELIANCE')}
                >
                  Inspect RELIANCE Dossier
                </button>
                <button
                  type="button"
                  className="chip-btn"
                  style={{ padding: '10px 20px', fontSize: '0.85rem' }}
                  onClick={() => handleSelectSymbol('TCS')}
                >
                  Inspect TCS Dossier
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Screen Companion Live Bottom Bar */}
      <footer className="companion-bar">
        <div className="companion-left">
          <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>AURXON SYSTEM ACTIVE</span>
          <div className="companion-symbols">
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Instruments:</span>
            <span className="companion-tag">NIFTY 50</span>
            <span className="companion-tag">BANKNIFTY</span>
            <span className="companion-tag">SENSEX</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
          <Shield size={12} color="var(--status-verified)" />
          <span>Local SQLite Ledger & Deterministic Validation Operational</span>
        </div>
      </footer>

      {/* Audit Ledger Modal */}
      <AuditLedgerModal isOpen={showLedger} onClose={() => setShowLedger(false)} />
    </div>
  );
};
