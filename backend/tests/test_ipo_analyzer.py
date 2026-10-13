"""Tests for IPO Prospectus Quantitative Analysis Engine.
Enforces Phase 2 Module A: IPO Prospectus Intelligence.
"""

from app.ipo.analyzer import (
    calculate_3y_cagr,
    compute_ipo_arithmetic,
    ipo_analyzer,
)
from app.schemas.ipo import IPOVerdictEnum


def test_ipo_arithmetic_precision():
    # Test case: Fresh Issue ₹3,560 Cr, OFS ₹3,000 Cr, Price Cap ₹70, Pre-issue shares 782.8 Cr, EPS ₹2.22
    arith = compute_ipo_arithmetic(
        price_band_floor=66.0,
        price_band_cap=70.0,
        fresh_issue_crores=3560.0,
        offer_for_sale_crores=3000.0,
        pre_issue_shares_cr=782.8,
        eps=2.22,
        promoter_holding_pre_pct=100.0,
    )

    # Total issue check: 3560 + 3000 = 6560.0
    assert arith["total_issue_crores"] == 6560.0

    # New shares = 3560 / 70 = 50.857 Cr
    expected_new_shares = 3560.0 / 70.0
    assert round(arith["new_shares_cr"], 1) == round(expected_new_shares, 1)

    # Post issue shares = 782.8 + 50.857 = 833.657 Cr
    assert round(arith["post_issue_shares_cr"], 1) == round(782.8 + expected_new_shares, 1)

    # Dilution check = (50.857 / 833.657) * 100 = ~6.1%
    assert 5.5 < arith["dilution_percent"] < 6.5

    # P/E at cap = 70 / 2.22 = ~31.5x
    assert round(arith["pe_at_cap"], 1) == round(70.0 / 2.22, 1)


def test_cagr_calculation():
    # Revenue growing from ₹1000 Cr to ₹1440 Cr in 2 periods (20% CAGR)
    # 1000 * 1.2 * 1.2 = 1440
    cagr = calculate_3y_cagr(initial_val=1000.0, latest_val=1440.0, periods=2)
    assert round(cagr, 1) == 20.0

    # Non-positive edge cases
    assert calculate_3y_cagr(initial_val=0.0, latest_val=100.0) == 0.0
    assert calculate_3y_cagr(initial_val=100.0, latest_val=-50.0) == 0.0


def test_bajaj_housing_finance_ipo_dossier():
    dossier = ipo_analyzer.analyze_ipo("BAJAJ_HOUSING")

    assert dossier.issuer_name == "Bajaj Housing Finance Limited"
    assert dossier.structure.price_band_cap == 70.0
    assert dossier.structure.total_issue_crores == 6560.0
    assert dossier.structure.fresh_issue_crores == 3560.0
    assert dossier.structure.offer_for_sale_crores == 3000.0

    # Verify the 7 mandated conclusions are present and non-empty
    assert len(dossier.business_quality_verdict) > 20
    assert len(dossier.financial_quality_verdict) > 20
    assert len(dossier.governance_risk_verdict) > 20
    assert len(dossier.valuation_verdict) > 20
    assert len(dossier.proceeds_utility_verdict) > 20
    assert len(dossier.listing_speculation_vs_long_term) > 20
    assert len(dossier.key_unresolved_facts) >= 2

    # Verify risks
    assert len(dossier.risks) >= 2
    assert any(r.category.value == "INDEBTEDNESS" for r in dossier.risks)

    # Verify peers
    assert len(dossier.valuation.peers) >= 2

    # Verify recommendation
    assert dossier.overall_recommendation in [
        IPOVerdictEnum.SUBSCRIBE_LONG_TERM,
        IPOVerdictEnum.SUBSCRIBE_LISTING_GAINS_ONLY,
    ]


def test_tata_technologies_ipo_dossier():
    dossier = ipo_analyzer.analyze_ipo("TATA_TECH")

    assert dossier.issuer_name == "Tata Technologies Limited"
    assert dossier.structure.fresh_issue_crores == 0.0  # 100% OFS
    assert dossier.structure.offer_for_sale_crores == 3042.5
    assert dossier.structure.dilution_percent == 0.0  # Zero new shares issued

    # Check anchor client concentration risk
    concentration_risks = [r for r in dossier.risks if r.category.value == "CUSTOMER_CONCENTRATION"]
    assert len(concentration_risks) > 0
    assert "Tata Motors" in concentration_risks[0].title or "Anchor" in concentration_risks[0].title
