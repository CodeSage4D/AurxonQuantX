"""AURXON Phase 3, Stage 2 Test Suite:
Persistent Paper Trading Portfolio Manager, Order Lifecycle, Risk Limits,
Kill Switch, Restart Recovery, Cash Conservation, and Data Provenance.
"""

from pathlib import Path
import json
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.market import DataClassification, FreshnessStatus
from app.schemas.paper_trading import (
    CancelOrderRequest,
    KillSwitchRequest,
    PaperCorporateActionRequest,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    RiskLimits,
)
from app.trading.costs import IndianTransactionCostModel, InstrumentType
from app.trading.paper_manager import PaperPortfolioManager

client = TestClient(app)


@pytest.fixture
def temp_paper_manager():
    """Provides an isolated PaperPortfolioManager with a clean temporary SQLite database."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_paper_portfolio.sqlite"
        cost_model = IndianTransactionCostModel(slippage_bps=5.0)
        manager = PaperPortfolioManager(db_path=db_path, cost_model=cost_model)
        yield manager


# ============================================================================
# 1. CASH CONSERVATION & ORDER EXECUTION
# ============================================================================

def test_paper_trading_cash_conservation_buy_and_sell(temp_paper_manager):
    """Verify virtual cash is strictly conserved across Buy and Sell transactions."""
    manager = temp_paper_manager
    port = manager.get_or_create_portfolio("TEST_PORT", initial_cash=1000000.0)
    assert port.current_cash == 1000000.0

    # 1. Buy 100 shares of Reliance @ benchmark price (~₹2,500)
    buy_req = PaperOrderRequest(
        portfolio_id="TEST_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=100,
        order_type=PaperOrderType.MARKET,
    )
    buy_order = manager.submit_order(buy_req)
    assert buy_order.status == PaperOrderStatus.FILLED
    assert buy_order.executed_quantity == 100
    assert buy_order.turnover > 0
    assert buy_order.transaction_costs > 0

    # Verify cash decreased by exact turnover + transaction costs
    expected_outflow = buy_order.turnover + buy_order.transaction_costs
    port_after_buy = manager.get_portfolio_state("TEST_PORT")
    assert round(port_after_buy.current_cash, 2) == round(1000000.0 - expected_outflow, 2)
    assert "RELIANCE" in port_after_buy.positions
    assert port_after_buy.positions["RELIANCE"].quantity == 100

    # 2. Sell 50 shares of Reliance
    sell_req = PaperOrderRequest(
        portfolio_id="TEST_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.SELL,
        quantity=50,
        order_type=PaperOrderType.MARKET,
    )
    sell_order = manager.submit_order(sell_req)
    assert sell_order.status == PaperOrderStatus.FILLED
    assert sell_order.executed_quantity == 50

    # Verify cash increased by exact net proceeds (turnover - costs)
    net_proceeds = sell_order.turnover - sell_order.transaction_costs
    port_after_sell = manager.get_portfolio_state("TEST_PORT")
    expected_cash_after_sell = port_after_buy.current_cash + net_proceeds
    assert round(port_after_sell.current_cash, 2) == round(expected_cash_after_sell, 2)
    assert port_after_sell.positions["RELIANCE"].quantity == 50


def test_paper_trading_insufficient_cash_rejection(temp_paper_manager):
    """Verify orders requiring more than available cash are rejected without negative cash balance."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("LOW_CASH_PORT", initial_cash=10000.0)

    # Attempt to buy 100 shares of Reliance (~₹2,50,000) with only ₹10,000
    req = PaperOrderRequest(
        portfolio_id="LOW_CASH_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=100,
        order_type=PaperOrderType.MARKET,
    )
    order = manager.submit_order(req)
    assert order.status == PaperOrderStatus.REJECTED
    assert "INSUFFICIENT_CASH" in order.rejection_reason

    # Cash must remain unchanged
    port = manager.get_portfolio_state("LOW_CASH_PORT")
    assert port.current_cash == 10000.0
    assert len(port.positions) == 0


