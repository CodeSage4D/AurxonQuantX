"""Phase 2.1 Independent Validation Gate: Mutual Fund & ETF Quantitative Reference Tests.
Verifies Workstream C: CAGR, rolling returns, direct vs regular compounding drag,
tracking error standard deviation, portfolio overlap arithmetic, and benchmark matching.
"""

import math
import pytest
from app.funds.analyzer import (
    calculate_portfolio_overlap,
    calculate_tracking_error,
    compute_cagr,
    compute_direct_plan_savings,
    CURATED_FUND_BENCHMARKS,
    fund_analyzer,
)
from app.schemas.funds import HoldingItem


def test_independent_cagr_reference():
    """Independent mathematical verification of CAGR: (End / Start) ** (1 / years) - 1.
    Reference Case: NAV ₹100 growing to ₹250 over 5 years.
    CAGR = (250 / 100) ** (1 / 5) - 1 = 2.5 ** 0.2 - 1 = 20.11%
    """
    start_nav = 100.0
    end_nav = 250.0
    years = 5.0

    expected_cagr = ((end_nav / start_nav) ** (1.0 / years) - 1.0) * 100.0
    assert round(expected_cagr, 2) == 20.11

    computed = compute_cagr(start_nav, end_nav, years)
    assert abs(computed - 20.11) < 0.01

    # Edge cases
    assert compute_cagr(0.0, 100.0, 5.0) == 0.0
    assert compute_cagr(100.0, 0.0, 5.0) == 0.0
    assert compute_cagr(100.0, 200.0, 0.0) == 0.0


def test_independent_direct_plan_savings_math():
    """Validates the direct plan compounding formula:
    FV_direct = P * (1 + gross - ter_direct) ** t
    FV_regular = P * (1 + gross - ter_regular) ** t
    Savings = FV_direct - FV_regular
    Reference: P = ₹10,00,000, Gross = 12%, Direct TER = 0.65%, Regular TER = 1.45%, t = 10 years.
    Net Direct = 12% - 0.65% = 11.35% = 0.1135
    Net Regular = 12% - 1.45% = 10.55% = 0.1055
    FV_direct = 10,00,000 * (1.1135 ** 10) = 10,00,000 * 2.930432 = 29,30,432
    FV_regular = 10,00,000 * (1.1055 ** 10) = 10,00,000 * 2.726561 = 27,26,561
    Difference = ₹2,03,871 = 2.04 Lakhs
    """
    principal = 1000000.0
    direct_ter = 0.65
    regular_ter = 1.45
    gross = 0.12
    years = 10

    net_d = gross - (direct_ter / 100.0)
    net_r = gross - (regular_ter / 100.0)
    fv_d = principal * ((1.0 + net_d) ** years)
    fv_r = principal * ((1.0 + net_r) ** years)
    expected_savings_lakhs = round((fv_d - fv_r) / 100000.0, 2)

    assert expected_savings_lakhs == 2.04

    result = compute_direct_plan_savings(
        principal_inr=principal,
        direct_ter_pct=direct_ter,
        regular_ter_pct=regular_ter,
        gross_annual_cagr=gross,
        years=years,
    )
    assert abs(result - 2.04) < 0.01


def test_independent_tracking_error_numerical_tolerance():
    """Independent verification of Annualized Tracking Error:
    TE = std(R_etf - R_bench) * sqrt(252) * 100
    Reference: Daily difference series with known sample standard deviation.
    """
    # 12 daily difference observations with known values (decimals)
    diffs = [0.0002, -0.0001, 0.0003, -0.0002, 0.0001, 0.0, -0.0001, 0.0002, -0.0003, 0.0001, 0.0, -0.0002]
    n = len(diffs)
    mean_diff = sum(diffs) / n
    sample_variance = sum((x - mean_diff) ** 2 for x in diffs) / (n - 1)
    sample_std = math.sqrt(sample_variance)
    expected_te = sample_std * math.sqrt(252) * 100.0

    # Build dummy returns: benchmark returns = 0.0, etf returns = diffs
    bench_returns = [0.0] * n
    etf_returns = list(diffs)

    computed_te = calculate_tracking_error(etf_returns, bench_returns)
    assert abs(computed_te - round(expected_te, 2)) < 0.01

    # Insufficient observations check (< 10)
    assert calculate_tracking_error([0.01, 0.02], [0.01, 0.02]) == 0.0


def test_independent_portfolio_overlap_arithmetic():
    """Validates holding overlap % = sum(min(wA, wB)) across 4 test cases."""
    # Case 1: Identical portfolios (100% overlap)
    h_same = [
        HoldingItem(company_name="A", symbol="A", weight_pct=60.0, sector="Sec1"),
        HoldingItem(company_name="B", symbol="B", weight_pct=40.0, sector="Sec2"),
    ]
    assert calculate_portfolio_overlap(h_same, h_same) == 100.0

    # Case 2: Completely disjoint portfolios (0% overlap)
    h_disjoint = [
        HoldingItem(company_name="C", symbol="C", weight_pct=50.0, sector="Sec3"),
        HoldingItem(company_name="D", symbol="D", weight_pct=50.0, sector="Sec4"),
    ]
    assert calculate_portfolio_overlap(h_same, h_disjoint) == 0.0

    # Case 3: Partial overlap with weight asymmetry
    # Portfolio 1: A=30%, B=40%, C=30%
    # Portfolio 2: A=10%, B=50%, D=40%
    # min(A): min(30, 10) = 10%
    # min(B): min(40, 50) = 40%
    # Total Overlap = 10 + 40 = 50.0%
    p1 = [
        HoldingItem(company_name="A", symbol="A", weight_pct=30.0, sector="S1"),
        HoldingItem(company_name="B", symbol="B", weight_pct=40.0, sector="S2"),
        HoldingItem(company_name="C", symbol="C", weight_pct=30.0, sector="S3"),
    ]
    p2 = [
        HoldingItem(company_name="A", symbol="A", weight_pct=10.0, sector="S1"),
        HoldingItem(company_name="B", symbol="B", weight_pct=50.0, sector="S2"),
        HoldingItem(company_name="D", symbol="D", weight_pct=40.0, sector="S4"),
    ]
    assert calculate_portfolio_overlap(p1, p2) == 50.0


def test_etf_benchmark_alignment_non_universal():
    """Confirms that index benchmarks match the specific fund and category,
    and Nifty 50 is not misapplied as a universal benchmark for all funds.
    """
    ppfas = CURATED_FUND_BENCHMARKS["PPFAS_FLEXI"]
    niftybees = CURATED_FUND_BENCHMARKS["NIFTYBEES"]
    mirae = CURATED_FUND_BENCHMARKS["MIRAE_LARGE"]

    # PPFAS Flexi Cap benchmarks against Nifty 500 TRI (broad market)
    assert ppfas["identity"]["benchmark_index"] == "Nifty 500 TRI"

    # NIFTYBEES benchmarks against Nifty 50 TRI (large cap top 50)
    assert niftybees["identity"]["benchmark_index"] == "Nifty 50 TRI"

    # Mirae Asset Large Cap benchmarks against Nifty 100 TRI (large cap 100)
    assert mirae["identity"]["benchmark_index"] == "Nifty 100 TRI"
