"""Tests for Mutual Fund and ETF Quantitative Analysis Engine.
Enforces Phase 2 Module B: Mutual Fund & ETF Intelligence.
"""

from app.funds.analyzer import (
    calculate_portfolio_overlap,
    calculate_tracking_error,
    compute_cagr,
    compute_direct_plan_savings,
    fund_analyzer,
)
from app.schemas.funds import HoldingItem


def test_cagr_calculation():
    # NAV doubles from 100 to 200 in 5 years: CAGR = (2)^(1/5) - 1 = 14.87%
    cagr = compute_cagr(start_nav=100.0, end_nav=200.0, years=5.0)
    assert round(cagr, 2) == 14.87

    # Edge cases
    assert compute_cagr(0.0, 100.0, 5.0) == 0.0
    assert compute_cagr(100.0, -10.0, 5.0) == 0.0


def test_portfolio_overlap_calculation():
    fund_a = [
        HoldingItem(company_name="HDFC Bank", symbol="HDFCBANK", weight_pct=10.0, sector="Financials"),
        HoldingItem(company_name="Reliance Industries", symbol="RELIANCE", weight_pct=8.0, sector="Energy"),
        HoldingItem(company_name="Infosys", symbol="INFY", weight_pct=6.0, sector="Tech"),
    ]
    fund_b = [
        HoldingItem(company_name="HDFC Bank", symbol="HDFCBANK", weight_pct=8.0, sector="Financials"),  # min = 8.0
        HoldingItem(company_name="Reliance Industries", symbol="RELIANCE", weight_pct=10.0, sector="Energy"),  # min = 8.0
        HoldingItem(company_name="TCS", symbol="TCS", weight_pct=5.0, sector="Tech"),  # not in A
    ]

    # Overlap must be min(10, 8) + min(8, 10) = 8 + 8 = 16.0%
    overlap = calculate_portfolio_overlap(fund_a, fund_b)
    assert overlap == 16.0


def test_direct_plan_compounding_savings():
    # ₹10 Lakhs invested for 10 years at 12% gross CAGR:
    # Direct TER 0.65% vs Regular TER 1.45% (80 bps difference)
    savings_lakhs = compute_direct_plan_savings(
        principal_inr=1000000.0,
        direct_ter_pct=0.65,
        regular_ter_pct=1.45,
        gross_annual_cagr=0.12,
        years=10,
    )
    # Direct saves approximately ₹2.2 to ₹2.6 Lakhs over a decade
    assert 2.0 < savings_lakhs < 3.0


def test_tracking_error_calculation():
    etf_daily = [0.01, 0.005, -0.008, 0.012, 0.002, -0.003, 0.004, 0.006, -0.001, 0.008]
    # Benchmark daily identical plus minor 0.01% noise
    bench_daily = [0.0099, 0.0049, -0.0081, 0.0121, 0.0020, -0.0029, 0.0041, 0.0059, -0.0011, 0.0081]

    te = calculate_tracking_error(etf_daily, bench_daily)
    assert 0.0 < te < 0.5  # Low tracking error for well-managed ETF


def test_fund_comparison_endpoint_logic():
    result = fund_analyzer.compare_funds("PPFAS_FLEXI", "NIFTYBEES")
    assert len(result.schemes) == 2
    assert "PPFAS_FLEXI" in result.metrics
    assert "NIFTYBEES" in result.metrics
    assert len(result.pairwise_overlap_pct) > 0
    # Overlap between PPFAS and NIFTYBEES (shares HDFC Bank, ICICI Bank, ITC, etc.)
    overlap_val = list(result.pairwise_overlap_pct.values())[0]
    assert 10.0 < overlap_val < 40.0
    assert result.direct_vs_regular_savings_10y_lakhs > 1.5


def test_goal_based_allocation_proposal():
    # Test aggressive wealth creation (10 years horizon)
    plan = fund_analyzer.generate_portfolio_allocation(
        goal_name="Long Term Wealth Creation",
        horizon_years=10,
        risk_profile="aggressive",
    )
    assert plan.recommended_equity_pct >= 75.0
    assert plan.recommended_debt_pct <= 15.0
    assert plan.downside_stress_scenario_drawdown_pct > 20.0  # Realistic equity drawdown
    assert len(plan.allocated_schemes) >= 3

    # Test conservative capital preservation (2 years horizon)
    cons_plan = fund_analyzer.generate_portfolio_allocation(
        goal_name="Emergency Capital Preservation",
        horizon_years=2,
        risk_profile="conservative",
    )
    assert cons_plan.recommended_debt_pct >= 60.0
    assert cons_plan.recommended_equity_pct <= 30.0
    assert cons_plan.downside_stress_scenario_drawdown_pct < 10.0
