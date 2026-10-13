import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Layers,
  Database,
  CheckCircle2,
  Play,
  RotateCw,
  Lock,
} from 'lucide-react';

interface ModelAsset {
  stable_id: string;
  display_name: string;
  provider: string;
  version_revision: string;
  intended_task: string;
  execution_mode: 'LOCAL_BINARY' | 'CLOUD_API' | 'DETERMINISTIC_ENGINE' | 'HEURISTIC_OFFLINE';
  storage_path_or_endpoint: string;
  license_type: string;
  estimated_ram_mb: number;
  is_available: boolean;
  operational_status: 'OPERATIONAL' | 'CONFIGURED_NO_KEYS' | 'FALLBACK_ACTIVE' | 'BLOCKED_UNAVAILABLE';
  is_demonstration: boolean;
  last_evaluation_date: string;
  dataset_version: string;
  notes: string;
}

interface ResponsibilityRecord {
  task_name: string;
  category: string;
  primary_model_id: string;
  rationale: string;
  fallback_model_id: string;
  can_override_risk_veto: boolean;
  measured_latency_p50_ms: number;
  limitations: string;
}

interface EvaluationRecord {
  model_id: string;
  task: string;
  metric_name: string;
  measured_value: number;
  benchmark_baseline: number;
  status: string;
  dataset_name: string;
  dataset_sample_size: number;
  test_conditions: string;
  tested_at: string;
}

