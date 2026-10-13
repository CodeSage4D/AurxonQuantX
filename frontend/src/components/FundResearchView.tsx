import React, { useEffect, useState } from 'react';
import { FundComparisonResult, PortfolioAllocationPlan } from '../types';
import {
  PieChart,
  Layers,
  ArrowRightLeft,
  Sliders,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';

export const FundResearchView: React.FC = () => {
  const [codeA, setCodeA] = useState('PPFAS_FLEXI');
  const [codeB, setCodeB] = useState('NIFTYBEES');
  const [comparison, setComparison] = useState<FundComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Allocation state
  const [goalName, setGoalName] = useState('Wealth Creation & Financial Independence');
  const [horizonYears, setHorizonYears] = useState(7);
  const [riskProfile, setRiskProfile] = useState('moderate');
  const [allocation, setAllocation] = useState<PortfolioAllocationPlan | null>(null);
  const [allocLoading, setAllocLoading] = useState(false);

  const fetchComparison = async (a: string, b: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/funds/compare?code_a=${a}&code_b=${b}`);
      if (res.ok) {
        const data = await res.json();
        setComparison(data);
      }
    } catch (err) {
      console.error('Failed to compare funds:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAllocation = async (e: React.FormEvent) => {
    e.preventDefault();
    setAllocLoading(true);
    try {
      const res = await fetch('/api/v1/funds/allocate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal_name: goalName,
          horizon_years: horizonYears,
          risk_profile: riskProfile,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setAllocation(data);
      }
    } catch (err) {
      console.error('Failed to generate allocation:', err);
    } finally {
      setAllocLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison(codeA, codeB);
  }, [codeA, codeB]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Card */}
      <div className="glass-card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <PieChart size={20} style={{ color: 'var(--accent-cyan)' }} />
            <span style={{ fontWeight: 700, fontSize: '1rem' }}>Mutual Fund & ETF Quantitative Intelligence</span>
            <span className="badge badge-verified">CATEGORY BENCHMARKED</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Compare:</span>
            <select
              className="select-input"
              style={{ width: 'auto', padding: '6px 10px', fontSize: '0.8rem' }}
              value={codeA}
              onChange={(e) => setCodeA(e.target.value)}
            >
              <option value="PPFAS_FLEXI">Parag Parikh Flexi Cap</option>
              <option value="MIRAE_LARGE">Mirae Asset Large Cap</option>
            </select>
            <ArrowRightLeft size={14} style={{ color: 'var(--text-dim)' }} />
            <select
              className="select-input"
              style={{ width: 'auto', padding: '6px 10px', fontSize: '0.8rem' }}
              value={codeB}
              onChange={(e) => setCodeB(e.target.value)}
            >
              <option value="NIFTYBEES">Nippon India Nifty 50 BeES (ETF)</option>
              <option value="MIRAE_LARGE">Mirae Asset Large Cap</option>
            </select>
            {loading && <span className="status-tag" style={{ fontSize: '0.75rem' }}>Comparing...</span>}
          </div>
        </div>
      </div>

      {/* Comparison View */}
      {comparison && (
        <>
          {/* Key Metric Highlights & Direct Savings */}
          <div className="metric-grid">
            <div className="metric-box">
              <div className="metric-label">Portfolio Overlap</div>
              <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
                {Object.values(comparison.pairwise_overlap_pct)[0]}%
              </div>
              <div className="metric-sub">Shared stock holdings weight</div>
            </div>

            <div className="metric-box">
              <div className="metric-label">10Y Direct Plan Savings</div>
              <div className="metric-value" style={{ color: 'var(--status-verified)' }}>
                +₹{comparison.direct_vs_regular_savings_10y_lakhs} Lakhs
              </div>
              <div className="metric-sub">Fee savings on ₹10L @ 12% CAGR</div>
            </div>

            <div className="metric-box">
              <div className="metric-label">{comparison.schemes[0].scheme_name.slice(0, 18)}... TER</div>
              <div className="metric-value">{comparison.schemes[0].expense_ratio_pct}%</div>
              <div className="metric-sub">Category: {comparison.schemes[0].category}</div>
            </div>

            <div className="metric-box">
              <div className="metric-label">{comparison.schemes[1].scheme_name.slice(0, 18)}... TER</div>
              <div className="metric-value">{comparison.schemes[1].expense_ratio_pct}%</div>
              <div className="metric-sub">Category: {comparison.schemes[1].category}</div>
            </div>
          </div>

          {/* Side by side comparison table */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <Layers size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Side-by-Side Factor & Rolling Return Performance</span>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                TRI BENCHMARKED • DIRECT GROWTH
              </span>
            </div>

            <div className="card-body">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', fontFamily: 'var(--font-mono)' }}>
                <thead>
                  <tr style={{ color: 'var(--text-dim)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>Metric</th>
                    <th style={{ padding: '8px', textAlign: 'right', color: 'var(--accent-cyan)' }}>
                      {comparison.schemes[0].scheme_name}
                    </th>
                    <th style={{ padding: '8px', textAlign: 'right', color: 'var(--accent-blue)' }}>
                      {comparison.schemes[1].scheme_name}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>Category & Strategy</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{comparison.schemes[0].category} (Active)</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{comparison.schemes[1].category} ({comparison.schemes[1].is_passive ? 'Passive' : 'Active'})</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>3-Year CAGR %</td>
                    <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700 }}>
                      {comparison.metrics[comparison.schemes[0].scheme_code]?.cagr_3y_pct}%
                    </td>
                    <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700 }}>
                      {comparison.metrics[comparison.schemes[1].scheme_code]?.cagr_3y_pct}%
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>5-Year CAGR %</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>
                      {comparison.metrics[comparison.schemes[0].scheme_code]?.cagr_5y_pct}%
                    </td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>
                      {comparison.metrics[comparison.schemes[1].scheme_code]?.cagr_5y_pct}%
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>3Y Rolling Return Range (Min / Median / Max)</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>
                      {comparison.metrics[comparison.schemes[0].scheme_code]?.rolling_return_3y_min_pct}% /{' '}
                      {comparison.metrics[comparison.schemes[0].scheme_code]?.rolling_return_3y_median_pct}% /{' '}
                      {comparison.metrics[comparison.schemes[0].scheme_code]?.rolling_return_3y_max_pct}%
                    </td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>
                      {comparison.metrics[comparison.schemes[1].scheme_code]?.rolling_return_3y_min_pct}% /{' '}
                      {comparison.metrics[comparison.schemes[1].scheme_code]?.rolling_return_3y_median_pct}% /{' '}
                      {comparison.metrics[comparison.schemes[1].scheme_code]?.rolling_return_3y_max_pct}%
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>Sharpe Ratio (RF = 6.8%)</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>
                      {comparison.metrics[comparison.schemes[0].scheme_code]?.sharpe_ratio}
                    </td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>
                      {comparison.metrics[comparison.schemes[1].scheme_code]?.sharpe_ratio}
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                    <td style={{ padding: '8px', color: 'var(--text-muted)' }}>Maximum Historical Drawdown %</td>
                    <td style={{ padding: '8px', textAlign: 'right', color: 'var(--status-contradicted)' }}>
                      -{comparison.metrics[comparison.schemes[0].scheme_code]?.max_drawdown_pct}%
                    </td>
                    <td style={{ padding: '8px', textAlign: 'right', color: 'var(--status-contradicted)' }}>
                      -{comparison.metrics[comparison.schemes[1].scheme_code]?.max_drawdown_pct}%
                    </td>
                  </tr>
                  {comparison.metrics[comparison.schemes[1].scheme_code]?.tracking_error_pct != null && (
                    <tr style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                      <td style={{ padding: '8px', color: 'var(--text-muted)' }}>ETF Annualized Tracking Error</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>N/A (Active)</td>
                      <td style={{ padding: '8px', textAlign: 'right', color: 'var(--status-verified)' }}>
                        {comparison.metrics[comparison.schemes[1].scheme_code]?.tracking_error_pct}%
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              {/* Research Notes */}
              <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {comparison.comparison_notes.map((note, i) => (
                  <div key={i} style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldCheck size={12} color="var(--accent-cyan)" /> {note}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Goal-Based Portfolio Allocator Card */}
      <div className="glass-card">
        <div className="card-header">
          <div className="card-title">
            <Sliders size={18} style={{ color: 'var(--accent-cyan)' }} />
            <span>Interactive Goal-Based Portfolio Allocation Engine</span>
          </div>
        </div>

        <div className="card-body">
          <form onSubmit={handleGenerateAllocation} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '16px' }}>
            <div>
              <label className="form-label">Goal / Objective</label>
              <input
                type="text"
                className="text-input"
                value={goalName}
                onChange={(e) => setGoalName(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="form-label">Time Horizon (Years): {horizonYears} Yrs</label>
              <input
                type="range"
                min={1}
                max={25}
                value={horizonYears}
                onChange={(e) => setHorizonYears(parseInt(e.target.value))}
                style={{ width: '100%', marginTop: '8px' }}
              />
            </div>

            <div>
              <label className="form-label">Risk Tolerance</label>
              <select
                className="select-input"
                value={riskProfile}
                onChange={(e) => setRiskProfile(e.target.value)}
              >
                <option value="conservative">Conservative (Capital Defense)</option>
                <option value="moderate">Moderate (Balanced Compounding)</option>
                <option value="aggressive">Aggressive (Wealth Acceleration)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button type="submit" className="btn-primary" disabled={allocLoading}>
                Generate Allocation
              </button>
            </div>
          </form>

          {allocation && (
            <div style={{ marginTop: '20px', padding: '16px', background: 'hsla(222, 25%, 10%, 0.8)', border: '1px solid var(--border-card)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                  Target Allocation: {allocation.recommended_equity_pct}% Equity | {allocation.recommended_debt_pct}% Debt | {allocation.recommended_gold_pct}% Gold
                </span>
                <span className="badge badge-uncertain" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertTriangle size={12} /> Stress Drawdown: -{allocation.downside_stress_scenario_drawdown_pct}%
                </span>
              </div>

              {/* Recommended vehicle grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px', marginBottom: '14px' }}>
                {allocation.allocated_schemes.map((s, idx) => (
                  <div key={idx} style={{ padding: '10px 12px', background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>{s.category}</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-cyan)', margin: '2px 0' }}>{s.weight_pct}%</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{s.vehicle}</div>
                  </div>
                ))}
              </div>

              {/* Caveats */}
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', lineHeight: 1.5 }}>
                {allocation.key_risks_and_caveats.map((c, i) => (
                  <div key={i} style={{ marginBottom: '2px' }}>• {c}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
