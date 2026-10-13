"""Tests for AURXON Phase 4.1: Live Provider Verification, Persona Honesty, and Risk Policies.
Covers:
1. Provider probe service execution and sensitive information redaction.
2. GET /api/v1/company/sources/probe endpoint verification.
3. Specialist persona honesty: strict absence of fictional personal names or credentials.
4. Downside risk policy review: maximum drawdown threshold enforced at <= 30.0% and fail-closed logic.
5. Opt-in live provider network test (isolated from standard offline test runs).
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research.company_researcher import CompanyResearcher, company_researcher
from app.research.company_resolver import company_resolver
from app.schemas.market import DataClassification, FreshnessStatus, MarketQuote
from app.sources.provider_probe import provider_probe_service

client = TestClient(app)


def test_provider_probe_service_structure_and_redaction():
    """Verifies that provider probe reports operational states without leaking credentials or secrets."""
    reports = provider_probe_service.probe_all()
    assert len(reports) >= 5

    source_ids = {r.source_id for r in reports}
    assert "SRC_AMFI" in source_ids
    assert "SRC_NSE_BSE" in source_ids
    assert "SRC_RBI" in source_ids
    assert "SRC_YFINANCE_NSE" in source_ids
    assert "SRC_BENCHMARK_ARCHIVE" in source_ids

    # Verify no secret tokens or passwords in string fields
    for r in reports:
        assert r.source_id != ""
        assert r.probe_timestamp != ""
        payload_str = f"{r.quota_and_rate_limits} {r.license_summary} {r.error_reason or ''}".lower()
        assert "password" not in payload_str
        assert "bearer " not in payload_str
        assert "secret" not in payload_str


def test_api_sources_probe_endpoint():
    """Verifies REST API probe endpoint GET /api/v1/company/sources/probe."""
    resp = client.get("/api/v1/company/sources/probe")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    first = data[0]
    assert "source_id" in first
    assert "operational" in first or "is_operational" in first
    assert "license_summary" in first


def test_specialist_persona_honesty_and_credential_removal():
    """Verifies that all fictional analyst personas, human names, and fake credentials are removed."""
    # Run research on standard ticker
    report = company_researcher.conduct_research("TCS")

    forbidden_names = [
        "Raghavan",
        "Arjun",
        "Mehta",
        "Priya",
        "Sengupta",
        "Sunil",
        "Natarajan",
        "Vikram",
        "Sethi",
        "Devika",
        "Rao",
        "Dr.",
        "CFA",
        "CMT",
    ]

    for p in report.specialist_perspectives:
        # Perspective name must be an honest engine/rule/model, not a human persona
        for forbidden in forbidden_names:
            assert forbidden not in p.role, f"Fictional name/title '{forbidden}' found in role '{p.role}'"
            assert forbidden not in p.analyst_name, f"Fictional name/title '{forbidden}' found in analyst_name '{p.analyst_name}'"

    # Counter-thesis must be present and labeled honestly
    counter_perspectives = [p for p in report.specialist_perspectives if "Counter-Thesis" in p.role]
    assert len(counter_perspectives) == 1
    assert "Adversarial" in counter_perspectives[0].role


def test_paper_trading_risk_gate_drawdown_limit_enforcement():
    """Verifies that maximum drawdown ceiling is enforced at 30.0% with explicit rejection reason."""
    # When drawdown is low (e.g. TCS fixture has ~5.9%), ticket is eligible
    report_normal = company_researcher.conduct_research("TCS")
    assert report_normal.paper_trading_ticket.is_eligible is True
    assert report_normal.paper_trading_ticket.max_recommended_allocation_pct <= 30.0

    res = company_resolver.resolve("TCS")
    company = res.resolved_company
    quote = MarketQuote(
        symbol="TCS.NS",
        clean_ticker="TCS",
        instrument_name="Tata Consultancy Services Limited",
        exchange="NSE",
        data_provider="Audited Test",
        source_reference="https://nseindia.com",
        classification=DataClassification.HISTORICAL_VERIFIED,
        freshness=FreshnessStatus.FRESH,
        current_price=3500.0,
        retrieval_timestamp="2026-10-13T10:00:00Z",
    )

    # Inject high drawdown (> 30.0%) and verify fail-closed risk veto
    ticket_high_dd = company_researcher.evaluate_paper_trading_eligibility(
        company=company,
        quote=quote,
        quant_metrics={"max_drawdown_1y_pct": 38.5},
    )
    assert ticket_high_dd.is_eligible is False
    assert any("drawdown" in r.lower() for r in ticket_high_dd.veto_reasons)


def test_paper_trading_risk_gate_fails_closed_on_missing_drawdown():
    """Verifies that missing or uncalculable drawdown causes immediate paper trading ticket veto."""
    res = company_resolver.resolve("TCS")
    company = res.resolved_company
    quote = MarketQuote(
        symbol="TCS.NS",
        clean_ticker="TCS",
        instrument_name="Tata Consultancy Services Limited",
        exchange="NSE",
        data_provider="Audited Test",
        source_reference="https://nseindia.com",
        classification=DataClassification.HISTORICAL_VERIFIED,
        freshness=FreshnessStatus.FRESH,
        current_price=3500.0,
        retrieval_timestamp="2026-10-13T10:00:00Z",
    )

    ticket_missing_dd = company_researcher.evaluate_paper_trading_eligibility(
        company=company,
        quote=quote,
        quant_metrics={"max_drawdown_1y_pct": None},
    )
    assert ticket_missing_dd.is_eligible is False
    assert any("insufficient historical price bars" in r.lower() for r in ticket_missing_dd.veto_reasons)


@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_PROVIDER_TESTS"),
    reason="Opt-in live provider network integration test (requires external network access)",
)
def test_opt_in_live_amfi_and_equity_fetching():
    """Opt-in integration test executed only when RUN_LIVE_PROVIDER_TESTS is set."""
    probe_amfi = provider_probe_service.probe_amfi()
    assert probe_amfi.operational is True
    assert probe_amfi.http_status == 200

    probe_yfin = provider_probe_service.probe_yfinance_nse("RELIANCE.NS")
    assert probe_yfin.operational is True
    assert probe_yfin.records_retrieved > 0
