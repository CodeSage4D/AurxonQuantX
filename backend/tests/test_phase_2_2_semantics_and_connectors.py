"""AURXON Phase 2.2 Test Suite: Financial Semantics, AMFI Connector,
Document Lineage, and Recommendation Readiness Gates.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.semantics import (
    MetricStatus,
    TypedFinancialMetric,
    FreshnessCategory,
    RecommendationStatus,
    RecommendationReadinessGate,
    ClaimType,
)
from app.schemas.market import DataClassification
from app.ipo.analyzer import compute_ipo_arithmetic, compute_financial_cagr, ipo_analyzer
from app.connectors.amfi_connector import AMFIConnector, amfi_connector


client = TestClient(app)


# ============================================================================
# WORKSTREAM A: FINANCIAL SEMANTICS REGRESSION & EDGE CASES
# ============================================================================

def test_negative_eps_produces_not_applicable():
    """Verify that a loss-making issuer receives typed NOT_APPLICABLE P/E rather than 0.0."""
    res = compute_ipo_arithmetic(
        price_band_floor=100.0,
        price_band_cap=120.0,
        fresh_issue_crores=500.0,
        offer_for_sale_crores=200.0,
        pre_issue_shares_cr=10.0,
        eps=-5.25,
        promoter_holding_pre_pct=75.0,
    )
    assert res["pe_at_floor"] is None
    assert res["pe_at_cap"] is None
    assert res["pe_status"] == MetricStatus.NOT_APPLICABLE
    assert "Loss-making" in res["pe_reason"] or "Negative earnings" in res["pe_reason"]


def test_zero_eps_produces_not_applicable():
    """Verify that zero EPS is not divided by zero, producing NOT_APPLICABLE."""
    res = compute_ipo_arithmetic(
        price_band_floor=50.0,
        price_band_cap=60.0,
        fresh_issue_crores=100.0,
        offer_for_sale_crores=50.0,
        pre_issue_shares_cr=5.0,
        eps=0.0,
        promoter_holding_pre_pct=60.0,
    )
    assert res["pe_at_floor"] is None
    assert res["pe_at_cap"] is None
    assert res["pe_status"] == MetricStatus.NOT_APPLICABLE
    assert "Zero EPS" in res["pe_reason"]


def test_missing_eps_produces_data_unavailable():
    """Verify that absent EPS returns typed DATA_UNAVAILABLE."""
    res = compute_ipo_arithmetic(
        price_band_floor=50.0,
        price_band_cap=60.0,
        fresh_issue_crores=100.0,
        offer_for_sale_crores=50.0,
        pre_issue_shares_cr=5.0,
        eps=None,
        promoter_holding_pre_pct=60.0,
    )
    assert res["pe_at_floor"] is None
    assert res["pe_at_cap"] is None
    assert res["pe_status"] == MetricStatus.DATA_UNAVAILABLE
    assert "unavailable" in res["pe_reason"].lower()


def test_positive_eps_produces_valid_metric():
    """Verify standard profitable issuer arithmetic produces VALID status with positive P/E."""
    res = compute_ipo_arithmetic(
        price_band_floor=66.0,
        price_band_cap=70.0,
        fresh_issue_crores=3560.0,
        offer_for_sale_crores=3000.0,
        pre_issue_shares_cr=775.7,
        eps=2.40,
        promoter_holding_pre_pct=100.0,
    )
    assert res["pe_status"] == MetricStatus.VALID
    assert res["pe_at_cap"] is not None
    assert res["pe_at_cap"] > 0
    assert res["pe_reason"] is None


def test_financial_cagr_semantics():
    """Test CAGR semantics for normal, negative base, and zero period inputs."""
    # Valid 3-year CAGR
    valid_cagr = compute_financial_cagr(100.0, 133.1, 3)
    assert valid_cagr.status == MetricStatus.VALID
    assert valid_cagr.value == 10.0
    assert valid_cagr.reason is None

    # Negative base value (undefined CAGR)
    neg_cagr = compute_financial_cagr(-50.0, 100.0, 3)
    assert neg_cagr.status == MetricStatus.NOT_APPLICABLE
    assert neg_cagr.value is None
    assert "Non-positive base value" in neg_cagr.reason

    # Zero periods
    zero_period_cagr = compute_financial_cagr(100.0, 120.0, 0)
    assert zero_period_cagr.status == MetricStatus.CALCULATION_ERROR
    assert zero_period_cagr.value is None
    assert "Periods must be greater than zero" in zero_period_cagr.reason


# ============================================================================
# WORKSTREAM B & E: AMFI STATUTORY NAV CONNECTOR
# ============================================================================

@pytest.mark.asyncio
async def test_amfi_raw_text_parsing():
    """Verify that pipe-delimited raw statutory AMFI records parse accurately."""
    sample_amfi_data = (
        "Scheme Code;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date\n"
        "122639;INF767K01011;INF767K01029;Parag Parikh Flexi Cap Fund - Direct Plan - Growth;72.8450;10-Oct-2024\n"
        "118989;INF200K01131;;Nippon India ETF Nifty 50 BeES;274.6500;10-Oct-2024\n"
    )
    connector = AMFIConnector()
    records = connector.parse_nav_file(sample_amfi_data)
    assert "122639" in records
    assert records["122639"].nav == 72.845
    assert records["122639"].nav_date == "10-Oct-2024"
    assert "Parag Parikh Flexi Cap Fund" in records["122639"].scheme_name

    assert "118989" in records
    assert records["118989"].nav == 274.65
    assert records["118989"].isin_growth == "INF200K01131"


@pytest.mark.asyncio
async def test_amfi_connector_lookup_and_fallback():
    """Verify AMFI connector resolves known scheme alias and provides verified statutory metadata."""
    record = await amfi_connector.get_nav("PPFAS_FLEXI")
    assert record is not None
    assert record.scheme_code == "122639"
    assert record.nav > 0
    assert record.classification in [DataClassification.HISTORICAL_VERIFIED, DataClassification.CACHED]
    assert record.source_url == "https://www.amfiindia.com/spages/NAVAll.txt"


# ============================================================================
# WORKSTREAM D & F: IPO LINEAGE AND PROSPECTUS AUDITABILITY
# ============================================================================

def test_bajaj_housing_lineage_records():
    """Verify that Bajaj Housing Finance dossier contains source-backed lineage records."""
    dossier = ipo_analyzer.analyze_ipo("BAJAJHFL")
    assert len(dossier.lineage_records) >= 3

    fields = {r.field_name: r for r in dossier.lineage_records}
    assert "fresh_issue_crores" in fields
    assert fields["fresh_issue_crores"].normalized_value == 3560.0
    assert fields["fresh_issue_crores"].page_number == 81
    assert "sebi.gov.in" in fields["fresh_issue_crores"].source_url

    assert "offer_for_sale_crores" in fields
    assert fields["offer_for_sale_crores"].normalized_value == 3000.0


def test_tata_tech_lineage_records():
    """Verify Tata Technologies OFS-only lineage records."""
    dossier = ipo_analyzer.analyze_ipo("TATATECH")
    assert len(dossier.lineage_records) >= 2

    fields = {r.field_name: r for r in dossier.lineage_records}
    assert "offer_for_sale_crores" in fields
    assert fields["offer_for_sale_crores"].normalized_value == 3042.5
    assert fields["offer_for_sale_crores"].page_number == 68


# ============================================================================
# WORKSTREAM G: RECOMMENDATION READINESS GATES
# ============================================================================

def test_recommendation_readiness_gate_structure():
    """Verify that recommendation gate contains distinct multi-dimensional scores."""
    dossier = ipo_analyzer.analyze_ipo("BAJAJHFL")
    gate = dossier.readiness_gate
    assert isinstance(gate, RecommendationReadinessGate)
    assert gate.is_ready is True
    assert gate.status == RecommendationStatus.ACTIVE_UNQUALIFIED

    # Check that analytical dimensions are preserved separately
    expected_dims = ["business_quality", "financial_quality", "governance", "valuation", "evidence_integrity"]
    for dim in expected_dims:
        assert dim in gate.dimension_scores
        assert 0.0 <= gate.dimension_scores[dim] <= 1.0


# ============================================================================
# WORKSTREAM H: API ENDPOINTS FOR LINEAGE, GATES, AND AMFI
# ============================================================================

def test_api_ipo_lineage_endpoint():
    """Test GET /api/v1/ipo/lineage/{symbol}."""
    resp = client.get("/api/v1/ipo/lineage/BAJAJHFL")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert data[0]["issuer"] == "Bajaj Housing Finance Limited"
    assert "source_url" in data[0]
    assert "page_number" in data[0]


def test_api_readiness_gate_endpoint():
    """Test GET /api/v1/gates/readiness/{symbol}."""
    resp = client.get("/api/v1/gates/readiness/TATATECH")
    assert resp.status_code == 200
    gate = resp.json()
    assert gate["is_ready"] is True
    assert "dimension_scores" in gate
    assert "governance" in gate["dimension_scores"]


def test_api_fund_nav_endpoint():
    """Test GET /api/v1/funds/nav/{scheme_code}."""
    resp = client.get("/api/v1/funds/nav/PPFAS_FLEXI")
    assert resp.status_code == 200
    nav_data = resp.json()
    assert nav_data["scheme_code"] == "122639"
    assert nav_data["nav"] > 0
    assert "amfiindia.com" in nav_data["source_url"]


def test_api_fund_nav_404_for_unknown():
    """Test GET /api/v1/funds/nav/UNKNOWN returns 404."""
    resp = client.get("/api/v1/funds/nav/UNKNOWN_SCHEME_XYZ")
    assert resp.status_code == 404
