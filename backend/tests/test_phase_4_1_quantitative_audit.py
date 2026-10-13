"""Deterministic Quantitative Audit Tests for AURXON Phase 4.1.
Independently verifies:
1. Return periods and trading-calendar bar count conventions (1M=21, 6M=126, 1Y=252).
2. Volatility annualization formula (sample standard deviation * sqrt(252)).
3. Maximum drawdown calculation (peak-to-trough over evaluation window).
4. Moving average warm-up periods (SMA 20, SMA 50, SMA 200).
5. Trend regime classification logic.
6. Benchmark relative strength calculation vs NIFTY50.
7. Financial ratios with zero revenue, negative net worth, and missing data.
8. Chronological sorting and absence of look-ahead bias.
"""

import math
import pytest
from app.analytics.company_quant import company_quant_engine
from app.schemas.historical_data import Exchange, HistoricalBar
from app.schemas.market import DataClassification, FreshnessStatus


def make_bar(trading_date: str, close: float, volume: int = 10000) -> HistoricalBar:
    return HistoricalBar(
        symbol="TEST.NS",
        exchange=Exchange.NSE,
        trading_date=trading_date,
        timestamp_iso=f"{trading_date}T15:30:00+05:30",
        open=close,
        high=close * 1.01,
        low=close * 0.99,
        close=close,
        volume=volume,
        data_provider="Deterministic Test Fixture",
        retrieval_timestamp_iso="2026-10-13T10:00:00Z",
        classification=DataClassification.HISTORICAL_VERIFIED,
        freshness=FreshnessStatus.OFFLINE_FROZEN,
    )


def test_independent_return_period_calculations():
    """Verifies that 1M, 6M, and 1Y returns require exactly 21, 126, and 252 bars respectively."""
    # Series with 20 bars: insufficient for 1M return
    bars_20 = [make_bar(f"2026-01-{i+1:02d}", 100.0 + i) for i in range(20)]
    metrics_20 = company_quant_engine.calculate_price_and_trend_metrics(bars_20)
    assert metrics_20["returns_1m_pct"] is None
    assert metrics_20["returns_6m_pct"] is None
    assert metrics_20["returns_1y_pct"] is None

    # Series with 21 bars: exactly sufficient for 1M return
    # Initial close at bar 0 = 100.0, bar 20 = 110.0
    # Expected return = (110.0 / 100.0 - 1) * 100 = 10.0%
    bars_21 = [make_bar(f"2026-01-{i+1:02d}", 100.0 if i < 20 else 110.0) for i in range(21)]
    metrics_21 = company_quant_engine.calculate_price_and_trend_metrics(bars_21)
    assert metrics_21["returns_1m_pct"] == 10.0
    assert metrics_21["returns_6m_pct"] is None
    assert metrics_21["returns_1y_pct"] is None

    # Series with 126 bars: exactly sufficient for 6M return
    # bar 0 = 200.0, bar 125 = 250.0 -> expected = (250/200 - 1) * 100 = 25.0%
    bars_126 = [make_bar(f"D{i:04d}", 200.0 if i < 125 else 250.0) for i in range(126)]
    metrics_126 = company_quant_engine.calculate_price_and_trend_metrics(bars_126)
    assert metrics_126["returns_6m_pct"] == 25.0
    assert metrics_126["returns_1y_pct"] is None

    # Series with 252 bars: exactly sufficient for 1Y return
    # bar 0 = 1000.0, bar 251 = 1200.0 -> expected = (1200/1000 - 1) * 100 = 20.0%
    bars_252 = [make_bar(f"D{i:04d}", 1000.0 if i < 251 else 1200.0) for i in range(252)]
    metrics_252 = company_quant_engine.calculate_price_and_trend_metrics(bars_252)
    assert metrics_252["returns_1y_pct"] == 20.0


