import React from 'react';
import { DeterministicValuation } from '../types';
import { ShieldCheck, Info, Calculator, Table } from 'lucide-react';

interface Props {
  valuation: DeterministicValuation | null;
}

export const ValuationCard: React.FC<Props> = ({ valuation }) => {
  if (!valuation) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)' }}>
        <Calculator size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
        <p>Awaiting research objective to compute deterministic valuation...</p>
      </div>
    );
  }

  const dcfPositive = valuation.dcf_upside_percent != null && valuation.dcf_upside_percent >= 0;
  const grahamPositive = valuation.graham_upside_percent >= 0;

  return (
    <div className="glass-card" style={{ marginBottom: '20px' }}>
      <div className="card-header">
        <div className="card-title">
          <Calculator size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span>Deterministic Valuation & Fundamental Scores</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-verified" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ShieldCheck size={12} /> 100% REPRODUCIBLE MATH
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            {valuation.ticker} @ ₹{valuation.current_price.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="card-body">
        {/* Sector Exclusion Warning if applicable */}
        {valuation.sector_exclusion_notes && (
          <div style={{ marginBottom: '16px', padding: '10px 14px', background: 'hsla(42, 95%, 52%, 0.1)', border: '1px solid var(--status-uncertain)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: 'var(--status-uncertain)', lineHeight: 1.5 }}>
            <strong>BANKING SECTOR GUARD:</strong> {valuation.sector_exclusion_notes}
          </div>
        )}

        {/* Metric Grid */}
        <div className="metric-grid">
          {/* DCF Fair Value */}
          <div className="metric-box">
            <div className="metric-label">
              <span>DCF Fair Value (2-Stage)</span>
              <span title={valuation.formula_signatures?.dcf_model} style={{ cursor: 'help' }}>
                <Info size={12} />
              </span>
            </div>
            <div className="metric-value">
              {valuation.fair_value_dcf != null ? `₹${valuation.fair_value_dcf.toFixed(2)}` : 'N/A (Excluded)'}
            </div>
            <div className={`metric-sub ${dcfPositive ? 'positive' : 'negative'}`}>
              {valuation.dcf_upside_percent != null
                ? `${dcfPositive ? '▲ +' : '▼ '}${valuation.dcf_upside_percent.toFixed(1)}% vs CMP`
                : 'Banking Model Exclusion'}
            </div>
          </div>

          {/* Graham Number */}
          <div className="metric-box">
            <div className="metric-label">
              <span>Benjamin Graham Fair Value</span>
              <span title={valuation.formula_signatures?.graham_number} style={{ cursor: 'help' }}>
                <Info size={12} />
              </span>
            </div>
            <div className="metric-value">₹{valuation.graham_number.toFixed(2)}</div>
            <div className={`metric-sub ${grahamPositive ? 'positive' : 'negative'}`}>
              {grahamPositive ? '▲ +' : '▼ '}
              {valuation.graham_upside_percent.toFixed(1)}% vs CMP
            </div>
          </div>

          {/* Piotroski F-Score */}
          <div className="metric-box">
            <div className="metric-label">
              <span>Piotroski F-Score (0-9)</span>
              <span title="9-point accounting fundamental strength" style={{ cursor: 'help' }}>
                <Info size={12} />
              </span>
            </div>
            <div className="metric-value" style={{ color: valuation.piotroski_f_score >= 7 ? 'var(--status-verified)' : 'var(--text-main)' }}>
              {valuation.piotroski_f_score} / 9
            </div>
            <div className="metric-sub" style={{ color: valuation.piotroski_f_score >= 7 ? 'var(--status-verified)' : 'var(--text-muted)' }}>
              {valuation.piotroski_f_score >= 7 ? 'High Accounting Quality' : 'Moderate Strength'}
            </div>
          </div>

          {/* Altman Z-Score */}
          <div className="metric-box">
            <div className="metric-label">
              <span>Altman Z-Score</span>
              <span title={valuation.formula_signatures?.altman_z_score} style={{ cursor: 'help' }}>
                <Info size={12} />
              </span>
            </div>
            <div className="metric-value">
              {valuation.altman_z_score != null ? valuation.altman_z_score.toFixed(2) : 'N/A (Bank/NBFC)'}
            </div>
            <div className="metric-sub" style={{ color: valuation.altman_z_score != null && valuation.altman_z_score >= 2.99 ? 'var(--status-verified)' : 'var(--text-dim)' }}>
              {valuation.altman_z_score != null
                ? (valuation.altman_z_score >= 2.99 ? 'Safe Zone (Low Default Risk)' : 'Grey / Alert Zone')
                : 'Excluded from Commercial Banks'}
            </div>
          </div>

          {/* P/E Multiples */}
          <div className="metric-box">
            <div className="metric-label">
              <span>P/E Ratio (TTM)</span>
            </div>
            <div className="metric-value">{valuation.pe_ratio.toFixed(1)}x</div>
            <div className="metric-sub" style={{ color: 'var(--text-dim)' }}>
              P/B: {valuation.pb_ratio.toFixed(2)}x
            </div>
          </div>

          {/* Dividend Yield */}
          <div className="metric-box">
            <div className="metric-label">
              <span>Dividend Yield</span>
            </div>
            <div className="metric-value">{valuation.dividend_yield_percent.toFixed(2)}%</div>
            <div className="metric-sub" style={{ color: 'var(--text-dim)' }}>
              Annual Payout
            </div>
          </div>
        </div>

        {/* DCF Sensitivity Grid (3x3) */}
        {valuation.dcf_sensitivity_matrix && (
          <div style={{ marginTop: '16px', background: 'hsla(222, 25%, 9%, 0.8)', border: '1px solid var(--border-card)', borderRadius: 'var(--radius-sm)', padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '8px' }}>
              <Table size={14} /> 3x3 DCF SENSITIVITY GRID (Discount Rate vs Terminal Growth)
            </div>
            <table style={{ width: '100%', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: 'var(--text-dim)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '4px', textAlign: 'left' }}>WACC \ g_term</th>
                  <th style={{ padding: '4px', textAlign: 'right' }}>3.5%</th>
                  <th style={{ padding: '4px', textAlign: 'right' }}>4.5% (Base)</th>
                  <th style={{ padding: '4px', textAlign: 'right' }}>5.5%</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(valuation.dcf_sensitivity_matrix).map(([drKey, row]) => (
                  <tr key={drKey} style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.2)' }}>
                    <td style={{ padding: '4px', color: 'var(--text-muted)', fontWeight: 600 }}>{drKey}</td>
                    <td style={{ padding: '4px', textAlign: 'right' }}>₹{row['3.5%']?.toFixed(1)}</td>
                    <td style={{ padding: '4px', textAlign: 'right', color: 'var(--accent-cyan)', fontWeight: 700 }}>₹{row['4.5%']?.toFixed(1)}</td>
                    <td style={{ padding: '4px', textAlign: 'right' }}>₹{row['5.5%']?.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Formula Transparency Drawer */}
        <div style={{ marginTop: '12px', padding: '10px 14px', background: 'hsla(222, 25%, 8%, 0.8)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            <strong>FORMULA AUDIT TRAIL:</strong> Graham = {valuation.formula_signatures?.graham_number} | DCF = {valuation.formula_signatures?.dcf_model}
          </div>
        </div>
      </div>
    </div>
  );
};
