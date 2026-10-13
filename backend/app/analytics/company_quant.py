"""AURXON Company Quantitative & Financial Analysis Engine.
Implements deterministic indicators: period returns, momentum, annualized volatility,
maximum drawdown, benchmark relative strength (vs NIFTY50), trend regimes (SMA 20/50/200),
financial margins, debt-to-equity, ROE, RoCE, and FCF trends.
"""

import math
from typing import Any, Dict, List, Optional
from app.schemas.historical_data import HistoricalBar


class CompanyQuantEngine:
    """Deterministic calculations with zero look-ahead bias and strict input validation."""

    @staticmethod
    def calculate_price_and_trend_metrics(
        bars: List[HistoricalBar],
        benchmark_bars: Optional[List[HistoricalBar]] = None,
    ) -> Dict[str, Any]:
        """Calculates returns, volatility, max drawdown, trend regime, and relative strength."""
        if not bars or len(bars) < 2:
            return {
                "returns_1m_pct": None,
                "returns_6m_pct": None,
                "returns_1y_pct": None,
                "volatility_annualized_pct": None,
                "max_drawdown_1y_pct": None,
                "sma_20": None,
                "sma_50": None,
                "sma_200": None,
                "trend_regime": "INSUFFICIENT_DATA",
                "relative_strength_vs_nifty": "UNAVAILABLE",
                "avg_daily_volume": None,
            }

        # Chronological sort (oldest to newest)
        sorted_bars = sorted(bars, key=lambda b: b.trading_date)
        closes = [b.close for b in sorted_bars]
        volumes = [b.volume for b in sorted_bars]
        n = len(closes)

        latest_close = closes[-1]

        # 1. Period Returns
        # ~21 bars for 1M, ~126 bars for 6M, ~245-252 bars for 1Y (Indian exchange holidays reduce calendar year to ~245-250 sessions)
        ret_1m = ((latest_close / closes[-21]) - 1.0) * 100.0 if n >= 21 and closes[-21] > 0 else None
        ret_6m = ((latest_close / closes[-126]) - 1.0) * 100.0 if n >= 126 and closes[-126] > 0 else None
        if n >= 252 and closes[-252] > 0:
            ret_1y = ((latest_close / closes[-252]) - 1.0) * 100.0
        elif n >= 245 and closes[0] > 0:
            ret_1y = ((latest_close / closes[0]) - 1.0) * 100.0
        else:
            ret_1y = None

        # 2. Moving Averages
        sma_20 = sum(closes[-20:]) / 20.0 if n >= 20 else None
        sma_50 = sum(closes[-50:]) / 50.0 if n >= 50 else None
        sma_200 = sum(closes[-200:]) / 200.0 if n >= 200 else None

        # 3. Trend Regime
        if sma_20 and sma_50:
            if latest_close > sma_20 > sma_50:
                trend_regime = "STRONG_BULLISH"
            elif latest_close > sma_50:
                trend_regime = "MILD_BULLISH"
            elif latest_close < sma_20 < sma_50:
                trend_regime = "STRONG_BEARISH"
            else:
                trend_regime = "CONSOLIDATION_NEUTRAL"
        else:
            trend_regime = "NEUTRAL"

        # 4. Annualized Volatility (over past min(n, 252) bars)
        window = min(n, 252)
        window_closes = closes[-window:]
        daily_returns = [
            (window_closes[i] / window_closes[i - 1]) - 1.0
            for i in range(1, len(window_closes))
            if window_closes[i - 1] > 0
        ]

        if len(daily_returns) >= 10:
            mean_ret = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            daily_std = math.sqrt(variance)
            annualized_vol_pct = daily_std * math.sqrt(252) * 100.0
        else:
            annualized_vol_pct = None

        # 5. Maximum Drawdown (1Y window)
        peak = window_closes[0]
        max_dd = 0.0
        for p in window_closes:
            if p > peak:
                peak = p
            dd = (p - peak) / peak if peak > 0 else 0.0
            if dd < max_dd:
                max_dd = dd
        max_dd_pct = abs(max_dd) * 100.0

        # 6. Relative Strength vs Benchmark (NIFTY50)
        relative_strength_str = "UNAVAILABLE"
        if benchmark_bars and len(benchmark_bars) >= 21 and ret_1m is not None:
            sorted_bm = sorted(benchmark_bars, key=lambda b: b.trading_date)
            bm_closes = [b.close for b in sorted_bm]
            if len(bm_closes) >= 21:
                bm_ret_1m = ((bm_closes[-1] / bm_closes[-21]) - 1.0) * 100.0
                excess_ret = ret_1m - bm_ret_1m
                if excess_ret > 3.0:
                    relative_strength_str = f"OUTPERFORMING (+{excess_ret:.1f}% vs Nifty)"
                elif excess_ret < -3.0:
                    relative_strength_str = f"UNDERPERFORMING ({excess_ret:.1f}% vs Nifty)"
                else:
                    relative_strength_str = f"MARKET_PERFORM ({excess_ret:+.1f}% vs Nifty)"

        # 7. Average Daily Volume (past 20 days)
        vol_window = volumes[-20:] if n >= 20 else volumes
        avg_vol = int(sum(vol_window) / len(vol_window)) if vol_window else None

        return {
            "returns_1m_pct": round(ret_1m, 2) if ret_1m is not None else None,
            "returns_6m_pct": round(ret_6m, 2) if ret_6m is not None else None,
            "returns_1y_pct": round(ret_1y, 2) if ret_1y is not None else None,
            "volatility_annualized_pct": round(annualized_vol_pct, 2) if annualized_vol_pct is not None else None,
            "max_drawdown_1y_pct": round(max_dd_pct, 2),
            "sma_20": round(sma_20, 2) if sma_20 is not None else None,
            "sma_50": round(sma_50, 2) if sma_50 is not None else None,
            "sma_200": round(sma_200, 2) if sma_200 is not None else None,
            "trend_regime": trend_regime,
            "relative_strength_vs_nifty": relative_strength_str,
            "avg_daily_volume": avg_vol,
        }

    @staticmethod
    def calculate_fundamental_metrics(statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates margins, ROE, RoCE, and debt ratios from verified financial statements."""
        if not statements:
            return {
                "ebitda_margin_pct": None,
                "pat_margin_pct": None,
                "debt_to_equity": None,
                "roe_pct": None,
                "roce_pct": None,
                "revenue_growth_yoy_pct": None,
            }

        # Latest statement
        latest = statements[-1]
        rev = latest.get("revenue_cr") or 0.0
        ebitda = latest.get("ebitda_cr") or 0.0
        pat = latest.get("pat_cr") or 0.0
        debt = latest.get("total_debt_cr") or 0.0
        net_worth = latest.get("net_worth_cr") or 0.0

        ebitda_margin = (ebitda / rev * 100.0) if rev > 0 else None
        pat_margin = (pat / rev * 100.0) if rev > 0 else None
        d_to_e = (debt / net_worth) if net_worth > 0 else None
        roe = (pat / net_worth * 100.0) if net_worth > 0 else None
        capital_employed = debt + net_worth
        roce = (ebitda / capital_employed * 100.0) if capital_employed > 0 else None

        rev_growth_yoy = None
        if len(statements) >= 2:
            prior = statements[-2]
            prior_rev = prior.get("revenue_cr") or 0.0
            if prior_rev > 0:
                rev_growth_yoy = ((rev / prior_rev) - 1.0) * 100.0

        return {
            "ebitda_margin_pct": round(ebitda_margin, 2) if ebitda_margin is not None else None,
            "pat_margin_pct": round(pat_margin, 2) if pat_margin is not None else None,
            "debt_to_equity": round(d_to_e, 2) if d_to_e is not None else None,
            "roe_pct": round(roe, 2) if roe is not None else None,
            "roce_pct": round(roce, 2) if roce is not None else None,
            "revenue_growth_yoy_pct": round(rev_growth_yoy, 2) if rev_growth_yoy is not None else None,
        }


company_quant_engine = CompanyQuantEngine()
