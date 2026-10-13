import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Play,
  Power,
  Briefcase,
  Clock,
  CheckCircle,
  XCircle,
  Layers,
  RefreshCw,
} from 'lucide-react';

interface PaperPosition {
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  realized_pnl: number;
  portfolio_weight_pct: number;
  last_updated_at: string;
}

interface PaperOrder {
  order_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT';
  quantity: number;
  limit_price?: number;
  status: 'PENDING' | 'SUBMITTED' | 'FILLED' | 'REJECTED' | 'CANCELLED';
  submitted_at: string;
  fill_price?: number;
  executed_quantity: number;
  turnover: number;
  transaction_costs: number;
  rejection_reason?: string;
  data_provenance: string;
  data_classification: string;
  is_demonstration: boolean;
  notes?: string;
}

interface RiskLimits {
  max_order_value_inr: number;
  max_position_weight_pct: number;
  max_daily_loss_inr: number;
  kill_switch_active: boolean;
}

interface PaperPortfolioState {
  portfolio_id: string;
  name: string;
  initial_cash: number;
  current_cash: number;
  positions_value: number;
  total_equity: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_transaction_costs_paid: number;
  kill_switch_active: boolean;
  risk_limits: RiskLimits;
  environment_banner: string;
  positions: Record<string, PaperPosition>;
  open_orders_count: number;
  total_orders_count: number;
}

