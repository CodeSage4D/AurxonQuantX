"""Phase 2.1 Independent Validation Gate: IPO Quantitative Reference Tests.
Verifies Workstream B: Independent IPO Mathematics, dilution, CAGR edge cases,
promoter holding bounds, negative earnings, and peer comparison alignment.
"""

import math
import pytest
from app.ipo.analyzer import (
    calculate_3y_cagr,
    compute_ipo_arithmetic,
    CURATED_IPO_BENCHMARKS,
    ipo_analyzer,
)


def test_independent_ipo_fresh_ofs_dilution():
    """Independent ground-truth test of issue size, fresh issue split, and dilution.
    Reference: DRHP Model with 200 Cr Fresh Issue at ₹100 Cap Price and 300 Cr OFS.
    Pre-issue shares = 50 Cr.
    """
    fresh_cr = 200.0
    ofs_cr = 300.0
    cap_price = 100.0
    pre_shares_cr = 50.0

    # Total issue = 200 + 300 = 500 Cr
    total_issue = fresh_cr + ofs_cr
    assert total_issue == 500.0

    # New shares issued = Fresh capital / Cap price = 200 Cr / ₹100 = 2.0 Cr shares
    new_shares = fresh_cr / cap_price
    assert new_shares == 2.0

    # Post-issue shares = 50 + 2 = 52.0 Cr shares
    post_shares = pre_shares_cr + new_shares
    assert post_shares == 52.0

    # Dilution % = (New shares / Post-issue shares) * 100 = (2 / 52) * 100 = 3.846%
    dilution_pct = (new_shares / post_shares) * 100.0
    assert abs(dilution_pct - 3.84615) < 0.01

    arith = compute_ipo_arithmetic(
        price_band_floor=90.0,
        price_band_cap=cap_price,
        fresh_issue_crores=fresh_cr,
        offer_for_sale_crores=ofs_cr,
        pre_issue_shares_cr=pre_shares_cr,
        eps=5.0,
        promoter_holding_pre_pct=80.0,
    )

    assert arith["total_issue_crores"] == total_issue
    assert arith["new_shares_cr"] == new_shares
    assert arith["post_issue_shares_cr"] == post_shares
    assert arith["dilution_percent"] == round(dilution_pct, 2)


def test_promoter_holding_bounds_and_ofs_allocation():
    """Tests promoter stake migration under different OFS participation scenarios.
    Pre-shares = 100 Cr, Promoter owns 70% (70 Cr shares).
    Fresh = 10 Cr shares, OFS = 10 Cr shares. Post-shares = 110 Cr.
    Scenario 1: Promoter sells 100% of OFS (10 Cr shares) -> Post stake = 60/110 = 54.55%
    Scenario 2: Non-promoter PE investors sell 100% of OFS -> Post stake = 70/110 = 63.64%
    """
    pre_shares = 100.0
    promoter_pre_pct = 70.0
    promoter_pre_shares = (promoter_pre_pct / 100.0) * pre_shares  # 70 Cr

    new_shares = 10.0
    ofs_shares = 10.0
    post_shares = pre_shares + new_shares  # 110 Cr

    min_post_pct = ((promoter_pre_shares - ofs_shares) / post_shares) * 100.0  # 54.545%
    max_post_pct = (promoter_pre_shares / post_shares) * 100.0  # 63.636%

    assert round(min_post_pct, 2) == 54.55
    assert round(max_post_pct, 2) == 63.64

    # Any reported post-holding must reside within these mathematically bounded limits
    arith = compute_ipo_arithmetic(
        price_band_floor=95.0,
        price_band_cap=100.0,
        fresh_issue_crores=1000.0,  # 10 Cr shares at ₹100
        offer_for_sale_crores=1000.0,  # 10 Cr shares at ₹100
        pre_issue_shares_cr=100.0,
        eps=4.0,
        promoter_holding_pre_pct=70.0,
    )
    assert min_post_pct <= arith["promoter_holding_post_percent"] <= max_post_pct


def test_cagr_mathematical_limits_and_turnaround_cases():
    """Validates CAGR edge cases: normal growth, zero base, and turnaround from negative base."""
    # Case 1: Standard positive CAGR: 100 to 200 over 3 periods (25.99% CAGR)
    # 100 * (1.25992)^3 = 200
    expected_cagr = round(((200.0 / 100.0) ** (1.0 / 3) - 1.0) * 100.0, 2)
    assert expected_cagr == 25.99
    assert calculate_3y_cagr(100.0, 200.0, 3) == expected_cagr

    # Case 2: Zero base (Division by zero): mathematically undefined
    assert calculate_3y_cagr(0.0, 150.0, 2) == 0.0  # Guarded against ZeroDivisionError

    # Case 3: Negative base (Turnaround from Loss to Profit):
    # E.g., Loss of -₹100 Cr in FY22 to Profit of +₹100 Cr in FY24.
    # CAGR is mathematically undefined (fractional power of negative number).
    # System must guard against complex numbers and not claim a positive CAGR.
    res_negative_base = calculate_3y_cagr(-100.0, 100.0, 2)
    assert res_negative_base == 0.0  # Suppresses complex result; limitation documented


def test_negative_or_zero_eps_valuation_multiples():
    """Ensures valuation handles loss-making issuers without producing invalid or negative multiples."""
    # Loss-making issuer with EPS = -₹5.0
    arith_loss = compute_ipo_arithmetic(
        price_band_floor=50.0,
        price_band_cap=60.0,
        fresh_issue_crores=100.0,
        offer_for_sale_crores=50.0,
        pre_issue_shares_cr=20.0,
        eps=-5.0,
        promoter_holding_pre_pct=60.0,
    )
    # P/E ratio is not meaningful for loss-making firms and must be guarded as 0.0
    assert arith_loss["pe_at_floor"] == 0.0
    assert arith_loss["pe_at_cap"] == 0.0


def test_bajaj_housing_rhp_cross_check():
    """Cross-checks curated Bajaj Housing Finance fixture values against official RHP (Sept 2024).
    Source: Bajaj Housing Finance Limited Red Herring Prospectus, Sept 2024.
    """
    bhfl = CURATED_IPO_BENCHMARKS["BAJAJ_HOUSING"]

    # Face value = ₹10
    assert bhfl["face_value"] == 10.0
    # Price band = ₹66 to ₹70
    assert bhfl["price_band_floor"] == 66.0
    assert bhfl["price_band_cap"] == 70.0
    # Fresh issue = ₹3,560 Cr; OFS = ₹3,000 Cr
    assert bhfl["fresh_issue_crores"] == 3560.0
    assert bhfl["offer_for_sale_crores"] == 3000.0

    # Net proceeds to company = 100% of Fresh Issue (Augmentation of capital base)
    assert "Augment Capital Base" in list(bhfl["use_of_proceeds"].keys())[0]

    # Revenue growth: FY22 ₹3,767 Cr -> FY24 ₹7,617 Cr
    # 2-year CAGR: sqrt(7617 / 3767) - 1 = sqrt(2.0220) - 1 = 42.19%
    cagr = calculate_3y_cagr(bhfl["financials"]["revenue_crores"][0], bhfl["financials"]["revenue_crores"][-1], 2)
    assert abs(cagr - 42.19) < 0.1
