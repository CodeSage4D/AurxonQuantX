import React, { useEffect, useState } from 'react';
import { AuditRecordSummary } from '../types';
import { FileText, X, Hash } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const AuditLedgerModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [records, setRecords] = useState<AuditRecordSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetch('/api/v1/audit/records?limit=30')
        .then((res) => res.json())
        .then((data) => {
          setRecords(data);
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px',
      }}
    >
      <div
        className="glass-card"
        style={{
          width: '900px',
          maxHeight: '85vh',
          background: 'hsl(222, 28%, 9%)',
          border: '1px solid var(--border-card)',
        }}
      >
        <div className="card-header">
          <div className="card-title">
            <FileText size={20} style={{ color: 'var(--accent-cyan)' }} />
            <span>Immutable Audit Ledger (SQLite + SHA-256)</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="chip-btn"
            style={{ padding: '4px 8px' }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="card-body" style={{ overflowY: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              Loading cryptographic ledger records...
            </div>
          ) : records.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
              No audit records stored yet.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px 10px' }}>AUDIT ID</th>
                  <th style={{ padding: '8px 10px' }}>TICKER</th>
                  <th style={{ padding: '8px 10px' }}>DECISION</th>
                  <th style={{ padding: '8px 10px' }}>PRICE</th>
                  <th style={{ padding: '8px 10px' }}>DCF VALUE</th>
                  <th style={{ padding: '8px 10px' }}>EVIDENCE SCORE</th>
                  <th style={{ padding: '8px 10px' }}>SHA-256 HASH</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => (
                  <tr key={rec.audit_id} style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.4)' }}>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                      {rec.audit_id}
                    </td>
                    <td style={{ padding: '10px', fontWeight: 600 }}>{rec.ticker}</td>
                    <td style={{ padding: '10px' }}>
                      <span className={`badge rec-${rec.recommendation}`}>{rec.recommendation}</span>
                    </td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>₹{rec.current_price.toFixed(2)}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>₹{rec.fair_value_dcf.toFixed(2)}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                      {Math.round(rec.evidence_score * 100)}%
                    </td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                      <span title={rec.content_sha256} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Hash size={11} /> {rec.content_sha256.slice(0, 10)}...
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