export const PaperTradingView: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PaperPortfolioState | null>(null);
  const [orders, setOrders] = useState<PaperOrder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Order Form State
  const [symbol, setSymbol] = useState('RELIANCE');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState(10);
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [limitPrice, setLimitPrice] = useState<string>('');

  // Corporate Action State
  const [caSymbol, setCaSymbol] = useState('RELIANCE');
  const [caType, setCaType] = useState<'CASH_DIVIDEND' | 'BONUS_ISSUE'>('CASH_DIVIDEND');
  const [caAmount, setCaAmount] = useState(15.0);

  const fetchPortfolio = async () => {
    try {
      const res = await fetch('/api/v1/paper/portfolio');
      if (res.ok) {
        const data = await res.json();
        setPortfolio(data);
      }
      const ordersRes = await fetch('/api/v1/paper/orders');
      if (ordersRes.ok) {
        const ordersData = await ordersRes.json();
        setOrders(ordersData);
      }
    } catch (err) {
      console.error('Failed to fetch paper portfolio state', err);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const handleOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setFeedbackMsg(null);

    const payload = {
      portfolio_id: 'DEFAULT',
      symbol: symbol.trim().toUpperCase(),
      side,
      quantity: Number(quantity),
      order_type: orderType,
      limit_price: orderType === 'LIMIT' && limitPrice ? Number(limitPrice) : undefined,
      idempotency_key: `UI-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    };

    try {
      const res = await fetch('/api/v1/paper/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const orderData: PaperOrder = await res.json();
      if (res.ok) {
        if (orderData.status === 'FILLED') {
          setFeedbackMsg({
            type: 'success',
            text: `Order FILLED: ${orderData.side} ${orderData.quantity} ${orderData.symbol} @ ₹${orderData.fill_price?.toFixed(2)} (Friction: ₹${orderData.transaction_costs.toFixed(2)})`,
          });
        } else if (orderData.status === 'REJECTED') {
          setFeedbackMsg({
            type: 'error',
            text: `Order REJECTED: ${orderData.rejection_reason}`,
          });
        } else {
          setFeedbackMsg({
            type: 'success',
            text: `Order placed in state: ${orderData.status}`,
          });
        }
        await fetchPortfolio();
      } else {
        setFeedbackMsg({ type: 'error', text: `Error: ${JSON.stringify(orderData)}` });
      }
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: `Failed to submit order: ${err.message}` });
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleKillSwitch = async () => {
    if (!portfolio) return;
    const newStatus = !portfolio.kill_switch_active;
    try {
      const res = await fetch('/api/v1/paper/kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: 'DEFAULT',
          active: newStatus,
          reason: newStatus ? 'Operator engaged emergency kill switch' : 'Operator disengaged kill switch',
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setPortfolio(updated);
        setFeedbackMsg({
          type: newStatus ? 'error' : 'success',
          text: newStatus ? 'EMERGENCY KILL SWITCH ENGAGED — Simulated orders blocked' : 'Kill switch disengaged',
        });
      }
    } catch (err) {
      console.error('Failed to toggle kill switch', err);
    }
  };

  const handleApplyCorporateAction = async () => {
    try {
      const res = await fetch('/api/v1/paper/corporate-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: 'DEFAULT',
          symbol: caSymbol,
          action_type: caType,
          dividend_amount_inr: caType === 'CASH_DIVIDEND' ? caAmount : undefined,
          split_ratio: caType === 'BONUS_ISSUE' ? 2.0 : undefined,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setFeedbackMsg({
          type: 'success',
          text: `Corporate action applied: ${JSON.stringify(data)}`,
        });
        await fetchPortfolio();
      } else {
        setFeedbackMsg({
          type: 'error',
          text: `Corporate action failed: ${data.detail || data.message}`,
        });
      }
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message });
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset paper portfolio to initial ₹10,00,000 cash? All virtual positions and orders will be cleared.')) return;
    try {
      const res = await fetch('/api/v1/paper/reset', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setPortfolio(data);
        setFeedbackMsg({ type: 'success', text: 'Virtual paper portfolio reset to ₹10,00,000 cash.' });
        await fetchPortfolio();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. PAPER TRADING ENVIRONMENT BANNER */}
      <div
        style={{
          background: 'linear-gradient(90deg, rgba(234, 88, 12, 0.15) 0%, rgba(20, 24, 33, 0.9) 100%)',
          border: '1px solid rgba(234, 88, 12, 0.4)',
          borderRadius: '8px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              background: 'rgba(234, 88, 12, 0.25)',
              padding: '10px',
              borderRadius: '8px',
              color: '#fb923c',
            }}
          >
            <ShieldAlert size={26} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 800, letterSpacing: '0.08em', color: '#fb923c' }}>
                PAPER TRADING ONLY — SIMULATION ENVIRONMENT
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(234, 88, 12, 0.2)',
                  color: '#fdba74',
                  fontWeight: 700,
                }}
              >
                RESEARCH STAGE 2
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              All virtual cash balances, executions, and positions are simulated locally. Real-money live broker order routing is blocked.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={fetchPortfolio}
            className="chip-btn"
            style={{ padding: '8px 14px', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={13} />
            <span>Refresh State</span>
          </button>
          <button
            type="button"
            onClick={handleToggleKillSwitch}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              border: portfolio?.kill_switch_active ? '1px solid #ef4444' : '1px solid rgba(234, 88, 12, 0.5)',
              background: portfolio?.kill_switch_active ? 'rgba(239, 68, 68, 0.25)' : 'rgba(234, 88, 12, 0.2)',
              color: portfolio?.kill_switch_active ? '#fca5a5' : '#fdba74',
            }}
          >
            <Power size={14} />
            <span>{portfolio?.kill_switch_active ? 'KILL SWITCH ENGAGED' : 'ENGAGE KILL SWITCH'}</span>
          </button>
        </div>
      </div>

      {/* Feedback Toast */}
      {feedbackMsg && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '6px',
            fontSize: '0.85rem',
            background: feedbackMsg.type === 'success' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: feedbackMsg.type === 'success' ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
            color: feedbackMsg.type === 'success' ? '#86efac' : '#fca5a5',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {feedbackMsg.type === 'success' ? <CheckCircle size={16} /> : <XCircle size={16} />}
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* 2. PORTFOLIO SNAPSHOT METRIC CARDS */}
      {portfolio && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
          <div className="glass-card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>VIRTUAL CASH</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '4px', color: 'var(--accent-cyan)' }}>
              ₹{portfolio.current_cash.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Initial: ₹{portfolio.initial_cash.toLocaleString('en-IN')}
            </div>
          </div>

          <div className="glass-card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>POSITIONS VALUE</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '4px', color: 'var(--text-main)' }}>
              ₹{portfolio.positions_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {Object.keys(portfolio.positions).length} Active Holdings
            </div>
          </div>

          <div className="glass-card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>PORTFOLIO EQUITY</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '4px', color: 'var(--text-main)' }}>
              ₹{portfolio.total_equity.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Cash + Position Mark-to-Market
            </div>
          </div>

          <div className="glass-card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>REALIZED P&L</div>
            <div
              style={{
                fontSize: '1.35rem',
                fontWeight: 800,
                marginTop: '4px',
                color: portfolio.total_realized_pnl >= 0 ? '#4ade80' : '#f87171',
              }}
            >
              {portfolio.total_realized_pnl >= 0 ? '+' : ''}₹{portfolio.total_realized_pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Closed FIFO Round-Trips
            </div>
          </div>

          <div className="glass-card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>UNREALIZED P&L</div>
            <div
              style={{
                fontSize: '1.35rem',
                fontWeight: 800,
                marginTop: '4px',
                color: portfolio.total_unrealized_pnl >= 0 ? '#4ade80' : '#f87171',
              }}
            >
              {portfolio.total_unrealized_pnl >= 0 ? '+' : ''}₹{portfolio.total_unrealized_pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Marked to Benchmark Feeds
            </div>
          </div>

          <div className="glass-card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>STATUTORY FRICTION PAID</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, marginTop: '4px', color: '#fb923c' }}>
              ₹{portfolio.total_transaction_costs_paid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              STT, Stamp Duty, NSE Txn, GST
            </div>
          </div>
        </div>
      )}

      {/* 3. MAIN WORKSPACE (2 COLUMNS) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '20px' }}>
        {/* Left Column: Order Submission & Corporate Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Order Placement Form */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <Play size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Simulate Order Placement</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>IDEMPOTENT REST LEDGER</div>
            </div>
            <div className="card-body">
              <form onSubmit={handleOrderSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                      SYMBOL
                    </label>
                    <select
                      value={symbol}
                      onChange={(e) => {
                        setSymbol(e.target.value);
                        setCaSymbol(e.target.value);
                      }}
                      style={{
                        width: '100%',
                        padding: '8px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-main)',
                      }}
                    >
                      <option value="RELIANCE">RELIANCE (NSE Benchmark)</option>
                      <option value="TCS">TCS (NSE Benchmark)</option>
                      <option value="NIFTY50_INDEX">NIFTY50_INDEX (Benchmark)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                      SIDE
                    </label>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        type="button"
                        onClick={() => setSide('BUY')}
                        style={{
                          flex: 1,
                          padding: '8px',
                          borderRadius: '4px',
                          border: side === 'BUY' ? '1px solid #22c55e' : '1px solid var(--border-subtle)',
                          background: side === 'BUY' ? 'rgba(34, 197, 94, 0.25)' : 'rgba(0,0,0,0.3)',
                          color: side === 'BUY' ? '#86efac' : 'var(--text-dim)',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        BUY
                      </button>
                      <button
                        type="button"
                        onClick={() => setSide('SELL')}
                        style={{
                          flex: 1,
                          padding: '8px',
                          borderRadius: '4px',
                          border: side === 'SELL' ? '1px solid #ef4444' : '1px solid var(--border-subtle)',
                          background: side === 'SELL' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(0,0,0,0.3)',
                          color: side === 'SELL' ? '#fca5a5' : 'var(--text-dim)',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        SELL
                      </button>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                      QUANTITY (SHARES)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="1000"
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                      style={{
                        width: '100%',
                        padding: '8px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-main)',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                      ORDER TYPE
                    </label>
                    <select
                      value={orderType}
                      onChange={(e) => setOrderType(e.target.value as 'MARKET' | 'LIMIT')}
                      style={{
                        width: '100%',
                        padding: '8px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-main)',
                      }}
                    >
                      <option value="MARKET">MARKET</option>
                      <option value="LIMIT">LIMIT</option>
                    </select>
                  </div>
                </div>

                {orderType === 'LIMIT' && (
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                      LIMIT PRICE (₹)
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      placeholder="e.g. 2950.00"
                      value={limitPrice}
                      onChange={(e) => setLimitPrice(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        color: 'var(--text-main)',
                      }}
                    />
                  </div>
                )}

                <div
                  style={{
                    fontSize: '0.72rem',
                    color: 'var(--text-dim)',
                    background: 'rgba(255,255,255,0.02)',
                    padding: '8px',
                    borderRadius: '4px',
                  }}
                >
                  Statutory Costs Applied: STT 0.1%, Stamp Duty 0.015% (Buy), NSE Txn 0.00297%, GST 18%, Slippage 5 bps.
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  style={{
                    padding: '10px',
                    borderRadius: '6px',
                    background: side === 'BUY' ? 'linear-gradient(90deg, #16a34a, #22c55e)' : 'linear-gradient(90deg, #dc2626, #ef4444)',
                    color: '#fff',
                    fontWeight: 700,
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {isLoading ? 'Executing Simulation...' : `Submit Simulated ${side} Order`}
                </button>
              </form>
            </div>
          </div>

          {/* Simulate Corporate Action Card */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <Layers size={18} style={{ color: 'var(--accent-purple)' }} />
                <span>Simulate Corporate Action</span>
              </div>
            </div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                    TARGET HOLDING
                  </label>
                  <select
                    value={caSymbol}
                    onChange={(e) => setCaSymbol(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-main)',
                    }}
                  >
                    <option value="RELIANCE">RELIANCE</option>
                    <option value="TCS">TCS</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                    EVENT TYPE
                  </label>
                  <select
                    value={caType}
                    onChange={(e) => setCaType(e.target.value as any)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-main)',
                    }}
                  >
                    <option value="CASH_DIVIDEND">Interim Dividend</option>
                    <option value="BONUS_ISSUE">1:1 Bonus Issue</option>
                  </select>
                </div>
              </div>

              {caType === 'CASH_DIVIDEND' && (
                <div>
                  <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                    DIVIDEND PER SHARE (₹)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={caAmount}
                    onChange={(e) => setCaAmount(parseFloat(e.target.value) || 0)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '4px',
                      color: 'var(--text-main)',
                    }}
                  />
                </div>
              )}

              <button
                type="button"
                onClick={handleApplyCorporateAction}
                className="chip-btn"
                style={{ padding: '8px 12px', fontSize: '0.8rem', fontWeight: 700 }}
              >
                Apply Corporate Action to Virtual Holdings
              </button>
            </div>
          </div>

          {/* Reset Portfolio */}
          <div style={{ textAlign: 'right' }}>
            <button
              type="button"
              onClick={handleReset}
              style={{
                background: 'transparent',
                border: '1px solid rgba(255,255,255,0.1)',
                color: 'var(--text-dim)',
                fontSize: '0.75rem',
                padding: '6px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Reset Virtual Portfolio
            </button>
          </div>
        </div>

        {/* Right Column: Open Positions & Order History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Open Positions Table */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <Briefcase size={18} style={{ color: 'var(--accent-cyan)' }} />
                <span>Open Virtual Positions</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                {portfolio ? Object.keys(portfolio.positions).length : 0} INSTRUMENTS
              </div>
            </div>
            <div className="card-body" style={{ overflowX: 'auto' }}>
              {portfolio && Object.keys(portfolio.positions).length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)', textAlign: 'left' }}>
                      <th style={{ padding: '8px 6px' }}>SYMBOL</th>
                      <th style={{ padding: '8px 6px' }}>QTY</th>
                      <th style={{ padding: '8px 6px' }}>AVG COST</th>
                      <th style={{ padding: '8px 6px' }}>LATEST PRICE</th>
                      <th style={{ padding: '8px 6px' }}>VALUE</th>
                      <th style={{ padding: '8px 6px' }}>UNREALIZED</th>
                      <th style={{ padding: '8px 6px' }}>WEIGHT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.values(portfolio.positions).map((pos) => (
                      <tr key={pos.symbol} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ padding: '10px 6px', fontWeight: 700 }}>{pos.symbol}</td>
                        <td style={{ padding: '10px 6px' }}>{pos.quantity}</td>
                        <td style={{ padding: '10px 6px' }}>₹{pos.average_cost.toFixed(2)}</td>
                        <td style={{ padding: '10px 6px' }}>₹{pos.current_price.toFixed(2)}</td>
                        <td style={{ padding: '10px 6px' }}>₹{pos.market_value.toLocaleString('en-IN')}</td>
                        <td
                          style={{
                            padding: '10px 6px',
                            color: pos.unrealized_pnl >= 0 ? '#4ade80' : '#f87171',
                            fontWeight: 700,
                          }}
                        >
                          {pos.unrealized_pnl >= 0 ? '+' : ''}₹{pos.unrealized_pnl.toFixed(2)} ({pos.unrealized_pnl_pct}%)
                        </td>
                        <td style={{ padding: '10px 6px' }}>{pos.portfolio_weight_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No open positions. Submit simulated buy orders to construct virtual portfolio.
                </div>
              )}
            </div>
          </div>

          {/* Order Lifecycle History */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <Clock size={18} style={{ color: 'var(--accent-orange)' }} />
                <span>Simulated Order Audit Trail</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{orders.length} EVENTS</div>
            </div>
            <div className="card-body" style={{ overflowX: 'auto', maxHeight: '420px', overflowY: 'auto' }}>
              {orders.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)', textAlign: 'left' }}>
                      <th style={{ padding: '6px' }}>ORDER ID</th>
                      <th style={{ padding: '6px' }}>ACTION</th>
                      <th style={{ padding: '6px' }}>STATUS</th>
                      <th style={{ padding: '6px' }}>FILL / LIMIT</th>
                      <th style={{ padding: '6px' }}>TURNOVER</th>
                      <th style={{ padding: '6px' }}>FRICTION</th>
                      <th style={{ padding: '6px' }}>PROVENANCE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((ord) => (
                      <tr key={ord.order_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ padding: '8px 6px', fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                          {ord.order_id.replace('ORD-PAP-', '')}
                        </td>
                        <td style={{ padding: '8px 6px', fontWeight: 700 }}>
                          <span style={{ color: ord.side === 'BUY' ? '#4ade80' : '#f87171' }}>{ord.side}</span> {ord.quantity} {ord.symbol}
                        </td>
                        <td style={{ padding: '8px 6px' }}>
                          <span
                            style={{
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '0.65rem',
                              fontWeight: 700,
                              background:
                                ord.status === 'FILLED'
                                  ? 'rgba(34, 197, 94, 0.15)'
                                  : ord.status === 'REJECTED'
                                  ? 'rgba(239, 68, 68, 0.15)'
                                  : 'rgba(234, 88, 12, 0.15)',
                              color:
                                ord.status === 'FILLED'
                                  ? '#86efac'
                                  : ord.status === 'REJECTED'
                                  ? '#fca5a5'
                                  : '#fdba74',
                            }}
                          >
                            {ord.status}
                          </span>
                        </td>
                        <td style={{ padding: '8px 6px' }}>
                          {ord.fill_price ? `₹${ord.fill_price.toFixed(2)}` : ord.limit_price ? `Lim: ₹${ord.limit_price}` : '—'}
                        </td>
                        <td style={{ padding: '8px 6px' }}>
                          {ord.turnover > 0 ? `₹${ord.turnover.toLocaleString('en-IN')}` : '—'}
                        </td>
                        <td style={{ padding: '8px 6px' }}>
                          {ord.transaction_costs > 0 ? `₹${ord.transaction_costs.toFixed(2)}` : '—'}
                        </td>
                        <td style={{ padding: '8px 6px', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                          {ord.rejection_reason ? (
                            <span style={{ color: '#fca5a5' }}>{ord.rejection_reason}</span>
                          ) : (
                            <span>{ord.data_provenance}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  No order activity recorded in this session.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