def test_paper_trading_insufficient_shares_rejection(temp_paper_manager):
    """Verify sell order exceeding held quantity is rejected."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("TEST_PORT", initial_cash=500000.0)

    # Attempt to sell without holding
    sell_req = PaperOrderRequest(
        portfolio_id="TEST_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.SELL,
        quantity=10,
        order_type=PaperOrderType.MARKET,
    )
    order = manager.submit_order(sell_req)
    assert order.status == PaperOrderStatus.REJECTED
    assert "INSUFFICIENT_SHARES" in order.rejection_reason


# ============================================================================
# 2. IDEMPOTENCY & DUPLICATE-EVENT PROTECTION
# ============================================================================

def test_paper_trading_idempotency_duplicate_protection(temp_paper_manager):
    """Verify submitting order with identical idempotency_key returns cached order without double-spending."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("IDEMP_PORT", initial_cash=1000000.0)

    key = f"IDEMP-KEY-{uuid.uuid4().hex[:8]}"
    req1 = PaperOrderRequest(
        portfolio_id="IDEMP_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=10,
        idempotency_key=key,
    )
    order1 = manager.submit_order(req1)
    assert order1.status == PaperOrderStatus.FILLED

    cash_after_first = manager.get_portfolio_state("IDEMP_PORT").current_cash

    # Submit second request with IDENTICAL idempotency key
    req2 = PaperOrderRequest(
        portfolio_id="IDEMP_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=10,
        idempotency_key=key,
    )
    order2 = manager.submit_order(req2)

    # Must return identical order ID
    assert order2.order_id == order1.order_id
    # Cash must NOT have been deducted a second time
    cash_after_second = manager.get_portfolio_state("IDEMP_PORT").current_cash
    assert cash_after_second == cash_after_first
    # Position quantity must remain 10, not 20
    assert manager.get_portfolio_state("IDEMP_PORT").positions["RELIANCE"].quantity == 10


# ============================================================================
# 3. RESTART RECOVERY & PERSISTENCE
# ============================================================================

def test_paper_trading_restart_recovery(temp_paper_manager):
    """Verify that restarting manager and reopening SQLite recovers exact portfolio state."""
    db_file = temp_paper_manager.db_path
    manager1 = temp_paper_manager

    manager1.get_or_create_portfolio("PERSIST_PORT", initial_cash=500000.0)
    buy_order = manager1.submit_order(
        PaperOrderRequest(
            portfolio_id="PERSIST_PORT",
            symbol="TCS",
            side=PaperOrderSide.BUY,
            quantity=20,
        )
    )
    assert buy_order.status == PaperOrderStatus.FILLED

    state_before_restart = manager1.get_portfolio_state("PERSIST_PORT")

    # Simulate restart by creating a new manager pointing to the same SQLite database
    manager2 = PaperPortfolioManager(db_path=db_file)
    state_after_restart = manager2.get_portfolio_state("PERSIST_PORT")

    assert state_after_restart.current_cash == state_before_restart.current_cash
    assert state_after_restart.positions_value == state_before_restart.positions_value
    assert state_after_restart.total_equity == state_before_restart.total_equity
    assert "TCS" in state_after_restart.positions
    assert state_after_restart.positions["TCS"].quantity == 20
    assert state_after_restart.positions["TCS"].average_cost == state_before_restart.positions["TCS"].average_cost


# ============================================================================
# 4. ORDER LIFECYCLE: LIMIT ORDERS & CANCELLATIONS
# ============================================================================

def test_paper_trading_limit_order_lifecycle_and_cancellation(temp_paper_manager):
    """Verify limit order placement when price not met and cancellation lifecycle."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("LIMIT_PORT", initial_cash=500000.0)

    # Reliance trades at ~₹2,500. Place a BUY limit order at ₹2,000 (below market)
    limit_req = PaperOrderRequest(
        portfolio_id="LIMIT_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=10,
        order_type=PaperOrderType.LIMIT,
        limit_price=2000.0,
    )
    order = manager.submit_order(limit_req)
    assert order.status == PaperOrderStatus.SUBMITTED
    assert order.executed_quantity == 0

    # Cancel the submitted order
    cancel_req = CancelOrderRequest(portfolio_id="LIMIT_PORT", order_id=order.order_id)
    cancelled = manager.cancel_order(cancel_req)
    assert cancelled.status == PaperOrderStatus.CANCELLED


# ============================================================================
# 5. RISK LIMITS & KILL SWITCH VETOES
# ============================================================================

def test_paper_trading_kill_switch_veto(temp_paper_manager):
    """Verify emergency kill switch halts all incoming simulated orders."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("KILL_PORT", initial_cash=500000.0)

    # Engage kill switch
    manager.toggle_kill_switch(KillSwitchRequest(portfolio_id="KILL_PORT", active=True, reason="Risk spike"))
    state = manager.get_portfolio_state("KILL_PORT")
    assert state.kill_switch_active is True

    # Attempt to place order
    req = PaperOrderRequest(
        portfolio_id="KILL_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=10,
    )
    rejected_order = manager.submit_order(req)
    assert rejected_order.status == PaperOrderStatus.REJECTED
    assert "KILL_SWITCH_ENGAGED" in rejected_order.rejection_reason

    # Disengage kill switch and verify order now succeeds
    manager.toggle_kill_switch(KillSwitchRequest(portfolio_id="KILL_PORT", active=False))
    accepted_order = manager.submit_order(req)
    assert accepted_order.status == PaperOrderStatus.FILLED


