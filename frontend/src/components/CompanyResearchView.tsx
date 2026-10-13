import React, { useState } from 'react';
import {
  Search,
  Building2,
  AlertTriangle,
  BookOpen,
  Scale,
  Activity,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  HelpCircle,
  ExternalLink,
  CheckCircle,
  XCircle,
  Sparkles,
} from 'lucide-react';


interface CompanyIdentity {
  cin?: string;
  isin?: string;
  legal_name: string;
  trade_name: string;
  nse_symbol?: string;
  bse_code?: string;
  primary_exchange: string;
  listing_status: string;
  security_type: string;
  sector: string;
  industry: string;
  aliases: string[];
  historical_names: string[];
  website_ir?: string;
}

interface SpecialistPerspective {
  role: string;
  analyst_name: string;
  sentiment: string;
  confidence_score: number;
  key_findings: string[];
  supporting_citations: string[];
  missing_data_warnings: string[];
  invalidation_conditions: string[];
}

interface ScenarioAnalysis {
  bull_case: string;
  bull_fair_value_est?: number;
  bull_catalysts: string[];
  base_case: string;
  base_fair_value_est?: number;
  base_assumptions: string[];
  bear_case: string;
  bear_fair_value_est?: number;
  bear_risks: string[];
  downside_protection_buffer_pct?: number;
}

interface PaperTradingTicket {
  is_eligible: boolean;
  ticker: string;
  exchange: string;
  as_of_price?: number;
  price_freshness: string;
  data_classification: string;
  gate_checks_passed: string[];
  veto_reasons: string[];
  max_recommended_allocation_pct: number;
  audit_timestamp: string;
}

interface CompanyResearchReport {
  report_id: string;
  company: CompanyIdentity;
  as_of_timestamp: string;
  retrieval_timestamp: string;
  data_freshness: string;
  data_classification: string;
  current_price?: number;
  market_cap_cr?: number;
  pe_ratio?: number;
  pb_ratio?: number;
  dividend_yield_pct?: number;
  eps_ttm?: number;
  book_value_per_share?: number;
  debt_to_equity?: number;
  roe_pct?: number;
  returns_1m_pct?: number;
  returns_6m_pct?: number;
  returns_1y_pct?: number;
  volatility_annualized_pct?: number;
  max_drawdown_1y_pct?: number;
  relative_strength_vs_nifty?: string;
  trend_regime: string;
  specialist_perspectives: SpecialistPerspective[];
  scenarios: ScenarioAnalysis;
  key_catalysts: string[];
  downside_risks: string[];
  adversarial_counterarguments: string[];
  source_citations: {
    title: string;
    source: string;
    url: string;
    date: string;
    excerpt: string;
  }[];
  paper_trading_ticket: PaperTradingTicket;
  provenance_disclaimer: string;
}

interface ResolutionResult {
  query: string;
  is_resolved: boolean;
  is_ambiguous: boolean;
  resolved_company?: CompanyIdentity;
  candidates: CompanyIdentity[];
  ambiguity_reason?: string;
  clarification_prompt?: string;
}