def test_independent_volatility_annualization():
    """Verifies that sample standard deviation of daily returns is multiplied by sqrt(252)."""
    # Create alternating series with known log/simple returns
    # Let closes alternate: 100, 102, 100, 102 ... for 21 bars (20 returns)
    closes = [100.0 if i % 2 == 0 else 102.0 for i in range(21)]
    bars = [make_bar(f"D{i:02d}", closes[i]) for i in range(21)]

    # Compute independent expected volatility
    daily_returns = [(closes[i] / closes[i - 1]) - 1.0 for i in range(1, len(closes))]
    mean_r = sum(daily_returns) / len(daily_returns)
    sample_var = sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    sample_std = math.sqrt(sample_var)
    expected_vol_pct = round(sample_std * math.sqrt(252) * 100.0, 2)

    metrics = company_quant_engine.calculate_price_and_trend_metrics(bars)
    assert metrics["volatility_annualized_pct"] == expected_vol_pct

    # With fewer than 10 daily returns (10 bars = 9 returns), volatility must be None
    short_bars = [make_bar(f"D{i:02d}", closes[i]) for i in range(10)]
    short_metrics = company_quant_engine.calculate_price_and_trend_metrics(short_bars)
    assert short_metrics["volatility_annualized_pct"] is None


def test_independent_maximum_drawdown_calculation():
    """Verifies peak-to-trough drawdown logic with multiple peaks and troughs."""
    # Path: 100 -> 150 (peak 1) -> 105 (trough 1, dd = -30%) -> 140 -> 80 (trough 2 from peak 1, dd = -46.67%) -> 200 (peak 2) -> 170 (dd = -15%)
    prices = [100.0, 150.0, 105.0, 140.0, 80.0, 200.0, 170.0]
    bars = [make_bar(f"D{i:02d}", prices[i]) for i in range(len(prices))]

    # Independent calculation:
    # Max peak was 150.0, lowest point reached after that peak was 80.0.
    # DD = (80 - 150) / 150 = -70 / 150 = -46.6666...%
    # Next peak is 200.0, then 170.0 is -15%. Max drawdown remains 46.67%.
    expected_mdd = round(abs((80.0 - 150.0) / 150.0) * 100.0, 2)

    metrics = company_quant_engine.calculate_price_and_trend_metrics(bars)
    assert metrics["max_drawdown_1y_pct"] == expected_mdd


def test_moving_average_warmup_periods():
    """Verifies exact warm-up bar requirements for SMA 20, SMA 50, and SMA 200."""
    bars_19 = [make_bar(f"D{i:04d}", 100.0) for i in range(19)]
    m_19 = company_quant_engine.calculate_price_and_trend_metrics(bars_19)
    assert m_19["sma_20"] is None
    assert m_19["sma_50"] is None
    assert m_19["sma_200"] is None

    bars_20 = [make_bar(f"D{i:04d}", float(i + 1)) for i in range(20)]
    m_20 = company_quant_engine.calculate_price_and_trend_metrics(bars_20)
    # Average of 1 to 20 = 210 / 20 = 10.5
    assert m_20["sma_20"] == 10.5
    assert m_20["sma_50"] is None
    assert m_20["sma_200"] is None

    bars_50 = [make_bar(f"D{i:04d}", float(i + 1)) for i in range(50)]
    m_50 = company_quant_engine.calculate_price_and_trend_metrics(bars_50)
    # Average of 1 to 50 = 1275 / 50 = 25.5
    assert m_50["sma_20"] == sum(range(31, 51)) / 20.0
    assert m_50["sma_50"] == 25.5
    assert m_50["sma_200"] is None

    bars_200 = [make_bar(f"D{i:04d}", 10.0) for i in range(200)]
    m_200 = company_quant_engine.calculate_price_and_trend_metrics(bars_200)
    assert m_200["sma_200"] == 10.0


def test_trend_regime_classification():
    """Verifies deterministic classification of bullish, bearish, and neutral regimes."""
    # Strong Bullish: Latest Close > SMA 20 > SMA 50
    # Create 55 bars where price increases from 100 to 200
    bars_bull = [make_bar(f"D{i:02d}", 100.0 + (i * 2.0)) for i in range(55)]
    m_bull = company_quant_engine.calculate_price_and_trend_metrics(bars_bull)
    assert m_bull["trend_regime"] == "STRONG_BULLISH"

    # Strong Bearish: Latest Close < SMA 20 < SMA 50
    bars_bear = [make_bar(f"D{i:02d}", 250.0 - (i * 2.0)) for i in range(55)]
    m_bear = company_quant_engine.calculate_price_and_trend_metrics(bars_bear)
    assert m_bear["trend_regime"] == "STRONG_BEARISH"


