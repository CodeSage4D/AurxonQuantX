import React, { useState, useEffect } from 'react';
import {
  Sliders,
  TrendingUp,
  Layers,
  AlertTriangle,
  RefreshCw,
  Camera,
  BarChart3,
  Zap,
  Info,
} from 'lucide-react';

interface PortfolioHolding {
  symbol: string;
  instrument_name: string;
  sector: string;
  asset_class: string;
  quantity: number;
  average_cost: number;
  current_price: number | null;
  market_value: number | null;
  cost_basis_total: number;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
  realized_pnl: number;
  portfolio_weight_pct: number;
  pricing_status: string;
  data_provider: string;
  price_timestamp: string | null;
}

interface ConcentrationAnalysis {
  top_position_symbol: string | null;
  top_position_weight_pct: number;
  top_3_positions_weight_pct: number;
  herfindahl_index: number;
  sector_weights: Record<string, number>;
  asset_class_weights: Record<string, number>;
  has_concentration_breach: boolean;
  breach_details: string[];
}

interface PerformanceMetrics {
  initial_capital: number;
  current_equity: number;
  total_cash: number;
  cash_reserve_pct: number;
  absolute_return_inr: number;
  total_return_pct: number;
  time_weighted_return_pct: number | null;
  money_weighted_return_pct: number | null;
  annualized_volatility_pct: number | null;
  max_drawdown_pct: number;
  current_drawdown_pct: number;
  peak_equity: number;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  risk_free_rate_pct: number;
  benchmark_symbol: string;
  benchmark_total_return_pct: number | null;
  active_return_pct: number | null;
  tracking_error_pct: number | null;
  information_ratio: number | null;
  portfolio_beta: number | null;
  portfolio_alpha_pct: number | null;
  methodology_notes: string[];
  limitations: string[];
}

interface FactorTile {
  factor_name: string;
  factor_category: string;
  portfolio_exposure_score: number | null;
  benchmark_exposure_score: number | null;
  tilt_status: string;
  input_description: string;
  sample_size_observations: number;
  return_frequency: string;
  data_origin?: string;
  is_available: boolean;
  methodology_notes: string;
  limitations_disclaimer: string;
}

interface FactorAttributionReport {
  portfolio_id: string;
  benchmark_symbol: string;
  as_of_date: string;
  factors: FactorTile[];
  limitations: string[];
}

interface StressScenarioResult {
  scenario_type: string;
  scenario_name: string;
  description: string;
  baseline_equity: number;
  stressed_equity: number;
  estimated_loss_inr: number;
  stressed_loss_pct: number;
  stressed_drawdown_pct: number;
  var_95_pct: number;
  var_99_pct: number;
  risk_limit_breaches: string[];
  disclaimer: string;
}

interface ProposedTrade {
  symbol: string;
  action: string;
  current_quantity: number;
  target_quantity: number;
  share_delta: number;
  estimated_price: number;
  estimated_turnover: number;
  estimated_transaction_costs: number;
  pre_trade_weight_pct: number;
  post_trade_weight_pct: number;
  reason: string;
  pricing_status: string;
}

interface RebalancingSimulationResult {
  portfolio_id: string;
  status: string;
  proposed_trades: ProposedTrade[];
  total_buy_turnover: number;
  total_sell_turnover: number;
  total_estimated_turnover: number;
  total_estimated_transaction_costs: number;
  current_cash: number;
  projected_post_rebalance_cash: number;
  projected_cash_reserve_pct: number;
  portfolio_turnover_pct: number;
  pre_rebalance_weights: Record<string, number>;
  post_rebalance_weights: Record<string, number>;
  qualifications_and_warnings: string[];
  execution_disclaimer: string;
}

