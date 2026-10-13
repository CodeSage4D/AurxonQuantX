import React, { useEffect, useState } from 'react';
import { SourceRegistration } from '../types';
import { Database, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SourcesInspectionModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [sources, setSources] = useState<SourceRegistration[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetch('/api/v1/sources')
        .then((res) => res.json())
        .then((data) => {
          setSources(data);
          setLoading(false);
        })
        .catch(() => setLoading(false));
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
          width: '950px',
          maxHeight: '85vh',
          background: 'hsl(222, 28%, 9%)',
          border: '1px solid var(--border-card)',
        }}
      >
        <div className="card-header">
          <div className="card-title">
            <Database size={20} style={{ color: 'var(--accent-cyan)' }} />
            <span>AURXON Source Registry & Access Governance</span>
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
              Loading registered data sources...
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px 10px' }}>SOURCE ID</th>
                  <th style={{ padding: '8px 10px' }}>NAME</th>
                  <th style={{ padding: '8px 10px' }}>CATEGORY</th>
                  <th style={{ padding: '8px 10px' }}>ACCESS</th>
                  <th style={{ padding: '8px 10px' }}>RELIABILITY</th>
                  <th style={{ padding: '8px 10px' }}>CADENCE</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((src) => (
                  <tr key={src.source_id} style={{ borderBottom: '1px solid hsla(220, 20%, 20%, 0.4)' }}>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                      {src.source_id}
                    </td>
                    <td style={{ padding: '10px', fontWeight: 600 }}>{src.name}</td>
                    <td style={{ padding: '10px' }}>
                      <span className="badge badge-verified">{src.category}</span>
                    </td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>{src.access_method}</td>
                    <td style={{ padding: '10px', fontFamily: 'var(--font-mono)' }}>
                      {Math.round(src.reliability_weight * 100)}%
                    </td>
                    <td style={{ padding: '10px', color: 'var(--text-dim)' }}>{src.update_frequency}</td>
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