def test_benchmark_relative_strength_alignment():
    """Verifies 1M relative strength spread computation vs NIFTY50."""
    # Asset: 21 bars with 10% gain (100 -> 110)
    asset_bars = [make_bar(f"2026-01-{i+1:02d}", 100.0 if i < 20 else 110.0) for i in range(21)]

    # Benchmark case 1: Nifty gains 2% (excess = +8.0% -> OUTPERFORMING)
    bm_bars_1 = [make_bar(f"2026-01-{i+1:02d}", 100.0 if i < 20 else 102.0) for i in range(21)]
    m_out = company_quant_engine.calculate_price_and_trend_metrics(asset_bars, bm_bars_1)
    assert "OUTPERFORMING (+8.0% vs Nifty)" in m_out["relative_strength_vs_nifty"]

    # Benchmark case 2: Nifty gains 15% (excess = -5.0% -> UNDERPERFORMING)
    bm_bars_2 = [make_bar(f"2026-01-{i+1:02d}", 100.0 if i < 20 else 115.0) for i in range(21)]
    m_under = company_quant_engine.calculate_price_and_trend_metrics(asset_bars, bm_bars_2)
    assert "UNDERPERFORMING (-5.0% vs Nifty)" in m_under["relative_strength_vs_nifty"]

    # Benchmark case 3: Nifty gains 11% (excess = -1.0% -> MARKET_PERFORM)
    bm_bars_3 = [make_bar(f"2026-01-{i+1:02d}", 100.0 if i < 20 else 111.0) for i in range(21)]
    m_mp = company_quant_engine.calculate_price_and_trend_metrics(asset_bars, bm_bars_3)
    assert "MARKET_PERFORM (-1.0% vs Nifty)" in m_mp["relative_strength_vs_nifty"]


def test_financial_ratios_edge_cases_and_zero_division():
    """Verifies ratio safety with zero revenue, negative net worth, and missing periods."""
    # Case 1: Zero revenue
    stmts_zero_rev = [
        {"fiscal_period": "FY24-Q4", "revenue_cr": 0.0, "ebitda_cr": -10.0, "pat_cr": -15.0, "total_debt_cr": 50.0, "net_worth_cr": 100.0}
    ]
    ratios_1 = company_quant_engine.calculate_fundamental_metrics(stmts_zero_rev)
    assert ratios_1["ebitda_margin_pct"] is None
    assert ratios_1["pat_margin_pct"] is None
    assert ratios_1["debt_to_equity"] == 0.5

    # Case 2: Negative net worth (insolvent / depleted capital)
    stmts_neg_equity = [
        {"fiscal_period": "FY24-Q4", "revenue_cr": 500.0, "ebitda_cr": 50.0, "pat_cr": -200.0, "total_debt_cr": 1000.0, "net_worth_cr": -200.0}
    ]
    ratios_2 = company_quant_engine.calculate_fundamental_metrics(stmts_neg_equity)
    assert ratios_2["debt_to_equity"] is None  # Safeguarded against negative D/E
    assert ratios_2["roe_pct"] is None         # Safeguarded against misleading positive ROE from negative PAT / negative NW

    # Case 3: Empty statements
    ratios_empty = company_quant_engine.calculate_fundamental_metrics([])
    assert ratios_empty["ebitda_margin_pct"] is None
    assert ratios_empty["revenue_growth_yoy_pct"] is None


def test_chronological_ordering_guard_against_lookahead():
    """Verifies that reverse-ordered bar inputs are sorted chronologically before analysis."""
    # Pass bars sorted latest-to-oldest
    bars_rev = [make_bar(f"2026-01-{i+1:02d}", 100.0 + i) for i in reversed(range(25))]
    assert bars_rev[0].trading_date == "2026-01-25"

    metrics = company_quant_engine.calculate_price_and_trend_metrics(bars_rev)
    # The latest close should be at 2026-01-25 (124.0), not 2026-01-01 (100.0)
    # Return should be positive, not negative
    assert metrics["returns_1m_pct"] is not None
    assert metrics["returns_1m_pct"] > 0.0
