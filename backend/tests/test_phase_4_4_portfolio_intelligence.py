"""AURXON Phase 4.4 Test Suite:
Portfolio Intelligence, Factor Attribution, Performance Methodology & Paper Rebalancing.
Covers Workstreams A, B, C, D, E, G, H.
"""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.schemas.portfolio_intelligence import (
    PricingStatus,
    RebalanceConstraints,
    StressScenarioType,
)
from app.schemas.paper_trading import (
    KillSwitchRequest,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
)
from app.trading.costs import IndianTransactionCostModel
from app.trading.paper_manager import PaperPortfolioManager
from app.trading.portfolio_analytics import PortfolioAnalyticsEngine
from app.analytics.factor_attribution import FactorAttributionEngine
from app.trading.rebalancing import PaperRebalancingEngine
from app.trading.stress_testing import PortfolioStressTestingEngine

from app.auth.security import create_access_token

client = TestClient(app)
client.headers["Authorization"] = f"Bearer {create_access_token('USR_SYSTEM', role='ADMIN')}"


@pytest.fixture
def isolated_portfolio_env():
    """Provides an isolated PaperPortfolioManager and connected analytics engines."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_portfolio_p44.sqlite"
        cost_model = IndianTransactionCostModel(slippage_bps=5.0)
        manager = PaperPortfolioManager(db_path=db_path, cost_model=cost_model)
        analytics = PortfolioAnalyticsEngine()
        factors = FactorAttributionEngine()
        rebalancing = PaperRebalancingEngine(cost_model=cost_model, paper_manager=manager)
        stress = PortfolioStressTestingEngine()

        # Seed initial portfolio with 1,000,000 INR
        manager.get_or_create_portfolio("P_TEST", initial_cash=1000000.0, name="Alpha Test Portfolio")

        # Execute initial buys: 50 shares of RELIANCE and 50 shares of TCS (within 30% position limits)
        manager.submit_order(
            PaperOrderRequest(portfolio_id="P_TEST", symbol="RELIANCE", side=PaperOrderSide.BUY, quantity=50)
        )
        manager.submit_order(
            PaperOrderRequest(portfolio_id="P_TEST", symbol="TCS", side=PaperOrderSide.BUY, quantity=50)
        )

        yield {
            "manager": manager,
            "analytics": analytics,
            "factors": factors,
            "rebalancing": rebalancing,
            "stress": stress,
        }


# ============================================================================
# 1. WORKSTREAM A: PORTFOLIO INVENTORY, SNAPSHOTS & CONCENTRATION
# ============================================================================

def test_multi_portfolio_listing_and_isolation(isolated_portfolio_env):
    """Verify distinct paper portfolios can be created, isolated, and listed."""
    manager = isolated_portfolio_env["manager"]

    # Create a secondary portfolio
    manager.get_or_create_portfolio("P_MOMENTUM", initial_cash=500000.0, name="Momentum Sleeve")
    
    portfolios = manager.list_portfolios()
    assert len(portfolios) >= 2
    ids = [p["portfolio_id"] for p in portfolios]
    assert "P_TEST" in ids
    assert "P_MOMENTUM" in ids


def test_durable_portfolio_snapshots(isolated_portfolio_env):
    """Verify periodic mark-to-market portfolio snapshots are recorded and retrievable."""
    manager = isolated_portfolio_env["manager"]
    
    snap1 = manager.record_portfolio_snapshot("P_TEST")
    assert snap1["snapshot_id"] is not None
    assert snap1["total_equity"] > 0
    assert snap1["positions_count"] == 2

    history = manager.get_portfolio_snapshots("P_TEST")
    assert len(history) >= 1
    assert history[0]["portfolio_id"] == "P_TEST"
    assert "RELIANCE" in history[0]["positions"]


def test_holdings_inventory_and_concentration_analysis(isolated_portfolio_env):
    """Verify sector mapping, concentration weights, and Herfindahl index calculation."""
    manager = isolated_portfolio_env["manager"]
    analytics = isolated_portfolio_env["analytics"]

    state = manager.get_portfolio_state("P_TEST")
    holdings, conc = analytics.build_holdings_inventory(state)

    assert len(holdings) == 2
    symbols = [h.symbol for h in holdings]
    assert "RELIANCE" in symbols
    assert "TCS" in symbols

    # Check sectors mapped
    rel_h = next(h for h in holdings if h.symbol == "RELIANCE")
    assert "Energy" in rel_h.sector
    tcs_h = next(h for h in holdings if h.symbol == "TCS")
    assert "IT Services" in tcs_h.sector

    # Concentration check
    assert conc.top_position_weight_pct > 0.0
    assert conc.top_3_positions_weight_pct > 0.0
    assert conc.herfindahl_index > 0.0
    assert "CASH" in conc.asset_class_weights
    assert "EQUITY" in conc.asset_class_weights


# ============================================================================
# 2. WORKSTREAM B: PERFORMANCE, TWR, MWR & TRACKING ERROR
# ============================================================================

def test_time_weighted_return_calculation(isolated_portfolio_env):
    """Verify subperiod geometric linking for Time-Weighted Return (TWR)."""
    analytics = isolated_portfolio_env["analytics"]

    # Subperiod returns: +5%, -2%, +3%
    # Compound: (1.05) * (0.98) * (1.03) = 1.05987 - 1 = +5.99%
    subperiods = [0.05, -0.02, 0.03]
    twr = analytics.calculate_time_weighted_return(subperiods)
    assert twr == pytest.approx(5.99, 0.01)

    # Empty subperiods returns None
    assert analytics.calculate_time_weighted_return([]) is None


def test_money_weighted_return_irr_bisection_solver(isolated_portfolio_env):
    """Verify Money-Weighted Return (MWR / IRR) solver on dated cash flows."""
    analytics = isolated_portfolio_env["analytics"]

    # Initial cash: 1,000,000 INR
    # Final equity: 1,100,000 INR after 1 full year with zero intermediate cash flows -> exactly 10.0% IRR
    mwr = analytics.calculate_money_weighted_return(
        initial_cash=1000000.0,
        final_equity=1100000.0,
        cash_flows=[],
        total_days=365,
    )
    assert mwr == pytest.approx(10.0, 0.05)

    # Intermediate cash flow: Deposit 500,000 at day 180, final equity 1,600,000 at day 365
    mwr_cf = analytics.calculate_money_weighted_return(
        initial_cash=1000000.0,
        final_equity=1600000.0,
        cash_flows=[(180, 500000.0)],
        total_days=365,
    )
    assert mwr_cf is not None
    assert 5.0 < mwr_cf < 15.0


def test_tracking_error_and_benchmark_metrics(isolated_portfolio_env):
    """Verify tracking error, beta, and information ratio against benchmark series."""
    analytics = isolated_portfolio_env["analytics"]

    # Aligned 10-day return series
    p_returns = [0.01, 0.02, -0.01, 0.005, 0.015, -0.005, 0.02, 0.01, -0.01, 0.005]
    b_returns = [0.008, 0.015, -0.008, 0.004, 0.012, -0.004, 0.018, 0.009, -0.008, 0.004]

    metrics = analytics.calculate_tracking_error_and_benchmark_metrics(p_returns, b_returns)
    assert metrics["tracking_error_pct"] is not None
    assert metrics["tracking_error_pct"] >= 0.0
    assert metrics["portfolio_beta"] is not None
    assert metrics["portfolio_beta"] > 0.0
    assert metrics["active_return_pct"] is not None


# ============================================================================
# 3. WORKSTREAM C: FACTOR ATTRIBUTION
# ============================================================================

def test_factor_attribution_engine_exposures(isolated_portfolio_env):
    """Verify factor tilts: Market Beta, Momentum, Value, Quality, Volatility, and Size."""
    manager = isolated_portfolio_env["manager"]
    analytics = isolated_portfolio_env["analytics"]
    factors = isolated_portfolio_env["factors"]

    state = manager.get_portfolio_state("P_TEST")
    holdings, _ = analytics.build_holdings_inventory(state)

    report = factors.analyze_portfolio_factors(holdings, portfolio_id="P_TEST")
    assert report.portfolio_id == "P_TEST"
    assert len(report.factors) == 6

    factor_names = [f.factor_name for f in report.factors]
    assert any("Beta" in name for name in factor_names)
    assert any("Momentum" in name for name in factor_names)
    assert any("Value" in name for name in factor_names)
    assert any("Quality" in name for name in factor_names)
    assert any("Volatility" in name for name in factor_names)
    assert any("Size" in name for name in factor_names)

    # Every factor tile must declare sample size and disclaimer
    for f in report.factors:
        assert f.sample_size_observations > 0
        assert f.portfolio_exposure_score is not None
        assert f.limitations_disclaimer is not None


def test_factor_attribution_handles_empty_portfolio(isolated_portfolio_env):
    """Verify factor engine cleanly returns UNAVAILABLE status on empty portfolio."""
    factors = isolated_portfolio_env["factors"]
    report = factors.analyze_portfolio_factors([], portfolio_id="EMPTY_PORT")
    
    assert len(report.factors) == 6
    for f in report.factors:
        assert f.is_available is False
        assert f.tilt_status == "UNAVAILABLE"


# ============================================================================
# 4. WORKSTREAM D: REBALANCING ENGINE
# ============================================================================

def test_rebalancing_simulation_generates_integer_lots_and_respects_constraints(isolated_portfolio_env):
    """Verify target rebalancing produces valid integer trades, models costs, and respects cash buffer."""
    manager = isolated_portfolio_env["manager"]
    rebalancing = isolated_portfolio_env["rebalancing"]

    state = manager.get_portfolio_state("P_TEST")
    
    # Target: 30% Reliance, 30% TCS, 20% INFY, reserving 20% cash
    target_weights = {
        "RELIANCE": 0.30,
        "TCS": 0.30,
        "INFY": 0.20,
    }
    constraints = RebalanceConstraints(
        max_position_weight_pct=30.0,
        target_cash_reserve_pct=20.0,
        min_trade_size_inr=1000.0,
    )

    sim = rebalancing.simulate_rebalance(
        current_state=state,
        target_weights=target_weights,
        constraints=constraints,
    )

    assert sim.status in ["FEASIBLE", "QUALIFIED"]
    assert len(sim.proposed_trades) > 0

    # Ensure all proposed share deltas are positive integers
    for t in sim.proposed_trades:
        assert isinstance(t.share_delta, int)
        assert t.share_delta >= 0
        assert t.estimated_transaction_costs > 0.0

    # Sells must be ordered before Buys to release liquidity
    actions = [t.action for t in sim.proposed_trades]
    if "SELL" in actions and "BUY" in actions:
        first_buy_idx = actions.index("BUY")
        last_sell_idx = max(i for i, a in enumerate(actions) if a == "SELL")
        assert last_sell_idx < first_buy_idx


def test_rebalancing_execution_in_virtual_paper_ledger(isolated_portfolio_env):
    """Verify proposed trades can be sequentially executed in the paper portfolio ledger."""
    manager = isolated_portfolio_env["manager"]
    rebalancing = isolated_portfolio_env["rebalancing"]

    state = manager.get_portfolio_state("P_TEST")
    
    # Simple rebalancing: trim Reliance slightly, buy a small lot of INFY
    target_weights = {"RELIANCE": 0.20, "TCS": 0.25, "INFY": 0.15}
    sim = rebalancing.simulate_rebalance(current_state=state, target_weights=target_weights)

    executed = rebalancing.execute_paper_rebalancing(sim)
    assert len(executed) > 0
    
    # Verify post-rebalance state updated
    post_state = manager.get_portfolio_state("P_TEST")
    assert post_state.total_equity > 0


# ============================================================================
# 5. WORKSTREAM E: STRESS TESTING
# ============================================================================

def test_stress_testing_scenarios_and_var(isolated_portfolio_env):
    """Verify all 6 stress testing scenarios execute and return loss metrics and VaR."""
    manager = isolated_portfolio_env["manager"]
    analytics = isolated_portfolio_env["analytics"]
    stress = isolated_portfolio_env["stress"]

    state = manager.get_portfolio_state("P_TEST")
    holdings, _ = analytics.build_holdings_inventory(state)

    results = stress.run_all_stress_scenarios(state, holdings)
    assert len(results) >= 6

    scenario_types = [r.scenario_type for r in results]
    assert StressScenarioType.BROAD_MARKET_CRASH_10 in scenario_types
    assert StressScenarioType.BROAD_MARKET_CRASH_20 in scenario_types
    assert StressScenarioType.SECTOR_SHOCK_IT_15 in scenario_types
    assert StressScenarioType.SINGLE_STOCK_SHOCK_25 in scenario_types
    assert StressScenarioType.VOLATILITY_SURGE_50 in scenario_types
    assert StressScenarioType.LIQUIDITY_HAIRCUT in scenario_types

    for r in results:
        assert r.baseline_equity == state.total_equity
        assert r.stressed_equity <= r.baseline_equity
        assert r.estimated_loss_inr >= 0.0
        assert r.var_95_pct >= 0.0
        assert "Hypothetical" in r.disclaimer


# ============================================================================
# 6. WORKSTREAM G: SECURITY INVARIANTS & KILL SWITCH
# ============================================================================

def test_real_trading_invariant_and_kill_switch_blocks_rebalancing(isolated_portfolio_env):
    """Verify ENABLE_REAL_TRADING=false is strictly preserved and kill switch halts execution."""
    assert settings.ENABLE_REAL_TRADING is False

    manager = isolated_portfolio_env["manager"]
    rebalancing = isolated_portfolio_env["rebalancing"]

    # Toggle kill switch
    manager.toggle_kill_switch(KillSwitchRequest(portfolio_id="P_TEST", active=True, reason="Safety Audit"))

    state = manager.get_portfolio_state("P_TEST")
    assert state.kill_switch_active is True

    # Attempt rebalancing execution
    sim = rebalancing.simulate_rebalance(
        current_state=state,
        target_weights={"RELIANCE": 0.25, "TCS": 0.25},
    )
    executed = rebalancing.execute_paper_rebalancing(sim)
    
    # All submitted orders must be REJECTED by kill switch veto
    for trade in executed:
        assert trade["status"] == PaperOrderStatus.REJECTED.value
        assert "kill switch" in trade["rejection_reason"].lower()


# ============================================================================
# 7. WORKSTREAM H: REST API INTEGRATION
# ============================================================================

def test_api_portfolio_intelligence_and_list_endpoints():
    """Verify REST endpoints for listing portfolios and retrieving unified intelligence snapshot."""
    # List portfolios
    res_list = client.get("/api/v1/portfolio/list")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert isinstance(data_list, list)

    # Portfolio Intelligence snapshot
    res_intel = client.get("/api/v1/portfolio/intelligence?portfolio_id=DEFAULT")
    assert res_intel.status_code == 200
    intel = res_intel.json()
    assert "holdings" in intel
    assert "concentration" in intel
    assert "performance" in intel
    assert "factor_attribution" in intel
    assert "stress_scenarios_summary" in intel
    assert intel["environment_banner"] == "PAPER TRADING ONLY — SIMULATION ENVIRONMENT"