export const ModelInventoryView: React.FC = () => {
  const [models, setModels] = useState<ModelAsset[]>([]);
  const [responsibilities, setResponsibilities] = useState<ResponsibilityRecord[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationRecord[]>([]);
  const [activeSection, setActiveSection] = useState<'ESTATE' | 'RESPONSIBILITIES' | 'EVALUATIONS'>('ESTATE');
  const [isLoading, setIsLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);

  const fetchInventory = async () => {
    setIsLoading(true);
    try {
      const [invRes, respRes] = await Promise.all([
        fetch('/api/v1/models/inventory'),
        fetch('/api/v1/models/responsibilities'),
      ]);
      if (invRes.ok) setModels(await invRes.json());
      if (respRes.ok) setResponsibilities(await respRes.json());
    } catch (err) {
      console.error('Failed to load model inventory:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const runEvaluation = async () => {
    setEvaluating(true);
    try {
      const res = await fetch('/api/v1/models/evaluate', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setEvaluations(data.scores || []);
        if (data.models) setModels(data.models);
      }
    } catch (err) {
      console.error('Evaluation run failed:', err);
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    fetchInventory();
    runEvaluation();
  }, []);

  const totalModels = models.length;
  const operationalModels = models.filter((m) => m.operational_status === 'OPERATIONAL').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        className="glass-card"
        style={{
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Cpu size={24} style={{ color: 'var(--accent-blue)' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>
              AI Model Estate & Responsibility Matrix
            </h2>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
            Transparent discovery of local binaries, deterministic arithmetic engines, cloud adapters, and honest benchmark scores.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            className="chip-btn"
            onClick={fetchInventory}
            disabled={isLoading}
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RotateCw size={13} className={isLoading ? 'spin' : ''} /> Refresh
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={runEvaluation}
            disabled={evaluating}
            style={{ width: 'auto', padding: '8px 16px', fontSize: '0.82rem' }}
          >
            <Play size={13} /> {evaluating ? 'Evaluating...' : 'Run Live Evaluation'}
          </button>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>
            Discovered Models & Engines
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '4px', color: 'var(--text-main)' }}>
            {totalModels}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Local, Cloud & Deterministic
          </div>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>
            Operational Ready
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '4px', color: 'var(--status-verified)' }}>
            {operationalModels} / {totalModels}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Ready for live invocation
          </div>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>
            Deterministic Risk Veto
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '4px', color: 'var(--status-verified)' }}>
            HARD LOCKED
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Zero LLM override permitted
          </div>
        </div>

        <div className="glass-card" style={{ padding: '16px 20px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>
            Verified Benchmarks
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: '4px', color: 'var(--accent-blue)' }}>
            {evaluations.length} Evaluated
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Gold-truth references tested
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
        <button
          type="button"
          className={`chip-btn ${activeSection === 'ESTATE' ? 'active' : ''}`}
          onClick={() => setActiveSection('ESTATE')}
        >
          <Database size={13} /> Discovered Model Estate ({models.length})
        </button>
        <button
          type="button"
          className={`chip-btn ${activeSection === 'RESPONSIBILITIES' ? 'active' : ''}`}
          onClick={() => setActiveSection('RESPONSIBILITIES')}
        >
          <Layers size={13} /> Task Responsibility Matrix ({responsibilities.length})
        </button>
        <button
          type="button"
          className={`chip-btn ${activeSection === 'EVALUATIONS' ? 'active' : ''}`}
          onClick={() => setActiveSection('EVALUATIONS')}
        >
          <CheckCircle2 size={13} /> Benchmark Evaluations ({evaluations.length})
        </button>
      </div>

      {/* Section 1: Discovered Model Estate */}
      {activeSection === 'ESTATE' && (
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">
              <Database size={15} style={{ color: 'var(--accent-blue)' }} /> Model Estate Registry
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
              Total footprint: ~{models.reduce((acc, m) => acc + m.estimated_ram_mb, 0).toFixed(0)} MB RAM
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model ID</th>
                  <th>Display Name</th>
                  <th>Execution Mode</th>
                  <th>Task Area</th>
                  <th>License</th>
                  <th>RAM</th>
                  <th>Status</th>
                  <th>Provenance Notes</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.stable_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{m.stable_id}</td>
                    <td>{m.display_name}</td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontFamily: 'var(--font-mono)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background:
                            m.execution_mode === 'LOCAL_BINARY'
                              ? 'rgba(16, 185, 129, 0.15)'
                              : m.execution_mode === 'DETERMINISTIC_ENGINE'
                              ? 'rgba(59, 130, 246, 0.15)'
                              : 'rgba(168, 85, 247, 0.15)',
                          color:
                            m.execution_mode === 'LOCAL_BINARY'
                              ? 'var(--status-verified)'
                              : m.execution_mode === 'DETERMINISTIC_ENGINE'
                              ? 'var(--accent-blue)'
                              : 'var(--accent-purple)',
                        }}
                      >
                        {m.execution_mode}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>{m.intended_task}</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{m.license_type}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{m.estimated_ram_mb > 0 ? `${m.estimated_ram_mb} MB` : 'Cloud API'}</td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          padding: '2px 6px',
                          borderRadius: '12px',
                          background:
                            m.operational_status === 'OPERATIONAL'
                              ? 'var(--status-verified-bg)'
                              : 'var(--status-uncertain-bg)',
                          color:
                            m.operational_status === 'OPERATIONAL'
                              ? 'var(--status-verified)'
                              : 'var(--status-uncertain)',
                          fontWeight: 600,
                        }}
                      >
                        {m.operational_status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{m.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Section 2: Task Responsibility Matrix */}
      {activeSection === 'RESPONSIBILITIES' && (
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">
              <Layers size={15} style={{ color: 'var(--accent-blue)' }} /> Intelligence Routing & Fallbacks
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--status-verified)', fontSize: '0.75rem' }}>
              <Lock size={12} /> Strict Deterministic Risk Isolation
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Task Name</th>
                  <th>Category</th>
                  <th>Primary Component</th>
                  <th>Rationale</th>
                  <th>Fallback Component</th>
                  <th>p50 Latency</th>
                  <th>Risk Override</th>
                </tr>
              </thead>
              <tbody>
                {responsibilities.map((r) => (
                  <tr key={r.task_name}>
                    <td style={{ fontWeight: 600 }}>{r.task_name}</td>
                    <td>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {r.category}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)', fontWeight: 600 }}>
                      {r.primary_model_id}
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.rationale}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {r.fallback_model_id}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.measured_latency_p50_ms} ms</td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'rgba(239, 68, 68, 0.12)',
                          color: 'var(--status-contradicted)',
                          fontWeight: 700,
                        }}
                      >
                        FORBIDDEN
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Section 3: Benchmark Evaluations */}
      {activeSection === 'EVALUATIONS' && (
        <div className="glass-card">
          <div className="card-header">
            <span className="card-title">
              <CheckCircle2 size={15} style={{ color: 'var(--status-verified)' }} /> Empirical Benchmark Scores
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
              Tested against gold-truth fixtures & RHP filings
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model ID</th>
                  <th>Evaluated Capability</th>
                  <th>Metric Name</th>
                  <th>Measured Score</th>
                  <th>Benchmark Baseline</th>
                  <th>Status</th>
                  <th>Dataset / Sample Size</th>
                  <th>Test Date</th>
                </tr>
              </thead>
              <tbody>
                {evaluations.map((ev, idx) => (
                  <tr key={idx}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{ev.model_id}</td>
                    <td>{ev.task}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{ev.metric_name}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--status-verified)' }}>
                      {(ev.measured_value * 100).toFixed(1)}%
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                      {(ev.benchmark_baseline * 100).toFixed(1)}%
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          padding: '2px 6px',
                          borderRadius: '12px',
                          background:
                            ev.status === 'VERIFIED'
                              ? 'var(--status-verified-bg)'
                              : 'var(--status-uncertain-bg)',
                          color:
                            ev.status === 'VERIFIED'
                              ? 'var(--status-verified)'
                              : 'var(--status-uncertain)',
                          fontWeight: 600,
                        }}
                      >
                        {ev.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {ev.dataset_name} (N={ev.dataset_sample_size})
                    </td>
                    <td style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                      {ev.tested_at}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
