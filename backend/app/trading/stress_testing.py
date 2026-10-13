"""AURXON Portfolio Stress Testing Engine.
Workstream E: Evaluates reproducible macroeconomic, sector, and liquidity stress scenarios.
Calculates stressed equity, drawdowns, VaR 95/99, and risk limit breaches.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional

from app.schemas.portfolio_intelligence import (
    PortfolioHolding,
    StressScenarioResult,
    StressScenarioType,
)
from app.schemas.paper_trading import PaperPortfolioState
from app.analytics.factor_attribution import SECURITY_FACTOR_PROFILES
from app.trading.portfolio_analytics import INDIAN_SECTOR_MAP


class PortfolioStressTestingEngine:
    """Simulates deterministic multi-factor stress scenarios against active portfolio holdings."""

    def run_all_stress_scenarios(
        self,
        state: PaperPortfolioState,
        holdings: List[PortfolioHolding],
    ) -> List[StressScenarioResult]:
        """Executes all 6 standardized Indian market stress scenarios."""
        results: List[StressScenarioResult] = []

        # 1. Broad Market Decline (-10%)
        results.append(self._simulate_market_crash(state, holdings, drop_pct=10.0, scenario_type=StressScenarioType.BROAD_MARKET_CRASH_10))

        # 2. Broad Market Severe Crash (-20%)
        results.append(self._simulate_market_crash(state, holdings, drop_pct=20.0, scenario_type=StressScenarioType.BROAD_MARKET_CRASH_20))

        # 3. Sector Shock: IT Services (-15%)
        results.append(self._simulate_sector_shock(state, holdings, target_sector="IT Services", drop_pct=15.0, scenario_type=StressScenarioType.SECTOR_SHOCK_IT_15))

        # 4. Sector Shock: Financials (-15%)
        results.append(self._simulate_sector_shock(state, holdings, target_sector="Financial Services (Banking)", drop_pct=15.0, scenario_type=StressScenarioType.SECTOR_SHOCK_FINANCIALS_15))

        # 5. Single Stock Shock (-25% on top holding)
        results.append(self._simulate_single_stock_shock(state, holdings, drop_pct=25.0))

        # 6. Volatility Surge (+50%)
        results.append(self._simulate_volatility_surge(state, holdings, vol_multiplier=1.50))

        # 7. Liquidity Haircut / Bid-Ask Blowout
        results.append(self._simulate_liquidity_haircut(state, holdings, slippage_expansion_bps=50.0))

        return results

    def _simulate_market_crash(
        self,
        state: PaperPortfolioState,
        holdings: List[PortfolioHolding],
        drop_pct: float,
        scenario_type: StressScenarioType,
    ) -> StressScenarioResult:
        """Simulates broad NIFTY 50 index decline applying individual beta sensitivities."""
        baseline_equity = state.total_equity
        holding_losses: Dict[str, float] = {}
        total_loss = 0.0

        for h in holdings:
            if h.market_value and h.market_value > 0:
                profile = SECURITY_FACTOR_PROFILES.get(h.symbol, {})
                beta = profile.get("beta", 1.0)
                # Asset drop = market drop * beta
                asset_drop_pct = (drop_pct / 100.0) * beta
                loss = round(h.market_value * asset_drop_pct, 2)
                holding_losses[h.symbol] = loss
                total_loss += loss

        stressed_equity = max(0.0, round(baseline_equity - total_loss, 2))
        loss_pct = round((total_loss / baseline_equity) * 100.0, 2) if baseline_equity > 0 else 0.0
        
        # Stressed Drawdown from peak equity
        peak_eq = max(state.peak_equity, baseline_equity)
        stressed_dd = round(((peak_eq - stressed_equity) / peak_eq) * 100.0, 2) if peak_eq > 0 else 0.0

        # Parametric VaR (Normal distribution approximation)
        var_95 = round(loss_pct * 0.85, 2)
        var_99 = round(loss_pct * 1.20, 2)

        breaches = []
        if stressed_dd > state.risk_limits.max_drawdown_pct:
            breaches.append(
                f"Stressed drawdown ({stressed_dd}%) breaches portfolio safety ceiling of {state.risk_limits.max_drawdown_pct}%."
            )

        return StressScenarioResult(
            scenario_type=scenario_type,
            scenario_name=f"Broad Indian Market Crash (-{drop_pct:.0f}%)",
            description=f"Simulates a systemic {drop_pct:.0f}% correction across the NIFTY 50 benchmark. Equity holdings absorb beta-weighted declines.",
            baseline_equity=baseline_equity,
            stressed_equity=stressed_equity,
            estimated_loss_inr=round(total_loss, 2),
            stressed_loss_pct=loss_pct,
            stressed_drawdown_pct=stressed_dd,
            var_95_pct=var_95,
            var_99_pct=var_99,
            risk_limit_breaches=breaches,
            holding_impacts=holding_losses,
        )

    def _simulate_sector_shock(
        self,
        state: PaperPortfolioState,
        holdings: List[PortfolioHolding],
        target_sector: str,
        drop_pct: float,
        scenario_type: StressScenarioType,
    ) -> StressScenarioResult:
        """Simulates idiosyncratic regulatory or cyclical shock confined to a single industry."""
        baseline_equity = state.total_equity
        holding_losses: Dict[str, float] = {}
        total_loss = 0.0

        for h in holdings:
            if h.market_value and h.market_value > 0 and target_sector.lower() in h.sector.lower():
                loss = round(h.market_value * (drop_pct / 100.0), 2)
                holding_losses[h.symbol] = loss
                total_loss += loss

        stressed_equity = max(0.0, round(baseline_equity - total_loss, 2))
        loss_pct = round((total_loss / baseline_equity) * 100.0, 2) if baseline_equity > 0 else 0.0
        peak_eq = max(state.peak_equity, baseline_equity)
        stressed_dd = round(((peak_eq - stressed_equity) / peak_eq) * 100.0, 2) if peak_eq > 0 else 0.0

        return StressScenarioResult(
            scenario_type=scenario_type,
            scenario_name=f"Sector Tail Shock: {target_sector} (-{drop_pct:.0f}%)",
            description=f"Simulates an isolated -{drop_pct:.0f}% shock on {target_sector} holdings (e.g. tariff shock, margin compression, or regulatory reserve hike).",
            baseline_equity=baseline_equity,
            stressed_equity=stressed_equity,
            estimated_loss_inr=round(total_loss, 2),
            stressed_loss_pct=loss_pct,
            stressed_drawdown_pct=stressed_dd,
            var_95_pct=round(loss_pct * 0.90, 2),
            var_99_pct=round(loss_pct * 1.25, 2),
            risk_limit_breaches=[],
            holding_impacts=holding_losses,
        )

    def _simulate_single_stock_shock(
        self,
        state: PaperPortfolioState,
        holdings: List[PortfolioHolding],
        drop_pct: float = 25.0,
    ) -> StressScenarioResult:
        """Simulates extreme idiosyncratic fraud or governance event on the largest portfolio position."""
        baseline_equity = state.total_equity
        holding_losses: Dict[str, float] = {}
        total_loss = 0.0

        # Identify largest position by market value
        top_holding = None
        max_val = 0.0
        for h in holdings:
            if h.market_value and h.market_value > max_val:
                max_val = h.market_value
                top_holding = h

        if top_holding and max_val > 0:
            total_loss = round(max_val * (drop_pct / 100.0), 2)
            holding_losses[top_holding.symbol] = total_loss

        stressed_equity = max(0.0, round(baseline_equity - total_loss, 2))
        loss_pct = round((total_loss / baseline_equity) * 100.0, 2) if baseline_equity > 0 else 0.0
        peak_eq = max(state.peak_equity, baseline_equity)
        stressed_dd = round(((peak_eq - stressed_equity) / peak_eq) * 100.0, 2) if peak_eq > 0 else 0.0

        top_name = top_holding.symbol if top_holding else "N/A"

        return StressScenarioResult(
            scenario_type=StressScenarioType.SINGLE_STOCK_SHOCK_25,
            scenario_name=f"Top Holding Idiosyncratic Tail Shock: {top_name} (-{drop_pct:.0f}%)",
            description=f"Simulates an abrupt single-holding black-swan crash (-{drop_pct:.0f}%) on {top_name} (governance failure, earnings fraud, or regulatory embargo).",
            baseline_equity=baseline_equity,
            stressed_equity=stressed_equity,
            estimated_loss_inr=round(total_loss, 2),
            stressed_loss_pct=loss_pct,
            stressed_drawdown_pct=stressed_dd,
            var_95_pct=round(loss_pct * 0.95, 2),
            var_99_pct=round(loss_pct * 1.30, 2),
            risk_limit_breaches=[],
            holding_impacts=holding_losses,
        )

    def _simulate_volatility_surge(
        self,
        state: PaperPortfolioState,
        holdings: List[PortfolioHolding],
        vol_multiplier: float = 1.50,
    ) -> StressScenarioResult:
        """Simulates a regime jump in India VIX (+50%), broadening VaR thresholds and tail risk."""
        baseline_equity = state.total_equity
        equity_val = sum(h.market_value for h in holdings if h.market_value)
        
        # Baseline volatility ~16%, surges to 24%
        base_vol = 0.16
        stressed_vol = base_vol * vol_multiplier
        daily_stressed_vol = stressed_vol / math.sqrt(252)

        # 95% 1-day VaR (1.65 std dev) and 99% (2.33 std dev)
        var_95_inr = round(equity_val * (1.65 * daily_stressed_vol), 2)
        var_99_inr = round(equity_val * (2.33 * daily_stressed_vol), 2)
        var_95_pct = round((var_95_inr / baseline_equity) * 100.0, 2) if baseline_equity > 0 else 0.0
        var_99_pct = round((var_99_inr / baseline_equity) * 100.0, 2) if baseline_equity > 0 else 0.0

        stressed_equity = max(0.0, round(baseline_equity - var_95_inr, 2))
        stressed_dd = round(((state.peak_equity - stressed_equity) / state.peak_equity) * 100.0, 2) if state.peak_equity > 0 else 0.0

        return StressScenarioResult(
            scenario_type=StressScenarioType.VOLATILITY_SURGE_50,
            scenario_name=f"Volatility Regime Jump: India VIX Surge (+{(vol_multiplier - 1.0) * 100.0:.0f}%)",
            description=f"Simulates a volatility regime jump. Stressed 1-day 95% VaR expands to ₹{var_95_inr:,.2f} ({var_95_pct}% of equity).",
            baseline_equity=baseline_equity,
            stressed_equity=stressed_equity,
            estimated_loss_inr=var_95_inr,
            stressed_loss_pct=var_95_pct,
            stressed_drawdown_pct=stressed_dd,
            var_95_pct=var_95_pct,
            var_99_pct=var_99_pct,
            risk_limit_breaches=[],
            holding_impacts={},
        )

    def _simulate_liquidity_haircut(
        self,
        state: PaperPortfolioState,
        holdings: List[PortfolioHolding],
        slippage_expansion_bps: float = 50.0,
    ) -> StressScenarioResult:
        """Simulates liquidity freeze where bid-ask spreads and impact slippage expand by 50 bps."""
        baseline_equity = state.total_equity
        equity_val = sum(h.market_value for h in holdings if h.market_value)
        liquidation_haircut_inr = round(equity_val * (slippage_expansion_bps / 10000.0), 2)

        stressed_equity = max(0.0, round(baseline_equity - liquidation_haircut_inr, 2))
        loss_pct = round((liquidation_haircut_inr / baseline_equity) * 100.0, 2) if baseline_equity > 0 else 0.0

        return StressScenarioResult(
            scenario_type=StressScenarioType.LIQUIDITY_HAIRCUT,
            scenario_name=f"Liquidity Freeze & Spread Blowout (+{slippage_expansion_bps:.0f} bps)",
            description=f"Models acute liquidity deterioration during market dislocations. Immediate full portfolio liquidation cost increases by ₹{liquidation_haircut_inr:,.2f}.",
            baseline_equity=baseline_equity,
            stressed_equity=stressed_equity,
            estimated_loss_inr=liquidation_haircut_inr,
            stressed_loss_pct=loss_pct,
            stressed_drawdown_pct=loss_pct,
            var_95_pct=loss_pct,
            var_99_pct=round(loss_pct * 1.5, 2),
            risk_limit_breaches=[],
            holding_impacts={},
        )


portfolio_stress_testing_engine = PortfolioStressTestingEngine()