const getClassificationBadge = (classification: string) => {
  switch (classification) {
    case 'LIVE_VERIFIED':
      return { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'LIVE VERIFIED' };
    case 'DELAYED_VERIFIED':
      return { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', label: 'DELAYED (15m)' };
    case 'HISTORICAL_VERIFIED':
      return { bg: 'bg-cyan-500/15', text: 'text-cyan-400', border: 'border-cyan-500/30', label: 'HISTORICAL VERIFIED' };
    case 'CACHED':
      return { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30', label: 'LOCAL CACHED' };
    case 'SYNTHETIC_BENCHMARK':
      return { bg: 'bg-purple-500/15', text: 'text-purple-400', border: 'border-purple-500/30', label: 'BENCHMARK ARCHIVE' };
    case 'SIMULATED':
      return { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30', label: 'SIMULATED' };
    case 'UNAVAILABLE':
    default:
      return { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30', label: classification || 'UNAVAILABLE' };
  }
};

export const CompanyResearchView: React.FC = () => {
  const [query, setQuery] = useState('TCS');
  const [report, setReport] = useState<CompanyResearchReport | null>(null);
  const [ambiguity, setAmbiguity] = useState<ResolutionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeSearch = async (targetQuery: string) => {
    setLoading(true);
    setError(null);
    setAmbiguity(null);

    try {
      // 1. Check ambiguity first
      const resResp = await fetch(`/api/v1/company/resolve?q=${encodeURIComponent(targetQuery)}`);
      const resData: ResolutionResult = await resResp.json();

      if (resData.is_ambiguous) {
        setAmbiguity(resData);
        setLoading(false);
        return;
      }

      if (!resData.is_resolved) {
        setError(resData.ambiguity_reason || `Could not resolve company for '${targetQuery}'`);
        setLoading(false);
        return;
      }

      // 2. Fetch full research report
      const repResp = await fetch(`/api/v1/company/research/${encodeURIComponent(targetQuery)}`);
      if (!repResp.ok) {
        const errDetail = await repResp.json();
        throw new Error(errDetail.detail || 'Failed to conduct company research.');
      }
      const repData: CompanyResearchReport = await repResp.json();
      setReport(repData);
    } catch (err: any) {
      setError(err.message || 'Error occurred during company research.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (ticker: string) => {
    setQuery(ticker);
    executeSearch(ticker);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header & Search Console */}
      <div className="bg-surface border border-theme rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="w-6 h-6 text-primary" />
              <h2 className="text-xl font-bold text-primary">Company Research & Security Intelligence</h2>
            </div>
            <p className="text-xs text-secondary mt-1">
              Authoritative Indian equity analysis with entity resolution, multi-specialist evidence review, and paper-trading safety gates.
            </p>
          </div>

          {/* Search Bar */}
          <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="relative flex-1 md:w-80">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && executeSearch(query)}
                placeholder="Company, Ticker (e.g. TCS, RELIANCE) or ISIN..."
                className="w-full bg-main border border-theme rounded-lg px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:border-primary pl-9"
              />
              <Search className="w-4 h-4 text-secondary absolute left-3 top-2.5" />
            </div>
            <button
              onClick={() => executeSearch(query)}
              disabled={loading || !query.trim()}
              className="bg-primary text-primary-fg hover:opacity-90 px-4 py-2 rounded-lg text-sm font-semibold transition disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <Activity className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Research
            </button>
          </div>
        </div>

        {/* Quick Tickers */}
        <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-theme text-xs">
          <span className="text-secondary font-medium">Quick Benchmarks:</span>
          {['TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'TATAMOTORS', 'Tata (Test Ambiguity)'].map((sym) => (
            <button
              key={sym}
              onClick={() => handleQuickSelect(sym.replace(' (Test Ambiguity)', ''))}
              className="px-2.5 py-1 rounded bg-surface hover:bg-main border border-theme text-secondary hover:text-primary transition font-medium"
            >
              {sym}
            </button>
          ))}
        </div>
      </div>

      {/* Ambiguity Clarification Modal/Banner */}
      {ambiguity && ambiguity.is_ambiguous && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 text-amber-500">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="space-y-3">
              <div className="font-semibold text-sm">Corporate Ambiguity Detected</div>
              <p className="text-xs text-amber-500/90">{ambiguity.clarification_prompt}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
                {ambiguity.candidates.map((cand) => (
                  <button
                    key={cand.nse_symbol || cand.trade_name}
                    onClick={() => handleQuickSelect(cand.nse_symbol || cand.trade_name)}
                    className="p-3 rounded-lg bg-surface border border-amber-500/20 text-left hover:border-amber-500/50 transition"
                  >
                    <div className="font-bold text-sm text-primary">{cand.trade_name}</div>
                    <div className="text-xs text-secondary mt-1">{cand.legal_name}</div>
                    <div className="text-[11px] font-mono text-cyan-400 mt-2">
                      NSE: {cand.nse_symbol} | BSE: {cand.bse_code}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-500 flex items-center gap-3 text-xs">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Research Report Display */}
      {report && (
        <div className="space-y-6">
          {/* Identity & Price Summary Banner */}
          <div className="bg-surface border border-theme rounded-xl p-6 shadow-sm">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-2xl font-extrabold text-primary">{report.company.trade_name}</span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                    {report.company.primary_exchange}: {report.company.nse_symbol}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-medium">
                    {report.company.listing_status}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-main border border-theme text-secondary">
                    ISIN: {report.company.isin || 'N/A'}
                  </span>
                </div>
                <div className="text-xs text-secondary mt-1">
                  {report.company.legal_name} • {report.company.sector} ({report.company.industry})
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-3 text-[11px] text-muted">
                  {(() => {
                    const badge = getClassificationBadge(report.data_classification);
                    return (
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold ${badge.bg} ${badge.text} ${badge.border}`}>
                        {badge.label}
                      </span>
                    );
                  })()}
                  <span>•</span>
                  <span>Freshness: <strong className="text-emerald-500">{report.data_freshness}</strong></span>
                  <span>•</span>
                  <span>As of: {new Date(report.as_of_timestamp).toLocaleDateString()}</span>
                  <span>•</span>
                  <span>Retrieved: {new Date(report.retrieval_timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              {/* Price & Primary Return Cards */}
              <div className="flex flex-wrap items-center gap-4">
                <div className="p-3 bg-main border border-theme rounded-lg text-right min-w-[120px]">
                  <div className="text-[11px] text-muted uppercase">Last Price (INR)</div>
                  <div className="text-xl font-bold text-primary font-mono">
                    ₹{report.current_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>

                <div className="p-3 bg-main border border-theme rounded-lg text-right min-w-[110px]">
                  <div className="text-[11px] text-muted uppercase">1M Return</div>
                  <div className={`text-base font-bold font-mono flex items-center justify-end gap-0.5 ${
                    (report.returns_1m_pct || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'
                  }`}>
                    {(report.returns_1m_pct || 0) >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                    {report.returns_1m_pct !== undefined ? `${report.returns_1m_pct > 0 ? '+' : ''}${report.returns_1m_pct}%` : 'N/A'}
                  </div>
                </div>

                <div className="p-3 bg-main border border-theme rounded-lg text-right min-w-[110px]">
                  <div className="text-[11px] text-muted uppercase">Trend Regime</div>
                  <div className="text-sm font-bold text-cyan-400">
                    {report.trend_regime}
                  </div>
                </div>
              </div>
            </div>

            {/* Financial Multiples Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 mt-6 pt-6 border-t border-theme text-xs font-mono">
              <div className="p-2.5 bg-main/50 rounded-lg border border-theme/50">
                <div className="text-[10px] text-muted uppercase font-sans">Trailing P/E</div>
                <div className="text-sm font-bold text-primary mt-0.5">{report.pe_ratio ? `${report.pe_ratio}x` : 'N/A'}</div>
              </div>
              <div className="p-2.5 bg-main/50 rounded-lg border border-theme/50">
                <div className="text-[10px] text-muted uppercase font-sans">Price to Book</div>
                <div className="text-sm font-bold text-primary mt-0.5">{report.pb_ratio ? `${report.pb_ratio}x` : 'N/A'}</div>
              </div>
              <div className="p-2.5 bg-main/50 rounded-lg border border-theme/50">
                <div className="text-[10px] text-muted uppercase font-sans">Diluted EPS</div>
                <div className="text-sm font-bold text-primary mt-0.5">{report.eps_ttm ? `₹${report.eps_ttm}` : 'N/A'}</div>
              </div>
              <div className="p-2.5 bg-main/50 rounded-lg border border-theme/50">
                <div className="text-[10px] text-muted uppercase font-sans">Dividend Yield</div>
                <div className="text-sm font-bold text-primary mt-0.5">{report.dividend_yield_pct ? `${report.dividend_yield_pct}%` : '0.00%'}</div>
              </div>
              <div className="p-2.5 bg-main/50 rounded-lg border border-theme/50">
                <div className="text-[10px] text-muted uppercase font-sans">Debt / Equity</div>
                <div className="text-sm font-bold text-primary mt-0.5">{report.debt_to_equity !== undefined ? `${report.debt_to_equity}x` : '0.00x'}</div>
              </div>
              <div className="p-2.5 bg-main/50 rounded-lg border border-theme/50">
                <div className="text-[10px] text-muted uppercase font-sans">1Y Max Drawdown</div>
                <div className="text-sm font-bold text-red-400 mt-0.5">{report.max_drawdown_1y_pct ? `-${report.max_drawdown_1y_pct}%` : 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* Paper Trading Consideration Ticket Gate Banner */}
          <div className={`p-5 rounded-xl border ${
            report.paper_trading_ticket.is_eligible
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : 'bg-red-500/10 border-red-500/30'
          }`}>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                {report.paper_trading_ticket.is_eligible ? (
                  <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-primary">
                      Paper Trading Safety & Eligibility Gate
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                      report.paper_trading_ticket.is_eligible
                        ? 'bg-emerald-500 text-black'
                        : 'bg-red-500 text-white'
                    }`}>
                      {report.paper_trading_ticket.is_eligible ? 'ELIGIBLE FOR SIMULATION' : 'ORDER VETOED'}
                    </span>
                  </div>
                  <div className="text-xs text-secondary mt-1">
                    {report.paper_trading_ticket.is_eligible
                      ? `Passed all ${report.paper_trading_ticket.gate_checks_passed.length} automated risk criteria. Max recommended allocation: ${report.paper_trading_ticket.max_recommended_allocation_pct}%.`
                      : `Veto reasons: ${report.paper_trading_ticket.veto_reasons.join(', ')}`}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-[11px] text-muted text-right hidden sm:block">
                  <div>Simulated Paper Execution Only</div>
                  <div className="text-secondary font-mono">Real Money Disabled</div>
                </div>
              </div>
            </div>
          </div>

          {/* 6 Specialist Perspectives Grid */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Layers className="w-5 h-5 text-primary" />
              <h3 className="text-base font-bold text-primary">Specialist Independent Research Perspectives</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {report.specialist_perspectives.map((spec) => (
                <div
                  key={spec.role}
                  className="bg-surface border border-theme rounded-xl p-5 flex flex-col justify-between shadow-sm"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-xs font-semibold text-primary">{spec.role}</div>
                        <div className="text-[11px] text-muted">{spec.analyst_name}</div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                        spec.sentiment === 'BULLISH'
                          ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                          : spec.sentiment === 'BEARISH'
                          ? 'bg-red-500/10 text-red-500 border border-red-500/20'
                          : 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                      }`}>
                        {spec.sentiment}
                      </span>
                    </div>

                    <div className="space-y-2 mt-4 text-xs text-secondary">
                      {spec.key_findings.map((f, i) => (
                        <div key={i} className="flex items-start gap-1.5">
                          <span className="text-primary font-bold">•</span>
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-theme/60 text-[11px]">
                    <div className="text-muted font-semibold">Invalidation Condition:</div>
                    <div className="text-secondary mt-0.5 italic">{spec.invalidation_conditions[0] || 'N/A'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Scenario Analysis Matrix */}
          <div className="bg-surface border border-theme rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Scale className="w-5 h-5 text-primary" />
              <h3 className="text-base font-bold text-primary">Probabilistic Scenario Analysis (12-Month Outlook)</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Bull Case */}
              <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-500 uppercase tracking-wide">Bull Scenario</span>
                  <span className="text-sm font-mono font-bold text-emerald-500">
                    ₹{report.scenarios.bull_fair_value_est?.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-secondary">{report.scenarios.bull_case}</p>
                <div className="pt-2 text-[11px] text-secondary space-y-1">
                  <div className="font-semibold text-primary">Catalysts:</div>
                  {report.scenarios.bull_catalysts.map((c, i) => (
                    <div key={i}>• {c}</div>
                  ))}
                </div>
              </div>

              {/* Base Case */}
              <div className="p-4 rounded-lg bg-cyan-500/5 border border-cyan-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-cyan-400 uppercase tracking-wide">Base Scenario</span>
                  <span className="text-sm font-mono font-bold text-cyan-400">
                    ₹{report.scenarios.base_fair_value_est?.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-secondary">{report.scenarios.base_case}</p>
                <div className="pt-2 text-[11px] text-secondary space-y-1">
                  <div className="font-semibold text-primary">Core Assumptions:</div>
                  {report.scenarios.base_assumptions.map((a, i) => (
                    <div key={i}>• {a}</div>
                  ))}
                </div>
              </div>

              {/* Bear Case */}
              <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-red-500 uppercase tracking-wide">Bear Scenario</span>
                  <span className="text-sm font-mono font-bold text-red-500">
                    ₹{report.scenarios.bear_fair_value_est?.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-secondary">{report.scenarios.bear_case}</p>
                <div className="pt-2 text-[11px] text-secondary space-y-1">
                  <div className="font-semibold text-primary">Downside Risks:</div>
                  {report.scenarios.bear_risks.map((r, i) => (
                    <div key={i}>• {r}</div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Citations & Evidence Lineage */}
          <div className="bg-surface border border-theme rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-primary" />
              <h3 className="text-base font-bold text-primary">Corroborated Primary Evidence & Disclosures</h3>
            </div>

            <div className="space-y-3">
              {report.source_citations.map((cite, idx) => (
                <div key={idx} className="p-3 bg-main border border-theme rounded-lg text-xs space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-primary">{cite.title}</span>
                    <a
                      href={cite.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:underline flex items-center gap-1 text-[11px]"
                    >
                      {cite.source} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <p className="text-secondary text-[11px]">{cite.excerpt}</p>
                  <div className="text-[10px] text-muted">Filing Date: {cite.date}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