export const PortfolioIntelligenceView: React.FC = () => {
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>('DEFAULT');
  const [portfoliosList, setPortfoliosList] = useState<any[]>([]);
  const [subTab, setSubTab] = useState<'HOLDINGS' | 'PERFORMANCE' | 'FACTORS' | 'REBALANCE' | 'STRESS'>('HOLDINGS');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Intelligence Payload States
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [concentration, setConcentration] = useState<ConcentrationAnalysis | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [factors, setFactors] = useState<FactorAttributionReport | null>(null);
  const [stressScenarios, setStressScenarios] = useState<StressScenarioResult[]>([]);
  const [environmentBanner, setEnvironmentBanner] = useState<string>('PAPER TRADING ONLY — SIMULATION ENVIRONMENT');

  // Rebalancing Target State
  const [targetWeights, setTargetWeights] = useState<Record<string, number>>({
    RELIANCE: 0.25,
    TCS: 0.25,
    INFY: 0.25,
    HDFCBANK: 0.15,
  });
  const [cashReserveTarget, setCashReserveTarget] = useState<number>(10.0);
  const [maxPositionLimit, setMaxPositionLimit] = useState<number>(30.0);
  const [simulationResult, setSimulationResult] = useState<RebalancingSimulationResult | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  const fetchPortfoliosList = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/portfolio/list');
      if (res.ok) {
        const data = await res.json();
        setPortfoliosList(data);
      }
    } catch {
      // offline dev fallback
    }
  };

  const fetchPortfolioIntelligence = async (portfolioId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/portfolio/intelligence?portfolio_id=${portfolioId}`);
      if (!res.ok) {
        throw new Error(`Failed to fetch portfolio intelligence: HTTP ${res.status}`);
      }
      const data = await res.json();
      setHoldings(data.holdings || []);
      setConcentration(data.concentration || null);
      setPerformance(data.performance || null);
      setFactors(data.factor_attribution || null);
      setStressScenarios(data.stress_scenarios_summary || []);
      setEnvironmentBanner(data.environment_banner || 'PAPER TRADING ONLY — SIMULATION ENVIRONMENT');
    } catch (err: any) {
      setErrorMessage(err.message || 'Error communicating with intelligence engine');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfoliosList();
    fetchPortfolioIntelligence(selectedPortfolioId);
  }, [selectedPortfolioId]);

  const handleRunRebalanceSimulation = async () => {
    setIsSimulating(true);
    setExecutionMessage(null);
    try {
      const res = await fetch('http://localhost:8000/api/v1/portfolio/rebalance/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: selectedPortfolioId,
          target_weights: targetWeights,
          constraints: {
            max_position_weight_pct: maxPositionLimit,
            target_cash_reserve_pct: cashReserveTarget,
            min_trade_size_inr: 1000.0,
            slippage_bps: 5.0,
          },
        }),
      });
      if (!res.ok) {
        throw new Error(`Rebalance simulation failed: HTTP ${res.status}`);
      }
      const data = await res.json();
      setSimulationResult(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error during rebalancing simulation');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleExecutePaperRebalancing = async () => {
    if (!simulationResult) return;
    try {
      const res = await fetch('http://localhost:8000/api/v1/portfolio/rebalance/execute-paper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(simulationResult),
      });
      if (!res.ok) {
        throw new Error(`Execution failed: HTTP ${res.status}`);
      }
      const executedTrades = await res.json();
      setExecutionMessage(`Successfully executed ${executedTrades.length} simulated trades in paper ledger.`);
      fetchPortfolioIntelligence(selectedPortfolioId);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error executing rebalance in paper ledger');
    }
  };

  const handleTakeSnapshot = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/paper/portfolio?portfolio_id=${selectedPortfolioId}`);
      if (res.ok) {
        fetchPortfolioIntelligence(selectedPortfolioId);
      }
    } catch {
      // ignore
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '24px', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
      {/* Simulation Banner */}
      <div style={{
        background: 'rgba(234, 88, 12, 0.12)',
        border: '1px solid rgba(234, 88, 12, 0.35)',
        padding: '10px 18px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        color: '#fb923c',
        fontSize: '0.82rem',
        fontWeight: 600,
        letterSpacing: '0.04em',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} />
          <span>{environmentBanner}</span>
        </div>
        <span style={{ fontSize: '0.75rem', opacity: 0.85 }}>Real-money execution disabled (ENABLE_REAL_TRADING=false)</span>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          padding: '10px 18px',
          borderRadius: '8px',
          color: '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <AlertTriangle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Header and Portfolio Selector */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
              Portfolio Intelligence &amp; Rebalancing
            </h1>
            <span className="brand-badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.3)' }}>
              AURXON QUANTX
            </span>
          </div>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginTop: '4px' }}>
            Multi-factor attribution, time-weighted performance, concentration limits, and paper-only rebalancing simulator.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dim)' }}>PORTFOLIO:</label>
          <select
            value={selectedPortfolioId}
            onChange={(e) => setSelectedPortfolioId(e.target.value)}
            style={{
              background: 'var(--bg-card)',
              color: 'var(--text-main)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.85rem',
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
            }}
          >
            <option value="DEFAULT">DEFAULT (Primary Paper Ledger)</option>
            {portfoliosList.map((p) => (
              <option key={p.portfolio_id} value={p.portfolio_id}>
                {p.portfolio_id} — {p.name}
              </option>
            ))}
          </select>

          <button
            type="button"
            className="chip-btn"
            onClick={() => fetchPortfolioIntelligence(selectedPortfolioId)}
            title="Refresh Mark-to-Market Intelligence"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} /> Refresh
          </button>

          <button
            type="button"
            className="chip-btn"
            onClick={handleTakeSnapshot}
            title="Record Point-in-Time Snapshot"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Camera size={14} /> Snapshot
          </button>
        </div>
      </div>

      {/* KPI Highlight Grid */}
      {performance && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
          <div className="card" style={{ padding: '16px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Total Equity</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '4px', color: '#38bdf8' }}>
              ₹{performance.current_equity.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Cash: ₹{performance.total_cash.toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({performance.cash_reserve_pct}%)</span>
          </div>

          <div className="card" style={{ padding: '16px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Time-Weighted Return</span>
            <div style={{
              fontSize: '1.4rem',
              fontWeight: 800,
              fontFamily: 'var(--font-mono)',
              marginTop: '4px',
              color: (performance.time_weighted_return_pct || 0) >= 0 ? '#10b981' : '#ef4444'
            }}>
              {(performance.time_weighted_return_pct || 0) >= 0 ? '+' : ''}{performance.time_weighted_return_pct || 0.0}%
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>MWR (IRR): {performance.money_weighted_return_pct || 0.0}%</span>
          </div>

          <div className="card" style={{ padding: '16px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Portfolio Beta</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '4px', color: '#a855f7' }}>
              {performance.portfolio_beta ? `${performance.portfolio_beta}x` : '1.00x'}
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>vs NIFTY 50 (^NSEI)</span>
          </div>

          <div className="card" style={{ padding: '16px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Tracking Error</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '4px', color: '#fbbf24' }}>
              {performance.tracking_error_pct ? `${performance.tracking_error_pct}%` : 'N/A'}
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Active Return: {performance.active_return_pct || 0.0}%</span>
          </div>

          <div className="card" style={{ padding: '16px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase' }}>Max Drawdown</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '4px', color: performance.current_drawdown_pct > 15 ? '#ef4444' : '#10b981' }}>
              {performance.current_drawdown_pct}%
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Peak: ₹{performance.peak_equity.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
          </div>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
        <button
          type="button"
          className={`chip-btn ${subTab === 'HOLDINGS' ? 'active' : ''}`}
          onClick={() => setSubTab('HOLDINGS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Layers size={14} /> Holdings &amp; Concentration ({holdings.length})
        </button>
        <button
          type="button"
          className={`chip-btn ${subTab === 'PERFORMANCE' ? 'active' : ''}`}
          onClick={() => setSubTab('PERFORMANCE')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <TrendingUp size={14} /> Performance &amp; Benchmark
        </button>
        <button
          type="button"
          className={`chip-btn ${subTab === 'FACTORS' ? 'active' : ''}`}
          onClick={() => setSubTab('FACTORS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <BarChart3 size={14} /> Factor Attribution (6)
        </button>
        <button
          type="button"
          className={`chip-btn ${subTab === 'REBALANCE' ? 'active' : ''}`}
          onClick={() => setSubTab('REBALANCE')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Sliders size={14} /> Rebalancing Simulator
        </button>
        <button
          type="button"
          className={`chip-btn ${subTab === 'STRESS' ? 'active' : ''}`}
          onClick={() => setSubTab('STRESS')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Zap size={14} /> Stress Testing Scenarios ({stressScenarios.length})
        </button>
      </div>

      {/* SUB-TAB 1: HOLDINGS & CONCENTRATION */}
      {subTab === 'HOLDINGS' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Concentration Warnings */}
          {concentration?.has_concentration_breach && (
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '12px 16px', borderRadius: '8px', color: '#f87171' }}>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={16} /> Concentration Limit Breach Warning
              </div>
              <ul style={{ marginTop: '6px', fontSize: '0.8rem', paddingLeft: '20px' }}>
                {concentration.breach_details.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Holdings Table */}
          <div className="card" style={{ padding: '20px', overflowX: 'auto' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px' }}>Active Portfolio Inventory</h3>
            {holdings.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-dim)' }}>
                No open positions in portfolio. Use the Paper Trading workstation or Rebalancing Simulator to initiate positions.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)' }}>
                    <th style={{ padding: '8px 12px' }}>TICKER</th>
                    <th style={{ padding: '8px 12px' }}>SECTOR</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>QTY</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>AVG COST</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>PRICE</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>VALUE</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>WEIGHT</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>UNREALIZED P&amp;L</th>
                    <th style={{ padding: '8px 12px' }}>PROVENANCE</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((h) => (
                    <tr key={h.symbol} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                        {h.symbol}
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 400 }}>{h.instrument_name}</div>
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-dim)' }}>{h.sector}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{h.quantity}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{h.average_cost.toFixed(2)}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {h.current_price ? `₹${h.current_price.toFixed(2)}` : 'UNPRICED'}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                        {h.market_value ? `₹${h.market_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : 'N/A'}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {h.portfolio_weight_pct.toFixed(1)}%
                      </td>
                      <td style={{
                        padding: '10px 12px',
                        textAlign: 'right',
                        fontFamily: 'var(--font-mono)',
                        color: (h.unrealized_pnl || 0) >= 0 ? '#10b981' : '#ef4444',
                        fontWeight: 600,
                      }}>
                        {h.unrealized_pnl !== null ? (
                          <>
                            {h.unrealized_pnl >= 0 ? '+' : ''}₹{h.unrealized_pnl.toFixed(0)} ({h.unrealized_pnl_pct}%)
                          </>
                        ) : 'N/A'}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className="brand-badge" style={{ fontSize: '0.65rem' }}>
                          {h.pricing_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Concentration Breakdown Cards */}
          {concentration && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
              <div className="card" style={{ padding: '18px' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px' }}>Sector Allocation Breakdown</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {Object.entries(concentration.sector_weights).map(([sec, wt]) => (
                    <div key={sec} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                        <span>{sec}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{wt}%</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${Math.min(wt, 100)}%`, height: '100%', background: wt > 50 ? '#ef4444' : '#38bdf8' }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card" style={{ padding: '18px' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px' }}>Concentration Risk Metrics</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.82rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Top Holding:</span>
                    <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{concentration.top_position_symbol || 'None'} ({concentration.top_position_weight_pct}%)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Top 3 Concentration:</span>
                    <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{concentration.top_3_positions_weight_pct}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Herfindahl-Hirschman Index (HHI):</span>
                    <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{concentration.herfindahl_index}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-dim)' }}>Asset Allocation:</span>
                    <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      Equity {concentration.asset_class_weights['EQUITY'] || 0}% / Cash {concentration.asset_class_weights['CASH'] || 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 2: PERFORMANCE & BENCHMARK */}
      {subTab === 'PERFORMANCE' && performance && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '12px' }}>Benchmark Tracking &amp; Risk-Adjusted Ratios</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginTop: '10px' }}>
              <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Sharpe Ratio</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                  {performance.sharpe_ratio !== null ? performance.sharpe_ratio : 'N/A'}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Rf baseline = {performance.risk_free_rate_pct}%</span>
              </div>

              <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Sortino Ratio</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                  {performance.sortino_ratio !== null ? performance.sortino_ratio : 'N/A'}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Downside deviation penalized</span>
              </div>

              <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Jensen Alpha (α)</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '4px', color: '#10b981' }}>
                  {performance.portfolio_alpha_pct !== null ? `+${performance.portfolio_alpha_pct}%` : 'N/A'}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Annualized excess return</span>
              </div>

              <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '6px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Information Ratio</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                  {performance.information_ratio !== null ? performance.information_ratio : 'N/A'}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Active Return / Tracking Error</span>
              </div>
            </div>

            <div style={{ marginTop: '20px', padding: '14px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '6px', fontSize: '0.8rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} /> Methodology Notes &amp; Statutory Caveats
              </div>
              <ul style={{ paddingLeft: '18px', color: 'var(--text-dim)' }}>
                {performance.methodology_notes.map((n, i) => <li key={i}>{n}</li>)}
                {performance.limitations.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: FACTOR ATTRIBUTION */}
      {subTab === 'FACTORS' && factors && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {factors.factors.map((f) => (
              <div key={f.factor_name} className="card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-dim)' }}>{f.factor_category}</span>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      {f.data_origin && (
                        <span className="brand-badge" style={{ fontSize: '0.68rem', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.25)' }}>
                          {f.data_origin}
                        </span>
                      )}
                      <span className="brand-badge" style={{
                        background: f.tilt_status === 'OVERWEIGHT' ? 'rgba(16, 185, 129, 0.15)' : (f.tilt_status === 'UNDERWEIGHT' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.05)'),
                        color: f.tilt_status === 'OVERWEIGHT' ? '#10b981' : (f.tilt_status === 'UNDERWEIGHT' ? '#ef4444' : 'var(--text-main)')
                      }}>
                        {f.tilt_status}
                      </span>
                    </div>
                  </div>
                  <h4 style={{ fontSize: '1.1rem', fontWeight: 800, marginTop: '6px' }}>{f.factor_name}</h4>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-mono)', margin: '8px 0', color: '#38bdf8' }}>
                    {f.portfolio_exposure_score !== null ? f.portfolio_exposure_score : 'UNAVAILABLE'}
                    <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-dim)', marginLeft: '8px' }}>
                      (BM: {f.benchmark_exposure_score})
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', lineHeight: 1.4 }}>{f.input_description}</p>
                </div>
                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                  <span>Sample: {f.sample_size_observations} obs ({f.return_frequency})</span>
                  <div style={{ fontStyle: 'italic', marginTop: '4px' }}>{f.limitations_disclaimer}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SUB-TAB 4: REBALANCING SIMULATOR */}
      {subTab === 'REBALANCE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Target Allocation Editor */}
          <div className="card" style={{ padding: '20px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '6px' }}>Simulated Target Allocation &amp; Constraints</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginBottom: '16px' }}>
              Set desired portfolio weights across benchmark equities and target cash reserve. The simulator computes integer lots, models statutory transaction drag, and verifies position ceilings.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
              {['RELIANCE', 'TCS', 'INFY', 'HDFCBANK'].map((ticker) => (
                <div key={ticker} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-dim)' }}>{ticker} WEIGHT (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={Math.round((targetWeights[ticker] || 0) * 100)}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0;
                      setTargetWeights({ ...targetWeights, [ticker]: val / 100.0 });
                    }}
                    style={{
                      background: 'var(--bg-primary)',
                      color: 'var(--text-main)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      padding: '8px 12px',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                    }}
                  />
                </div>
              ))}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-dim)' }}>CASH RESERVE (%)</label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  step="1"
                  value={cashReserveTarget}
                  onChange={(e) => setCashReserveTarget(parseFloat(e.target.value) || 10.0)}
                  style={{
                    background: 'var(--bg-primary)',
                    color: 'var(--text-main)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                  }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-dim)' }}>MAX POSITION CAP (%)</label>
                <input
                  type="number"
                  min="10"
                  max="50"
                  step="5"
                  value={maxPositionLimit}
                  onChange={(e) => setMaxPositionLimit(parseFloat(e.target.value) || 30.0)}
                  style={{
                    background: 'var(--bg-primary)',
                    color: 'var(--text-main)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 600,
                  }}
                />
              </div>
            </div>

            <div style={{ marginTop: '18px', display: 'flex', gap: '12px' }}>
              <button
                type="button"
                className="chip-btn active"
                onClick={handleRunRebalanceSimulation}
                disabled={isSimulating}
                style={{ padding: '8px 20px', fontSize: '0.85rem', fontWeight: 700 }}
              >
                {isSimulating ? 'Simulating...' : 'Run Rebalance Simulation'}
              </button>
            </div>
          </div>

          {/* Rebalancing Simulation Results */}
          {simulationResult && (
            <div className="card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
                  Proposed Rebalance Execution Plan
                </h3>
                <span className="brand-badge" style={{
                  background: simulationResult.status === 'FEASIBLE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(234, 88, 12, 0.15)',
                  color: simulationResult.status === 'FEASIBLE' ? '#10b981' : '#fb923c'
                }}>
                  {simulationResult.status}
                </span>
              </div>

              {simulationResult.qualifications_and_warnings.length > 0 && (
                <div style={{ background: 'rgba(234, 88, 12, 0.08)', border: '1px solid rgba(234, 88, 12, 0.25)', padding: '10px 14px', borderRadius: '6px', marginBottom: '14px', fontSize: '0.8rem', color: '#fb923c' }}>
                  {simulationResult.qualifications_and_warnings.map((w, i) => (
                    <div key={i}>• {w}</div>
                  ))}
                </div>
              )}

              {/* Proposed Trades Table */}
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem', marginBottom: '16px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)' }}>
                    <th style={{ padding: '8px 10px' }}>ACTION</th>
                    <th style={{ padding: '8px 10px' }}>TICKER</th>
                    <th style={{ padding: '8px 10px', textAlign: 'right' }}>UNITS</th>
                    <th style={{ padding: '8px 10px', textAlign: 'right' }}>PRICE</th>
                    <th style={{ padding: '8px 10px', textAlign: 'right' }}>TURNOVER</th>
                    <th style={{ padding: '8px 10px', textAlign: 'right' }}>EST. COSTS</th>
                    <th style={{ padding: '8px 10px', textAlign: 'right' }}>PRE → POST WT</th>
                    <th style={{ padding: '8px 10px' }}>RATIONALE</th>
                  </tr>
                </thead>
                <tbody>
                  {simulationResult.proposed_trades.map((t, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '8px 10px' }}>
                        <span style={{
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          background: t.action === 'BUY' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: t.action === 'BUY' ? '#10b981' : '#ef4444'
                        }}>
                          {t.action}
                        </span>
                      </td>
                      <td style={{ padding: '8px 10px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{t.symbol}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{t.share_delta}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{t.estimated_price.toFixed(2)}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{t.estimated_turnover.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>₹{t.estimated_transaction_costs.toFixed(2)}</td>
                      <td style={{ padding: '8px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                        {t.pre_trade_weight_pct}% → <strong>{t.post_trade_weight_pct}%</strong>
                      </td>
                      <td style={{ padding: '8px 10px', fontSize: '0.78rem', color: 'var(--text-dim)' }}>{t.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                  Total Turnover: ₹{simulationResult.total_estimated_turnover.toLocaleString('en-IN', { maximumFractionDigits: 0 })} |
                  Costs: ₹{simulationResult.total_estimated_transaction_costs.toFixed(2)} |
                  Projected Cash: ₹{simulationResult.projected_post_rebalance_cash.toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({simulationResult.projected_cash_reserve_pct}%)
                </div>

                <button
                  type="button"
                  className="chip-btn active"
                  onClick={handleExecutePaperRebalancing}
                  style={{ padding: '8px 20px', background: '#10b981', color: '#ffffff', fontWeight: 700 }}
                >
                  Execute in Paper Ledger
                </button>
              </div>

              {executionMessage && (
                <div style={{ marginTop: '12px', padding: '10px 14px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '6px', color: '#10b981', fontSize: '0.82rem' }}>
                  ✓ {executionMessage}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 5: STRESS TESTING */}
      {subTab === 'STRESS' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {stressScenarios.map((s) => (
              <div key={s.scenario_type} className="card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ef4444' }}>STRESS SCENARIO</span>
                    <span className="brand-badge" style={{ fontSize: '0.65rem' }}>SIMULATION</span>
                  </div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 800, marginTop: '6px' }}>{s.scenario_name}</h4>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', margin: '8px 0', lineHeight: 1.4 }}>{s.description}</p>

                  <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '6px', marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-dim)' }}>Stressed Equity:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#f87171' }}>
                        ₹{s.stressed_equity.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-dim)' }}>Projected Loss:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#f87171' }}>
                        -₹{s.estimated_loss_inr.toLocaleString('en-IN', { maximumFractionDigits: 0 })} (-{s.stressed_loss_pct}%)
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-dim)' }}>Stressed Drawdown:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{s.stressed_drawdown_pct}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-dim)' }}>1-Day VaR (95% / 99%):</span>
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{s.var_95_pct}% / {s.var_99_pct}%</span>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', fontSize: '0.7rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                  {s.disclaimer}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
