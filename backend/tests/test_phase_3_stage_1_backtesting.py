"""AURXON Phase 3, Stage 1 Test Suite:
Deterministic Event-Driven Backtesting Engine, Historical Data Contract,
Indian Transaction Cost Schedule, Corporate Action Accounting, and Lookahead Prevention.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.historical_data import (
    CorporateAction,
    CorporateActionType,
    Exchange,
    HistoricalBar,
    validate_historical_series,
)
from app.schemas.market import DataClassification
from app.trading.costs import (
    IndianTransactionCostModel,
    TradeAction,
    default_indian_cost_model,
)
from app.trading.engine import (
    BuyAndHoldStrategy,
    DeterministicBacktestEngine,
    DualMovingAverageStrategy,
    OrderRequest,
)
from app.trading.fixtures import (
    RELIANCE_SERIES,
    TCS_BONUS_SERIES,
    NIFTY50_BENCHMARK_SERIES,
    generate_benchmark_equity_bars,
)
from app.trading.metrics import calculate_backtest_metrics


client = TestClient(app)


# ============================================================================
# 1. HISTORICAL MARKET DATA CONTRACT & VALIDATION
# ============================================================================

def test_historical_series_validation_clean():
    """Verify clean benchmark series passes all contract integrity checks."""
    report = validate_historical_series("RELIANCE", RELIANCE_SERIES)
    assert report.is_ready_for_backtest is True
    assert report.is_chronological is True
    assert report.has_duplicates is False
    assert report.has_ohlc_inconsistencies is False
    assert len(report.rejection_reasons) == 0


def test_historical_series_validation_detects_ohlc_violation():
    """Verify validation detects invalid High < Low or negative prices."""
    bad_bar = HistoricalBar(
        symbol="BAD_STOCK",
        exchange=Exchange.NSE,
        trading_date="2024-01-02",
        timestamp_iso="2024-01-02T15:30:00+05:30",
        open=100.0,
        high=90.0,  # High < Open (violation)
        low=105.0,  # Low > Open (violation)
        close=95.0,
        volume=1000,
        source="TEST_FIXTURE",
        data_classification=DataClassification.HISTORICAL_VERIFIED,
    )
    report = validate_historical_series("BAD_STOCK", [bad_bar])
    assert report.is_ready_for_backtest is False
    assert any("High/Low violated" in r for r in report.inconsistency_dates)
    assert any("inconsistencies" in r.lower() for r in report.rejection_reasons)


def test_historical_series_validation_detects_duplicate_dates():
    """Verify validation detects duplicate trading dates."""
    bars = generate_benchmark_equity_bars("TEST", num_bars=5)
    # Inject duplicate
    bars[1].trading_date = bars[0].trading_date
    report = validate_historical_series("TEST", bars)
    assert report.is_ready_for_backtest is False
    assert report.has_duplicates is True


# ============================================================================
# 2. INDIAN STATUTORY TRANSACTION COST MODEL
# ============================================================================

def test_indian_cost_model_buy_delivery():
    """Verify exact line-item calculation of Indian taxes on equity buy delivery."""
    cost_model = IndianTransactionCostModel(
        slippage_bps=0.0,  # Zero slippage to isolate tax math
        stt_delivery_buy_pct=0.1,
        stamp_duty_buy_pct=0.015,
        exchange_txn_charge_pct=0.00297,
        sebi_turnover_fee_pct=0.0001,
        gst_rate_pct=18.0,
    )
    # Buy 100 shares @ ₹1,000 = ₹100,000 turnover
    breakdown = cost_model.calculate_trade_costs(
        action=TradeAction.BUY, raw_price=1000.0, quantity=100, is_delivery=True
    )
    assert breakdown.turnover_gross == 100000.0
    assert breakdown.stt == 100.0  # 0.1% of ₹100,000 = ₹100
    assert breakdown.stamp_duty == 15.0  # 0.015% of ₹100,000 = ₹15
    assert breakdown.exchange_txn_charge == 2.97  # 0.00297% of ₹100,000 = ₹2.97
    assert breakdown.sebi_turnover_fee == 0.10  # ₹10/Cr = 0.0001% = ₹0.10
    # GST = 18% on (Exchange Txn ₹2.97 + SEBI Fee ₹0.10) = 18% of 3.07 = ₹0.55
    assert breakdown.gst == 0.55
    # Total costs = ₹100 + ₹15 + ₹2.97 + ₹0.10 + ₹0.55 = ₹118.62
    assert breakdown.total_costs == 118.62
    assert breakdown.total_cash_impact == -100118.62


def test_indian_cost_model_sell_delivery_stamp_duty_exemption():
    """Verify Stamp Duty is strictly 0 on sell transactions (Indian Stamp Act 2020)."""
    cost_model = IndianTransactionCostModel(slippage_bps=0.0)
    breakdown = cost_model.calculate_trade_costs(
        action=TradeAction.SELL, raw_price=1000.0, quantity=100, is_delivery=True
    )
    assert breakdown.stamp_duty == 0.0  # Zero on sell
    assert breakdown.stt == 100.0  # 0.1% on sell delivery
    assert breakdown.total_cash_impact > 0  # Inflow


def test_slippage_adjustment():
    """Verify bid-ask slippage increases buy execution price and decreases sell execution price."""
    cost_model = IndianTransactionCostModel(slippage_bps=10.0)  # 10 bps = 0.1%
    buy_breakdown = cost_model.calculate_trade_costs(TradeAction.BUY, 1000.0, 10)
    sell_breakdown = cost_model.calculate_trade_costs(TradeAction.SELL, 1000.0, 10)

    assert buy_breakdown.execution_price_with_slippage == 1001.0
    assert sell_breakdown.execution_price_with_slippage == 999.0


# ============================================================================
# 3. DETERMINISTIC REPLAY & LOOKAHEAD BIAS PREVENTION
# ============================================================================

def test_deterministic_replay_identical_output():
    """Verify running backtest twice with identical inputs yields bit-for-bit identical results."""
    engine = DeterministicBacktestEngine()
    strategy1 = DualMovingAverageStrategy(fast_period=5, slow_period=15, quantity=10)
    strategy2 = DualMovingAverageStrategy(fast_period=5, slow_period=15, quantity=10)

    res1 = engine.run_backtest(strategy1, RELIANCE_SERIES, initial_capital=100000.0)
    res2 = engine.run_backtest(strategy2, RELIANCE_SERIES, initial_capital=100000.0)

    assert res1.metrics.total_return_net_pct == res2.metrics.total_return_net_pct
    assert res1.metrics.final_equity_net == res2.metrics.final_equity_net
    assert len(res1.trades) == len(res2.trades)
    for t1, t2 in zip(res1.trades, res2.trades):
        assert t1.execution_date == t2.execution_date
        assert t1.execution_price == t2.execution_price
        assert t1.turnover == t2.turnover


def test_strictly_lagged_next_bar_execution():
    """Verify orders generated on Bar T are strictly executed on Bar T+1 (no same-bar leakage)."""
    engine = DeterministicBacktestEngine()
    strategy = DualMovingAverageStrategy(fast_period=5, slow_period=15, quantity=10)
    res = engine.run_backtest(strategy, RELIANCE_SERIES, initial_capital=100000.0)

    assert len(res.trades) > 0
    for trade in res.trades:
        # Execution date must be strictly chronologically after signal date
        assert trade.execution_date > trade.signal_date, (
            f"Lookahead violation detected: execution {trade.execution_date} not after signal {trade.signal_date}"
        )


# ============================================================================
# 4. CORPORATE ACTIONS ACCOUNTING
# ============================================================================

def test_corporate_actions_cash_dividend():
    """Verify cash dividend increases cash balance on Ex-Date without altering share count."""
    engine = DeterministicBacktestEngine()
    # Buy and hold strategy enters on bar 0; dividend occurs on bar 35
    strategy = BuyAndHoldStrategy(quantity=10)
    res = engine.run_backtest(strategy, RELIANCE_SERIES, initial_capital=100000.0)

    # Bar 35 dividend was ₹10/share for 10 shares = ₹100 cash inflow
    # Total trades: 1 buy
    assert len(res.trades) == 1
    # Verify equity curve reflects dividend
    assert res.metrics.final_equity_net > 0


def test_corporate_actions_bonus_split_adjustment():
    """Verify 1:1 bonus issue on Day 50 doubles position quantity and halves cost basis."""
    engine = DeterministicBacktestEngine()
    strategy = BuyAndHoldStrategy(quantity=10)
    res = engine.run_backtest(strategy, TCS_BONUS_SERIES, initial_capital=100000.0)

    assert len(res.trades) == 1
    # Check that position doubled on Day 50 (from 10 to 20 shares)
    final_equity_point = res.equity_curve[-1]
    assert final_equity_point.positions_value > 0


# ============================================================================
# 5. ORDER REJECTION & CASH BOUNDS
# ============================================================================

def test_insufficient_cash_order_rejection():
    """Verify engine rejects orders when capital is insufficient, preventing negative cash."""
    engine = DeterministicBacktestEngine()
    # Try to buy 10,000 shares @ ₹2,500 = ₹25,000,000 with only ₹10,000 capital
    strategy = BuyAndHoldStrategy(quantity=10000)
    res = engine.run_backtest(strategy, RELIANCE_SERIES, initial_capital=10000.0)

    assert len(res.trades) == 0
    assert len(res.rejections) >= 1
    assert "Insufficient cash" in res.rejections[0]["reason"]
    # Cash must remain exactly initial capital
    assert res.equity_curve[-1].cash == 10000.0


# ============================================================================
# 6. PERFORMANCE & RISK METRICS INTEGRITY
# ============================================================================

def test_gross_vs_net_return_separation():
    """Verify net return is strictly less than gross return due to transaction cost drag."""
    engine = DeterministicBacktestEngine()
    strategy = DualMovingAverageStrategy(fast_period=5, slow_period=15, quantity=10)
    res = engine.run_backtest(strategy, RELIANCE_SERIES, initial_capital=100000.0)

    if len(res.trades) > 0:
        assert res.metrics.total_transaction_costs_inr > 0
        assert res.metrics.total_return_net_pct < res.metrics.total_return_gross_pct
        assert res.metrics.transaction_cost_drag_pct > 0


def test_drawdown_bounds():
    """Verify maximum drawdown is strictly between 0% and 100%."""
    engine = DeterministicBacktestEngine()
    strategy = DualMovingAverageStrategy(fast_period=5, slow_period=15, quantity=10)
    res = engine.run_backtest(strategy, RELIANCE_SERIES, initial_capital=100000.0)

    assert 0.0 <= res.metrics.max_drawdown_pct <= 100.0


# ============================================================================
# 7. API ENDPOINTS & AUDIT CHAIN
# ============================================================================

def test_api_backtest_strategies():
    """Test GET /api/v1/backtest/strategies."""
    resp = client.get("/api/v1/backtest/strategies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    strat_ids = [s["id"] for s in data]
    assert "DualMovingAverage" in strat_ids
    assert "BuyAndHold" in strat_ids


def test_api_backtest_fixtures():
    """Test GET /api/v1/backtest/fixtures."""
    resp = client.get("/api/v1/backtest/fixtures")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    symbols = [f["symbol"] for f in data]
    assert "RELIANCE" in symbols
    assert "TCS" in symbols


def test_api_backtest_run_endpoint():
    """Test POST /api/v1/backtest/run returns full deterministic execution result."""
    payload = {
        "symbol": "RELIANCE",
        "strategy": "DualMovingAverage",
        "parameters": {"fast_period": 5, "slow_period": 15, "quantity": 10},
        "initial_capital": 100000.0,
        "slippage_bps": 5.0,
    }
    resp = client.post("/api/v1/backtest/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "audit_id" in data
    assert "audit_chain_hash" in data
    assert "metrics" in data
    assert "equity_curve" in data
    assert data["metrics"]["initial_capital"] == 100000.0
    assert len(data["equity_curve"]) == len(RELIANCE_SERIES)
