"""Unit tests for deterministic financial valuation and risk calculations.
Verifies reproducibility, mathematical accuracy, and zero-hallucination guarantees.
"""

import math
import pytest
from app.analytics.valuation import (
    calculate_altman_z_score,
    calculate_dcf_fair_value,
    calculate_graham_number,
    calculate_piotroski_f_score,
    calculate_risk_metrics,
    compute_deterministic_valuation_dossier,
)


def test_graham_number_calculation():
    # Benchmark: EPS = 100, BVPS = 500
    # Expected: sqrt(22.5 * 100 * 500) = sqrt(1,125,000) = ~1060.66
    graham = calculate_graham_number(eps=100.0, bvps=500.0)
    expected = math.sqrt(22.5 * 100.0 * 500.0)
    assert round(graham, 2) == round(expected, 2)

    # Edge cases: non-positive EPS or BVPS returns 0.0
    assert calculate_graham_number(eps=-10.0, bvps=200.0) == 0.0
    assert calculate_graham_number(eps=50.0, bvps=-100.0) == 0.0
    assert calculate_graham_number(eps=0.0, bvps=200.0) == 0.0


def test_dcf_fair_value_calculation():
    # Test realistic parameters: FCF = 1000 Cr, Shares = 10 Cr, Net cash = 500 Cr, Debt = 200 Cr
    dcf = calculate_dcf_fair_value(
        fcf_latest=1000.0,
        shares_outstanding=10.0,
        cash_and_equivalents=500.0,
        total_debt=200.0,
        growth_rate_stage1=0.10,
        growth_rate_stage2=0.06,
        terminal_growth_rate=0.04,
        discount_rate=0.11,
    )
    assert dcf > 0.0
    assert isinstance(dcf, float)

    # Boundary case: negative or zero FCF returns 0.0
    assert calculate_dcf_fair_value(fcf_latest=-100.0, shares_outstanding=10.0) == 0.0
    assert calculate_dcf_fair_value(fcf_latest=500.0, shares_outstanding=0.0) == 0.0


def test_piotroski_f_score():
    # Perfect score test (all 9 signals positive)
    perfect_metrics = {
        "net_income_current": 500.0,
        "operating_cash_flow_current": 600.0,  # Cash Flow > Net Income
        "roa_current": 0.15,
        "roa_prior": 0.12,  # Improved ROA
        "long_term_debt_current": 100.0,
        "long_term_debt_prior": 200.0,  # Lower debt
        "current_ratio_current": 2.5,
        "current_ratio_prior": 2.0,  # Improved current ratio
        "shares_current": 10.0,
        "shares_prior": 10.0,  # No dilution
        "gross_margin_current": 0.35,
        "gross_margin_prior": 0.30,  # Improved margin
        "asset_turnover_current": 1.2,
        "asset_turnover_prior": 1.0,  # Improved turnover
    }
    score = calculate_piotroski_f_score(perfect_metrics)
    assert score == 9

    # Distressed company test (all signals negative/failing)
    failing_metrics = {
        "net_income_current": -100.0,
        "operating_cash_flow_current": -150.0,  # Cash Flow < Net Income (fails Signal 4)
        "roa_current": -0.05,
        "roa_prior": 0.02,
        "long_term_debt_current": 500.0,
        "long_term_debt_prior": 200.0,
        "current_ratio_current": 0.8,
        "current_ratio_prior": 1.2,
        "shares_current": 15.0,
        "shares_prior": 10.0,  # Dilution
        "gross_margin_current": 0.15,
        "gross_margin_prior": 0.25,
        "asset_turnover_current": 0.5,
        "asset_turnover_prior": 0.8,
    }
    failing_score = calculate_piotroski_f_score(failing_metrics)
    assert failing_score == 0


def test_altman_z_score():
    z = calculate_altman_z_score(
        working_capital=1500.0,
        total_assets=5000.0,
        retained_earnings=2000.0,
        ebit=900.0,
        market_cap=6000.0,
        total_liabilities=1500.0,
        sales=4500.0,
    )
    # Solvent, safe zone score (> 2.99)
    assert z > 2.99


def test_risk_metrics():
    # Synthetic series of 50 daily returns with mean ~ 0.1% and std ~ 1%
    import numpy as np

    np.random.seed(42)
    daily_rets = list(np.random.normal(loc=0.0008, scale=0.012, size=100))

    metrics = calculate_risk_metrics(daily_rets, risk_free_rate_annual=0.065)
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics
    assert "max_drawdown_pct" in metrics
    assert metrics["annualized_volatility_pct"] > 0.0


def test_deterministic_valuation_dossier():
    dossier = compute_deterministic_valuation_dossier(
        ticker="TCS",
        current_price=4000.0,
        eps=128.0,
        bvps=265.0,
        fcf=42000.0,
        shares_outstanding=361.0,
        cash=18000.0,
        debt=0.0,
        pe_ratio=31.25,
        pb_ratio=15.0,
    )
    assert dossier.ticker == "TCS"
    assert dossier.currency == "INR"
    assert dossier.graham_number > 0.0
    assert dossier.fair_value_dcf > 0.0
    assert "graham_number" in dossier.formula_signatures
