"""AURXON Portfolio Analytics & Performance Engine.
Workstream B: Deterministic returns, Time-Weighted Return (TWR), Money-Weighted Return (MWR / IRR),
tracking error, benchmark-relative analytics, and concentration audits.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.portfolio_intelligence import (
    ConcentrationAnalysis,
    PerformanceMetrics,
    PortfolioHolding,
    PricingStatus,
)
from app.schemas.paper_trading import PaperPortfolioState, PaperPositionRecord
from app.market_data.nse_connector import NSEDataConnector


# Standard sector classifications for Indian large-cap equities
INDIAN_SECTOR_MAP: Dict[str, str] = {
    "RELIANCE": "Energy & Conglomerate",
    "TCS": "IT Services",
    "INFY": "IT Services",
    "WIPRO": "IT Services",
    "HCLTECH": "IT Services",
    "HDFCBANK": "Financial Services (Banking)",
    "ICICIBANK": "Financial Services (Banking)",
    "SBIN": "Financial Services (Banking)",
    "KOTAKBANK": "Financial Services (Banking)",
    "AXISBANK": "Financial Services (Banking)",
    "BAJFINANCE": "Financial Services (NBFC)",
    "LT": "Infrastructure & Capital Goods",
    "ITC": "Fast Moving Consumer Goods (FMCG)",
    "HINDUNILVR": "Fast Moving Consumer Goods (FMCG)",
    "TATAMOTORS": "Automobile",
    "MARUTI": "Automobile",
    "M&M": "Automobile",
    "SUNPHARMA": "Pharmaceuticals",
    "CIPLA": "Pharmaceuticals",
    "BHARTIARTL": "Telecommunications",
    "TATASTEEL": "Metals & Mining",
    "NTPC": "Power & Utilities",
    "POWERGRID": "Power & Utilities",
}


class PortfolioAnalyticsEngine:
    """Calculates verifiable portfolio metrics, concentration analysis, and benchmark tracking."""

    def __init__(self, connector: Optional[NSEDataConnector] = None):
        self.connector = connector or NSEDataConnector()

    def build_holdings_inventory(
        self, state: PaperPortfolioState
    ) -> Tuple[List[PortfolioHolding], ConcentrationAnalysis]:
        """Converts raw paper positions into enriched holdings with verified sector and pricing status."""
        total_equity = state.total_equity
        holdings: List[PortfolioHolding] = []
        sector_totals: Dict[str, float] = {}
        top_weight = 0.0
        top_symbol = None
        weights: List[float] = []

        for sym, pos in state.positions.items():
            clean = sym.strip().upper().replace(".NS", "").replace(".BO", "")
            sector = INDIAN_SECTOR_MAP.get(clean, "Diversified Indian Equities")
            
            # Resolve live or fixture quote
            quote = self.connector.get_market_quote(clean)
            
            # Determine pricing status
            if quote.current_price is not None and quote.current_price > 0:
                price = quote.current_price
                price_ts = quote.market_timestamp or quote.retrieval_timestamp
                provider = quote.data_provider
                if "Benchmark" in quote.data_provider:
                    pricing_status = PricingStatus.BENCHMARK_FIXTURE
                elif "Cached" in quote.data_provider or quote.classification.value == "CACHED_LOCAL":
                    pricing_status = PricingStatus.CACHED
                else:
                    pricing_status = PricingStatus.DELAYED_VERIFIED
            elif pos.current_price > 0:
                price = pos.current_price
                price_ts = pos.last_updated_at
                provider = "Local Paper Ledger Cache"
                pricing_status = PricingStatus.CACHED
            else:
                price = None
                price_ts = None
                provider = "Unavailable"
                pricing_status = PricingStatus.UNPRICED

            # Market value and P&L
            if price is not None:
                market_val = round(pos.quantity * price, 2)
                cost_basis = round(pos.quantity * pos.average_cost, 2)
                unrealized = round(market_val - cost_basis, 2)
                unrealized_pct = (
                    round(((price - pos.average_cost) / pos.average_cost) * 100.0, 2)
                    if pos.average_cost > 0
                    else 0.0
                )
            else:
                market_val = None
                cost_basis = round(pos.quantity * pos.average_cost, 2)
                unrealized = None
                unrealized_pct = None

            weight_pct = (
                round((market_val / total_equity) * 100.0, 2)
                if total_equity > 0 and market_val is not None
                else 0.0
            )

            weights.append(weight_pct)
            if weight_pct > top_weight:
                top_weight = weight_pct
                top_symbol = clean

            if market_val is not None:
                sector_totals[sector] = sector_totals.get(sector, 0.0) + market_val

            holding = PortfolioHolding(
                symbol=clean,
                instrument_name=quote.instrument_name if quote else f"{clean} Ltd",
                sector=sector,
                asset_class="EQUITY",
                quantity=pos.quantity,
                average_cost=pos.average_cost,
                current_price=price,
                market_value=market_val,
                cost_basis_total=cost_basis,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized_pct,
                realized_pnl=pos.realized_pnl,
                portfolio_weight_pct=weight_pct,
                pricing_status=pricing_status,
                data_provider=provider,
                price_timestamp=price_ts,
            )
            holdings.append(holding)

        # Asset class weights
        cash_weight_pct = round((state.current_cash / total_equity) * 100.0, 2) if total_equity > 0 else 100.0
        equity_weight_pct = round(100.0 - cash_weight_pct, 2)
        asset_class_weights = {"CASH": cash_weight_pct, "EQUITY": equity_weight_pct}

        # Sector weights
        sector_weights = {
            sec: round((val / total_equity) * 100.0, 2)
            for sec, val in sector_totals.items()
        } if total_equity > 0 else {}

        # Herfindahl-Hirschman Index (HHI): sum of squared percentage weights (0 to 10,000)
        hhi = round(sum((w ** 2) for w in weights) + (cash_weight_pct ** 2), 2)
        sorted_weights = sorted(weights, reverse=True)
        top_3_pct = round(sum(sorted_weights[:3]), 2)

        # Concentration breaches
        breaches = []
        max_pos_limit = state.risk_limits.max_position_weight_pct
        if top_weight > max_pos_limit:
            breaches.append(f"Position '{top_symbol}' weight ({top_weight}%) exceeds limit of {max_pos_limit}%.")
        
        for sec, sw in sector_weights.items():
            if sw > 50.0:
                breaches.append(f"Sector '{sec}' weight ({sw}%) exceeds sector ceiling of 50.0%.")

        concentration = ConcentrationAnalysis(
            top_position_symbol=top_symbol,
            top_position_weight_pct=top_weight,
            top_3_positions_weight_pct=top_3_pct,
            herfindahl_index=hhi,
            sector_weights=sector_weights,
            asset_class_weights=asset_class_weights,
            max_position_weight_limit_pct=max_pos_limit,
            max_sector_weight_limit_pct=50.0,
            has_concentration_breach=len(breaches) > 0,
            breach_details=breaches,
        )

        return holdings, concentration

    def calculate_time_weighted_return(
        self, subperiod_returns: List[float]
    ) -> Optional[float]:
        """Calculates Time-Weighted Return (TWR) by linking subperiod returns:
        TWR = Product(1 + r_t) - 1.
        Insulates performance against the timing and magnitude of external deposits/withdrawals.
        """
        if not subperiod_returns:
            return None
        twr_factor = 1.0
        for r in subperiod_returns:
            twr_factor *= (1.0 + r)
        return round((twr_factor - 1.0) * 100.0, 2)

    def calculate_money_weighted_return(
        self,
        initial_cash: float,
        final_equity: float,
        cash_flows: List[Tuple[int, float]],  # (days_from_start, cash_flow_amount)
        total_days: int = 365,
    ) -> Optional[float]:
        """Calculates Money-Weighted Return (MWR / Internal Rate of Return) via numerical bisection.
        Solves: initial_cash + sum(CF_t / (1 + r)^(t / 365)) = final_equity / (1 + r)^(T / 365).
        """
        if initial_cash <= 0 or final_equity <= 0 or total_days <= 0:
            return None

        if not cash_flows:
            # When no intermediate cash flows occur, MWR equals simple annualized return
            years = max(total_days / 365.0, 1.0 / 365.0)
            return round(((final_equity / initial_cash) ** (1.0 / years) - 1.0) * 100.0, 2)

        def npv(r: float) -> float:
            base = 1.0 + r
            if base <= 1e-6:
                return -1e12
            val = initial_cash
            for t_days, cf in cash_flows:
                val += cf / (base ** (t_days / 365.0))
            val -= final_equity / (base ** (total_days / 365.0))
            return val

        # Bisection solver in range [-0.90, +5.00] (-90% to +500% IRR)
        low, high = -0.90, 5.00
        f_low = npv(low)
        f_high = npv(high)

        if f_low * f_high > 0:
            # Bracket failure: no single root exists in the realistic [-90%, +500%] search interval.
            # Return None to transparently indicate that IRR is undefined or out-of-bounds for these cash flows.
            return None

        for _ in range(60):
            mid = (low + high) / 2.0
            f_mid = npv(mid)
            if abs(f_mid) < 1e-4:
                return round(mid * 100.0, 2)
            if f_low * f_mid < 0:
                high = mid
                f_high = f_mid
            else:
                low = mid
                f_low = f_mid

        return round(mid * 100.0, 2)

    def calculate_tracking_error_and_benchmark_metrics(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float],
    ) -> Dict[str, Optional[float]]:
        """Computes tracking error, beta, and information ratio vs benchmark."""
        if not portfolio_returns or not benchmark_returns or len(portfolio_returns) != len(benchmark_returns):
            return {
                "active_return_pct": None,
                "tracking_error_pct": None,
                "information_ratio": None,
                "portfolio_beta": None,
                "portfolio_alpha_pct": None,
            }

        n = len(portfolio_returns)
        if n < 5:
            return {
                "active_return_pct": None,
                "tracking_error_pct": None,
                "information_ratio": None,
                "portfolio_beta": None,
                "portfolio_alpha_pct": None,
            }

        diffs = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        mean_diff = sum(diffs) / n
        active_ret_pct = round(mean_diff * 252.0 * 100.0, 2)

        # Tracking error: annualized std dev of return differences
        te_var = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
        te_daily = math.sqrt(te_var)
        tracking_error_pct = round(te_daily * math.sqrt(252) * 100.0, 2)

        # Information Ratio: Active Return / Tracking Error
        info_ratio = (
            round(active_ret_pct / tracking_error_pct, 2)
            if tracking_error_pct > 1e-4
            else None
        )

        # Portfolio Beta: Cov(Rp, Rb) / Var(Rb)
        bm_mean = sum(benchmark_returns) / n
        p_mean = sum(portfolio_returns) / n
        bm_var = sum((b - bm_mean) ** 2 for b in benchmark_returns) / (n - 1)
        cov_pb = sum((p - p_mean) * (b - bm_mean) for p, b in zip(portfolio_returns, benchmark_returns)) / (n - 1)

        beta = round(cov_pb / bm_var, 2) if bm_var > 1e-8 else None

        # Alpha: Rp - Beta * Rb (annualized)
        alpha_pct = (
            round((p_mean * 252.0 - (beta * bm_mean * 252.0)) * 100.0, 2)
            if beta is not None
            else None
        )

        return {
            "active_return_pct": active_ret_pct,
            "tracking_error_pct": tracking_error_pct,
            "information_ratio": info_ratio,
            "portfolio_beta": beta,
            "portfolio_alpha_pct": alpha_pct,
        }

    def compute_performance_dossier(
        self,
        state: PaperPortfolioState,
        historical_snapshots: Optional[List[Dict[str, Any]]] = None,
        benchmark_returns: Optional[List[float]] = None,
    ) -> PerformanceMetrics:
        """Assembles a comprehensive, auditable performance metrics package."""
        init_cash = state.initial_cash
        curr_equity = state.total_equity
        abs_return = round(curr_equity - init_cash, 2)
        tot_return_pct = round((abs_return / init_cash) * 100.0, 2) if init_cash > 0 else 0.0
        cash_res_pct = round((state.current_cash / curr_equity) * 100.0, 2) if curr_equity > 0 else 100.0

        methodology_notes = [
            "Returns computed net of statutory STT, GST, brokerage, and slippage fees.",
            "Benchmark comparison aligned against NIFTY 50 (^NSEI) daily settlement closes.",
            "Indian Risk-Free Rate benchmarked at 6.50% (91-day Government T-bill yield).",
        ]
        limitations = [
            "Simulated paper portfolio ledger; does not account for real liquidity queue priority.",
            "Missing intraday price fluctuations; valuation relies on verified end-of-day quotes or benchmark fixtures.",
        ]

        # Use snapshot history if available for multi-period TWR and Volatility
        daily_rets: List[float] = []
        if historical_snapshots and len(historical_snapshots) >= 2:
            equities = [s["total_equity"] for s in historical_snapshots]
            daily_rets = [
                (equities[i] / equities[i - 1]) - 1.0
                for i in range(1, len(equities))
                if equities[i - 1] > 0
            ]
        else:
            # Baseline single-period daily approximation
            daily_rets = [tot_return_pct / 100.0]

        # Time-Weighted Return
        twr = self.calculate_time_weighted_return(daily_rets) or tot_return_pct
        # Money-Weighted Return (no intermediate external cash flows in baseline)
        mwr = self.calculate_money_weighted_return(init_cash, curr_equity, [])

        # Volatility
        if len(daily_rets) >= 2:
            m = sum(daily_rets) / len(daily_rets)
            v = sum((r - m) ** 2 for r in daily_rets) / (len(daily_rets) - 1)
            ann_vol = round(math.sqrt(v) * math.sqrt(252) * 100.0, 2)
        else:
            ann_vol = 0.0

        # Sharpe and Sortino
        rf_daily = (6.5 / 100.0) / 252.0
        daily_mean = sum(daily_rets) / len(daily_rets) if daily_rets else 0.0
        vol_daily = ann_vol / (math.sqrt(252) * 100.0) if ann_vol > 0 else 0.0
        
        sharpe = round(((daily_mean - rf_daily) / vol_daily) * math.sqrt(252), 2) if vol_daily > 1e-4 else None
        
        downside_sq = [min(0.0, r - rf_daily) ** 2 for r in daily_rets]
        downside_dev = math.sqrt(sum(downside_sq) / max(1, len(daily_rets)))
        sortino = round(((daily_mean - rf_daily) / downside_dev) * math.sqrt(252), 2) if downside_dev > 1e-4 else None

        # Benchmark Tracking (resolved from market data store if not explicitly passed)
        resolved_bm_returns = benchmark_returns
        if not resolved_bm_returns and len(daily_rets) >= 5:
            resolved_bm_returns = self.get_benchmark_returns(len(daily_rets))

        if resolved_bm_returns and len(resolved_bm_returns) == len(daily_rets) and len(daily_rets) >= 5:
            bm_stats = self.calculate_tracking_error_and_benchmark_metrics(
                portfolio_returns=daily_rets,
                benchmark_returns=resolved_bm_returns,
            )
            bm_total_ret = round(sum(resolved_bm_returns) * 100.0, 2)
            p_beta = bm_stats.get("portfolio_beta")
            p_alpha = bm_stats.get("portfolio_alpha_pct")
            active_ret = bm_stats.get("active_return_pct")
            te_pct = bm_stats.get("tracking_error_pct")
            ir_val = bm_stats.get("information_ratio")
        else:
            bm_total_ret = None
            p_beta = None
            p_alpha = None
            active_ret = None
            te_pct = None
            ir_val = None
            limitations.append(
                "Benchmark tracking metrics (Beta, Alpha, Tracking Error) unavailable: requires at least 5 synchronized daily settlement bars with NIFTY 50."
            )

        return PerformanceMetrics(
            initial_capital=init_cash,
            current_equity=curr_equity,
            total_cash=state.current_cash,
            cash_reserve_pct=cash_res_pct,
            absolute_return_inr=abs_return,
            total_return_pct=tot_return_pct,
            time_weighted_return_pct=twr,
            money_weighted_return_pct=mwr,
            annualized_volatility_pct=ann_vol,
            max_drawdown_pct=state.current_drawdown_pct,
            current_drawdown_pct=state.current_drawdown_pct,
            peak_equity=state.peak_equity,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            risk_free_rate_pct=6.5,
            benchmark_symbol="^NSEI",
            benchmark_total_return_pct=bm_total_ret,
            active_return_pct=active_ret,
            tracking_error_pct=te_pct,
            information_ratio=ir_val,
            portfolio_beta=p_beta,
            portfolio_alpha_pct=p_alpha,
            observation_window_bars=len(daily_rets),
            start_date=state.created_at[:10],
            end_date=state.updated_at[:10],
            methodology_notes=methodology_notes,
            limitations=limitations,
        )

    def get_benchmark_returns(self, n_bars: int = 252) -> Optional[List[float]]:
        """Fetches daily settlement returns for NIFTY 50 benchmark from local market data store."""
        try:
            from app.market_data.store import market_data_store
            bars = market_data_store.get_historical_bars("NIFTY50.NSE") or market_data_store.get_historical_bars("^NSEI")
            if not bars or len(bars) < 5:
                return None
            closes = [b.close for b in sorted(bars, key=lambda x: x.trading_date)]
            all_rets = [(closes[i] / closes[i - 1]) - 1.0 for i in range(1, len(closes)) if closes[i - 1] > 0]
            if len(all_rets) < n_bars:
                return all_rets
            return all_rets[-n_bars:]
        except Exception:
            return None


portfolio_analytics_engine = PortfolioAnalyticsEngine()
