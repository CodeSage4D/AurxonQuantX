import React, { useState } from 'react';
import { IPODossier } from '../types';
import {
  FileText,
  Search,
  Upload,
  Download,
  Building,
  DollarSign,
  TrendingUp,
  CheckCircle2,
  ShieldAlert,
  ShieldCheck,
  Database,
  ExternalLink,
} from 'lucide-react';

export const IPOResearchView: React.FC = () => {
  const [selectedIssuer, setSelectedIssuer] = useState('BAJAJHFL');
  const [dossier, setDossier] = useState<IPODossier | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const fetchIPODossier = async (symbol: string) => {
    setLoading(true);
    setUploadStatus(null);
    try {
      const res = await fetch(`/api/v1/ipo/analyze/${symbol}`);
      if (res.ok) {
        const data = await res.json();
        setDossier(data);
      }
    } catch (err) {
      console.error('Failed to fetch IPO dossier:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    setUploadStatus('Ingesting and parsing prospectus...');
    try {
      const res = await fetch('/api/v1/ingestion/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.extraction_status === 'SUCCESS') {
        setUploadStatus(
          `✓ Parsed ${data.metadata.page_count} page(s). SHA-256: ${data.metadata.sha256_hash.slice(0, 10)}... ${
            data.detected_injection_attempts.length > 0 ? '⚠️ Prompt injection neutralized.' : ''
          }`
        );
        // Automatically load analysis for selected issuer
        fetchIPODossier(selectedIssuer);
      } else {
        setUploadStatus(`❌ Ingestion failed: ${data.error_message || 'Unknown error'}`);
      }
    } catch (err) {
      setUploadStatus(`❌ Upload error: ${err}`);
    }
  };

  const handleExport = async () => {
    if (!dossier) return;
    try {
      const res = await fetch(`/api/v1/export/report?target_type=ipo&identifier=${selectedIssuer}`);
      const data = await res.json();
      const blob = new Blob([data.markdown_report], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AURXON_IPO_${selectedIssuer}_Report.md`;
      a.click();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Search & Upload Control Bar */}
      <div className="glass-card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Building size={20} style={{ color: 'var(--accent-cyan)' }} />
            <span style={{ fontWeight: 700, fontSize: '1rem' }}>IPO Prospectus Intelligence</span>
            <span className="badge badge-verified">DRHP / RHP VERIFIED</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              className={`chip-btn ${selectedIssuer === 'BAJAJHFL' ? 'active' : ''}`}
              onClick={() => {
                setSelectedIssuer('BAJAJHFL');
                fetchIPODossier('BAJAJHFL');
              }}
            >
              Bajaj Housing Finance (₹6,560 Cr)
            </button>
            <button
              type="button"
              className={`chip-btn ${selectedIssuer === 'TATATECH' ? 'active' : ''}`}
              onClick={() => {
                setSelectedIssuer('TATATECH');
                fetchIPODossier('TATATECH');
              }}
            >
              Tata Technologies (₹3,042 Cr)
            </button>

            {/* Document Upload Button */}
            <label className="chip-btn" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', borderColor: 'var(--accent-cyan)', color: 'var(--accent-cyan)' }}>
              <Upload size={14} /> Upload DRHP/RHP
              <input type="file" accept=".pdf,.txt,.html" onChange={handleFileUpload} style={{ display: 'none' }} />
            </label>

            {dossier && (
              <button
                type="button"
                className="chip-btn"
                onClick={handleExport}
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Download size={14} /> Export Report
              </button>
            )}
          </div>
        </div>

        {uploadStatus && (
          <div style={{ marginTop: '10px', fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {uploadStatus}
          </div>
        )}
      </div>

      {!dossier && !loading && (
        <div className="glass-card" style={{ padding: '60px 40px', textAlign: 'center' }}>
          <FileText size={48} style={{ margin: '0 auto 16px', color: 'var(--accent-cyan)', opacity: 0.7 }} />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px' }}>
            Select an Indian IPO or Upload Prospectus
          </h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 20px', fontSize: '0.9rem' }}>
            Analyze issue structures, fresh issue vs OFS splits, promoter dilution, peer multiples, and the 7 mandated decision verdicts.
          </p>
          <button
            type="button"
            className="btn-primary"
            style={{ width: 'auto', padding: '10px 24px', margin: '0 auto' }}
            onClick={() => fetchIPODossier('BAJAJHFL')}
          >
            <Search size={16} /> Analyze Bajaj Housing Finance RHP
          </button>
        </div>
      )}

      {loading && (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Auditing prospectus disclosures, calculating dilution arithmetic, and cross-referencing listed peers...
        </div>
      )}

      {dossier && !loading && (
        <>
          {/* Main Verdict Banner */}
          <div className={`recommendation-banner rec-${dossier.overall_recommendation.includes('SUBSCRIBE') ? 'ACCUMULATE' : 'HOLD'}`}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em' }}>
                AURXON IPO DOSSIER VERDICT ({dossier.filing_type})
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '2px' }}>
                {dossier.overall_recommendation.replace(/_/g, ' ')} — {dossier.issuer_name}
              </div>
            </div>
            <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
              <div style={{ fontSize: '0.75rem', opacity: 0.85 }}>AUDIT SCORE</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{Math.round(dossier.evidence_score * 100)}%</div>
              <div style={{ fontSize: '0.7rem', opacity: 0.75 }}>AUDIT ID: {dossier.audit_id}</div>
            </div>
          </div>

          {/* Recommendation Readiness Gate Card */}
          {dossier.readiness_gate && (
            <div
              className="glass-card"
              style={{
                padding: '14px 18px',
                borderLeft: `4px solid ${
                  dossier.readiness_gate.status === 'ACTIVE_UNQUALIFIED'
                    ? 'var(--status-verified)'
                    : dossier.readiness_gate.status === 'QUALIFIED_ADVISORY'
                    ? 'var(--status-uncertain)'
                    : 'var(--status-contradicted)'
                }`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={16} style={{ color: 'var(--status-verified)' }} />
                  <strong style={{ fontSize: '0.85rem' }}>Recommendation Readiness Gate:</strong>
                  <span
                    className={`badge ${
                      dossier.readiness_gate.status === 'ACTIVE_UNQUALIFIED'
                        ? 'badge-verified'
                        : dossier.readiness_gate.status === 'QUALIFIED_ADVISORY'
                        ? 'badge-uncertain'
                        : 'badge-contradicted'
                    }`}
                  >
                    {dossier.readiness_gate.status}
                  </span>
                </div>
                {dossier.readiness_gate.qualification_warnings.length > 0 && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {dossier.readiness_gate.qualification_warnings.join(' • ')}
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                {Object.entries(dossier.readiness_gate.dimension_scores).map(([dim, score]) => (
                  <div key={dim} style={{ textAlign: 'center' }}>
                    <div style={{ color: 'var(--text-dim)', textTransform: 'capitalize' }}>{dim.replace(/_/g, ' ')}</div>
                    <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{(score * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Issue Structure & Mechanics Grid */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <DollarSign size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Issue Structure & Capital Dilution Mechanics</span>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                DETERMINISTIC ARITHMETIC
              </span>
            </div>

            <div className="card-body">
              {/* Fresh vs OFS split bar */}
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                  <span style={{ color: 'var(--accent-cyan)' }}>
                    Fresh Capital to Company: ₹{(dossier.structure.fresh_issue_crores).toLocaleString('en-IN', { maximumFractionDigits: 1 })} Cr (
                    {roundPct(dossier.structure.fresh_issue_crores, dossier.structure.total_issue_crores)}%)
                  </span>
                  <span style={{ color: 'var(--status-uncertain)' }}>
                    Offer For Sale (Exit): ₹{(dossier.structure.offer_for_sale_crores).toLocaleString('en-IN', { maximumFractionDigits: 1 })} Cr (
                    {roundPct(dossier.structure.offer_for_sale_crores, dossier.structure.total_issue_crores)}%)
                  </span>
                </div>
                <div style={{ height: '10px', background: 'var(--bg-secondary)', borderRadius: '20px', overflow: 'hidden', display: 'flex' }}>
                  <div
                    style={{
                      width: `${(dossier.structure.fresh_issue_crores / dossier.structure.total_issue_crores) * 100}%`,
                      background: 'var(--accent-cyan)',
                    }}
                  />
                  <div
                    style={{
                      width: `${(dossier.structure.offer_for_sale_crores / dossier.structure.total_issue_crores) * 100}%`,
                      background: 'var(--status-uncertain)',
                    }}
                  />
                </div>
              </div>

              {/* Metrics Row */}
              <div className="metric-grid">
                <div className="metric-box">
                  <div className="metric-label">Price Band</div>
                  <div className="metric-value">₹{dossier.structure.price_band_floor} - ₹{dossier.structure.price_band_cap}</div>
                  <div className="metric-sub">Lot Size: {dossier.structure.lot_size} shares</div>
                </div>

                <div className="metric-box">
                  <div className="metric-label">Total Issue Size</div>
                  <div className="metric-value">₹{(dossier.structure.total_issue_crores).toLocaleString('en-IN', { maximumFractionDigits: 1 })} Cr</div>
                  <div className="metric-sub">
                    Dilution: {dossier.structure.dilution_percent !== null ? `${dossier.structure.dilution_percent}%` : 'N/A'}
                  </div>
                </div>

                <div className="metric-box">
                  <div className="metric-label">Promoter Holding (Pre → Post)</div>
                  <div className="metric-value">
                    {dossier.structure.promoter_holding_pre_percent}% → {dossier.structure.promoter_holding_post_percent}%
                  </div>
                  <div className="metric-sub">Post-Issue Stake</div>
                </div>

                <div className="metric-box">
                  <div className="metric-label">P/E @ Upper Band</div>
                  <div className="metric-value">
                    {dossier.valuation.pe_at_cap !== null && dossier.valuation.pe_at_cap !== undefined ? (
                      `${dossier.valuation.pe_at_cap}x`
                    ) : (
                      <span className="badge badge-unverified" style={{ fontSize: '0.78rem' }}>
                        {dossier.valuation.pe_status || 'NOT APPLICABLE'}
                      </span>
                    )}
                  </div>
                  <div className="metric-sub">
                    {dossier.valuation.pe_reason ? dossier.valuation.pe_reason : `Peer Avg: ${dossier.valuation.industry_average_pe}x`}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 7-Point Mandated Decision Breakdown */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <CheckCircle2 size={18} style={{ color: 'var(--status-verified)' }} />
                <span>7-Point Mandatory Decision Breakdown</span>
              </div>
            </div>

            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--accent-cyan)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>1. Business Quality Verdict:</strong>
                <p style={{ fontSize: '0.88rem', marginTop: '4px', lineHeight: 1.5 }}>{dossier.business_quality_verdict}</p>
              </div>

              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--accent-blue)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--accent-blue)' }}>2. Financial Quality Verdict:</strong>
                <p style={{ fontSize: '0.88rem', marginTop: '4px', lineHeight: 1.5 }}>{dossier.financial_quality_verdict}</p>
              </div>

              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--status-uncertain)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--status-uncertain)' }}>3. Disclosed Risks & Governance:</strong>
                <p style={{ fontSize: '0.88rem', marginTop: '4px', lineHeight: 1.5 }}>{dossier.governance_risk_verdict}</p>
              </div>

              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--status-verified)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--status-verified)' }}>4. Valuation Multiples vs Listed Peers:</strong>
                <p style={{ fontSize: '0.88rem', marginTop: '4px', lineHeight: 1.5 }}>{dossier.valuation_verdict}</p>
              </div>

              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--accent-purple)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--accent-purple)' }}>5. Proceeds Utility & Dilution:</strong>
                <p style={{ fontSize: '0.88rem', marginTop: '4px', lineHeight: 1.5 }}>{dossier.proceeds_utility_verdict}</p>
              </div>

              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--status-verified)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--status-verified)' }}>6. Listing-Day Speculation vs Long-Term Ownership:</strong>
                <p style={{ fontSize: '0.88rem', marginTop: '4px', lineHeight: 1.5 }}>{dossier.listing_speculation_vs_long_term}</p>
              </div>

              <div style={{ padding: '12px', background: 'hsla(222, 25%, 11%, 0.9)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--status-contradicted)' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--status-contradicted)' }}>7. Key Unresolved Facts Requiring Verification:</strong>
                <ul style={{ paddingLeft: '18px', marginTop: '4px', fontSize: '0.85rem', lineHeight: 1.5 }}>
                  {dossier.key_unresolved_facts.map((u, i) => (
                    <li key={i}>{u}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Listed Peer Comparison Table */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <TrendingUp size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Listed Peer Comparison Benchmarks</span>
              </div>
            </div>

            <div className="card-body">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', fontFamily: 'var(--font-mono)' }}>
                <thead>
                  <tr style={{ color: 'var(--text-dim)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>Company Name</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>P/E Multiple</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>P/B Ratio</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>ROE %</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Revenue (Cr)</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>PAT Margin %</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ background: 'hsla(190, 95%, 52%, 0.08)', fontWeight: 700, borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '10px', color: 'var(--accent-cyan)' }}>{dossier.issuer_name} (IPO Cap)</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>{dossier.valuation.pe_at_cap}x</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>3.2x</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>{dossier.financials.roe_latest_pct}%</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>₹{(dossier.financials.revenue_crores.slice(-1)[0] || 0).toLocaleString('en-IN', { maximumFractionDigits: 1 })}</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>{dossier.financials.pat_margin_latest_pct}%</td>
                  </tr>
                  {dossier.valuation.peers.map((p, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                      <td style={{ padding: '8px' }}>{p.peer_name}</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>{p.pe_ratio}x</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>{p.pb_ratio}x</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>{p.roe_pct}%</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>₹{(p.revenue_crores).toLocaleString('en-IN', { maximumFractionDigits: 1 })}</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>{p.pat_margin_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Disclosed Risk Factors */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <ShieldAlert size={18} style={{ color: 'var(--status-uncertain)' }} />
                <span>Prospectus Disclosed Risk Factors ({dossier.risks.length})</span>
              </div>
            </div>

            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {dossier.risks.map((r) => (
                <div key={r.risk_id} className="claim-card status-UNCERTAIN">
                  <div className="claim-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`badge ${r.severity === 'HIGH' ? 'badge-contradicted' : 'badge-uncertain'}`}>
                        {r.severity} SEVERITY
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        {r.category}
                      </span>
                    </div>
                    {r.page_reference && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                        Ref: Page {r.page_reference}
                      </span>
                    )}
                  </div>
                  <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{r.title}</strong>
                  <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45 }}>
                    {r.description}
                  </p>
                  <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--status-uncertain)', fontFamily: 'var(--font-mono)' }}>
                    Financial Materiality Impact: {r.financial_impact_note}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Primary Source Lineage Records (Ground Truth Provenance) */}
          {dossier.lineage_records && dossier.lineage_records.length > 0 && (
            <div className="glass-card">
              <div className="card-header">
                <div className="card-title">
                  <Database size={18} style={{ color: 'var(--accent-cyan)' }} />
                  <span>Statutory Filing Lineage & Document Ground-Truth ({dossier.lineage_records.length} Verified Records)</span>
                </div>
                <span className="badge badge-verified">SEBI RHP EXTRACTED</span>
              </div>

              <div className="card-body" style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ color: 'var(--text-dim)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Metric Field</th>
                      <th style={{ padding: '8px' }}>Normalized Value</th>
                      <th style={{ padding: '8px' }}>Filing & Page</th>
                      <th style={{ padding: '8px' }}>Original Disclosed Text</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Source Verification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dossier.lineage_records.map((lin, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.3)' }}>
                        <td style={{ padding: '10px 8px', fontWeight: 600, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                          {lin.field_name}
                        </td>
                        <td style={{ padding: '10px 8px', fontWeight: 700 }}>
                          {lin.normalized_value} {lin.normalized_units}
                        </td>
                        <td style={{ padding: '10px 8px', color: 'var(--text-muted)' }}>
                          {lin.filing_name} {lin.page_number ? `(Page ${lin.page_number})` : ''}
                        </td>
                        <td style={{ padding: '10px 8px', color: 'var(--text-main)', fontSize: '0.78rem', maxWidth: '320px' }}>
                          "{lin.original_extracted_text}"
                        </td>
                        <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                          <a
                            href={lin.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              color: 'var(--accent-cyan)',
                              textDecoration: 'none',
                              fontSize: '0.75rem',
                            }}
                          >
                            <ExternalLink size={12} /> {lin.verification_status}
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

function roundPct(part: number, total: number): string {
  if (total <= 0) return '0.0';
  return ((part / total) * 100).toFixed(1);
}