def test_paper_trading_max_order_value_risk_veto(temp_paper_manager):
    """Verify orders exceeding max order value threshold are rejected."""
    manager = temp_paper_manager
    # Default max order value is ₹5,00,000
    manager.get_or_create_portfolio("RISK_PORT", initial_cash=2000000.0)

    # 1000 shares of Reliance @ ₹2,500 = ₹25,00,000 (exceeds ₹5,00,000 limit)
    req = PaperOrderRequest(
        portfolio_id="RISK_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=1000,
    )
    order = manager.submit_order(req)
    assert order.status == PaperOrderStatus.REJECTED
    assert "RISK_LIMIT_EXCEEDED" in order.rejection_reason


# ============================================================================
# 6. CORPORATE ACTION HANDLING ON PAPER PORTFOLIO
# ============================================================================

def test_paper_trading_corporate_action_cash_dividend(temp_paper_manager):
    """Verify cash dividend increases virtual cash without changing share count."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("CA_PORT", initial_cash=1000000.0)

    # Buy 50 shares of Reliance (~₹1,25,000 = 12.5% of ₹10,00,000 <= 30% limit)
    buy_res = manager.submit_order(
        PaperOrderRequest(portfolio_id="CA_PORT", symbol="RELIANCE", side=PaperOrderSide.BUY, quantity=50)
    )
    assert buy_res.status == PaperOrderStatus.FILLED
    cash_before_div = manager.get_portfolio_state("CA_PORT").current_cash

    # Simulate ₹15/share dividend on 50 shares = ₹750 cash inflow
    res = manager.apply_corporate_action(
        PaperCorporateActionRequest(
            portfolio_id="CA_PORT", symbol="RELIANCE", action_type="CASH_DIVIDEND", dividend_amount_inr=15.0
        )
    )
    assert res["status"] == "SUCCESS"
    assert res["credited_inr"] == 750.0

    port_after_div = manager.get_portfolio_state("CA_PORT")
    assert round(port_after_div.current_cash, 2) == round(cash_before_div + 750.0, 2)
    assert port_after_div.positions["RELIANCE"].quantity == 50


def test_paper_trading_corporate_action_bonus_split(temp_paper_manager):
    """Verify 1:1 bonus issue doubles position quantity and halves average cost."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("BONUS_PORT", initial_cash=1000000.0)

    # Buy 20 shares of TCS (~₹72,000 = 7.2% of ₹10,00,000 <= 30% limit)
    buy_res = manager.submit_order(
        PaperOrderRequest(portfolio_id="BONUS_PORT", symbol="TCS", side=PaperOrderSide.BUY, quantity=20)
    )
    assert buy_res.status == PaperOrderStatus.FILLED
    pos_before = manager.get_portfolio_state("BONUS_PORT").positions["TCS"]
    assert pos_before.quantity == 20
    avg_before = pos_before.average_cost

    # Apply 1:1 bonus issue (ratio = 2.0)
    res = manager.apply_corporate_action(
        PaperCorporateActionRequest(
            portfolio_id="BONUS_PORT", symbol="TCS", action_type="BONUS_ISSUE", split_ratio=2.0
        )
    )
    assert res["status"] == "SUCCESS"
    assert res["new_shares"] == 40

    pos_after = manager.get_portfolio_state("BONUS_PORT").positions["TCS"]
    assert pos_after.quantity == 40
    assert round(pos_after.average_cost, 2) == round(avg_before / 2.0, 2)


# ============================================================================
# 7. MARKET DATA PROVENANCE & MISSING DATA VETO
# ============================================================================

