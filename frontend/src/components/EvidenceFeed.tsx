import React from 'react';
import { EvidenceClaim } from '../types';
import { CheckCircle2, AlertTriangle, XCircle, ExternalLink, ShieldAlert } from 'lucide-react';

interface Props {
  claims: EvidenceClaim[];
}

export const EvidenceFeed: React.FC<Props> = ({ claims }) => {
  if (!claims || claims.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)' }}>
        <p>No evidence claims extracted yet. Run research to extract and verify claims.</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <span className="badge badge-verified" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={12} /> VERIFIED
          </span>
        );
      case 'UNCERTAIN':
        return (
          <span className="badge badge-uncertain" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={12} /> UNCERTAIN / STALE
          </span>
        );
      case 'CONTRADICTED':
        return (
          <span className="badge badge-contradicted" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <XCircle size={12} /> CONTRADICTED
          </span>
        );
      default:
        return <span className="badge">{status}</span>;
    }
  };

  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-title">
          <CheckCircle2 size={18} style={{ color: 'var(--status-verified)' }} />
          <span>Extracted Evidence & Exchange Disclosures ({claims.length})</span>
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
          TIMESTAMPED CITATIONS
        </div>
      </div>

      <div className="card-body">
        <div className="claims-container">
          {claims.map((claim) => (
            <div key={claim.claim_id} className={`claim-card status-${claim.verification_status}`}>
              <div className="claim-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {getStatusBadge(claim.verification_status)}
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {claim.claim_id}
                  </span>
                </div>
                <div className="claim-source">
                  {claim.publication_date ? `Pub: ${claim.publication_date}` : 'Exchange Disclosure'}
                </div>
              </div>

              <div className="claim-body">{claim.claim_text}</div>

              {claim.contradiction_notes && (
                <div className="claim-contradiction">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                    <ShieldAlert size={14} /> Contradiction Audit Warning:
                  </div>
                  <div>{claim.contradiction_notes}</div>
                </div>
              )}

              <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Source: <strong>{claim.source_name}</strong>
                  {claim.source_url && (
                    <a
                      href={claim.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', marginLeft: '4px' }}
                    >
                      <ExternalLink size={11} />
                    </a>
                  )}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>
                  Confidence: {Math.round(claim.confidence_score * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