def test_paper_trading_unverified_ticker_rejection_without_silent_fallback(temp_paper_manager):
    """Verify order for unsupported/unknown ticker is rejected without silent substitution."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("DATA_PORT", initial_cash=500000.0)

    req = PaperOrderRequest(
        portfolio_id="DATA_PORT",
        symbol="NONEXISTENT_STOCK_XYZ",
        side=PaperOrderSide.BUY,
        quantity=10,
    )
    order = manager.submit_order(req)
    assert order.status == PaperOrderStatus.REJECTED
    assert "DATA_UNAVAILABLE" in order.rejection_reason


# ============================================================================
# 8. REST API ENDPOINTS INTEGRATION
# ============================================================================

def test_api_paper_trading_portfolio_endpoint():
    """Test GET /api/v1/paper/portfolio returns valid state with simulation banner."""
    resp = client.get("/api/v1/paper/portfolio?portfolio_id=API_TEST_PORT")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_paper_trading"] is True
    assert "PAPER TRADING ONLY" in data["environment_banner"]
    assert "current_cash" in data
    assert "positions" in data


def test_api_paper_trading_order_submission_endpoint():
    """Test POST /api/v1/paper/order executes simulated fill."""
    key = f"API-ORDER-{uuid.uuid4().hex[:8]}"
    payload = {
        "portfolio_id": "API_TEST_PORT",
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 5,
        "order_type": "MARKET",
        "idempotency_key": key,
    }
    resp = client.post("/api/v1/paper/order", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["FILLED", "REJECTED"]
    assert data["order_id"].startswith("ORD-PAP-")
    assert data["is_demonstration"] is True


def test_api_paper_trading_kill_switch_endpoint():
    """Test POST /api/v1/paper/kill-switch engages and disengages switch."""
    resp = client.post("/api/v1/paper/kill-switch", json={"portfolio_id": "API_TEST_PORT", "active": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["kill_switch_active"] is True

    # Re-enable
    resp2 = client.post("/api/v1/paper/kill-switch", json={"portfolio_id": "API_TEST_PORT", "active": False})
    assert resp2.status_code == 200
    assert resp2.json()["kill_switch_active"] is False


def test_paper_trading_daily_loss_risk_veto(temp_paper_manager):
    """Verify daily stop-loss limit halts new orders when cumulative daily loss threshold is crossed."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("LOSS_PORT", initial_cash=1000000.0)

    # Configure strict daily stop-loss limit: ₹2,000
    with sqlite3.connect(manager.db_path) as conn:
        limits = RiskLimits(max_daily_loss_inr=2000.0, include_unrealized_in_daily_loss=True)
        conn.execute(
            "UPDATE paper_portfolios SET risk_limits_json = ? WHERE portfolio_id = ?",
            (json.dumps(limits.model_dump()), "LOSS_PORT"),
        )
        # Seed an existing position with a heavy unrealized loss: 100 shares bought at ₹3000, current price ₹2500 -> ₹50,000 loss
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO paper_positions (portfolio_id, symbol, quantity, average_cost, current_price, realized_pnl, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("LOSS_PORT", "RELIANCE", 100, 3000.0, 2500.0, 0.0, now_iso),
        )

    # Now attempt a new order - should be vetoed by daily stop-loss
    req = PaperOrderRequest(
        portfolio_id="LOSS_PORT",
        symbol="TCS",
        side=PaperOrderSide.BUY,
        quantity=5,
    )
    rej = manager.submit_order(req)
    assert rej.status == PaperOrderStatus.REJECTED
    assert "DAILY_STOP_LOSS_EXCEEDED" in rej.rejection_reason


def test_paper_trading_max_drawdown_risk_veto(temp_paper_manager):
    """Verify maximum portfolio drawdown circuit breaker restricts new buy orders."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("DD_PORT", initial_cash=1000000.0)

    # Set peak equity to ₹10,00,000, current cash to ₹8,00,000 (20% drawdown) and max_drawdown_pct to 10%
    with sqlite3.connect(manager.db_path) as conn:
        limits = RiskLimits(max_drawdown_pct=10.0)
        conn.execute(
            "UPDATE paper_portfolios SET current_cash = 800000.0, peak_equity = 1000000.0, risk_limits_json = ? WHERE portfolio_id = ?",
            (json.dumps(limits.model_dump()), "DD_PORT"),
        )

    req = PaperOrderRequest(
        portfolio_id="DD_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=10,
    )
    rej = manager.submit_order(req)
    assert rej.status == PaperOrderStatus.REJECTED
    assert "MAX_DRAWDOWN_EXCEEDED" in rej.rejection_reason


def test_paper_trading_stale_market_data_veto(temp_paper_manager, monkeypatch):
    """Verify market quotes with STALE_WARNING freshness status are rejected."""
    manager = temp_paper_manager
    manager.get_or_create_portfolio("STALE_PORT", initial_cash=1000000.0)

    # Mock _resolve_market_price to return STALE_WARNING
    def mock_resolve_stale(symbol):
        return (2500.0, DataClassification.DELAYED_VERIFIED, FreshnessStatus.STALE_WARNING, "MOCK_STALE_FEED")

    monkeypatch.setattr(manager, "_resolve_market_price", mock_resolve_stale)

    req = PaperOrderRequest(
        portfolio_id="STALE_PORT",
        symbol="RELIANCE",
        side=PaperOrderSide.BUY,
        quantity=5,
    )
    rej = manager.submit_order(req)
    assert rej.status == PaperOrderStatus.REJECTED
    assert "STALE_MARKET_DATA" in rej.rejection_reason

