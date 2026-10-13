"""Tests for AURXON Phase 4: Live Data & Company Research Intelligence Engine.
Covers:
- Company identity resolution and ambiguity detection.
- Enhanced source registry metadata and health probes.
- Market data store persistence and historical bars retrieval.
- Deterministic company quantitative metrics and financial ratios.
- Multi-specialist evidence research report generation.
- Paper trading consideration eligibility tickets and safety gates.
- API REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.analytics.company_quant import company_quant_engine
from app.main import app
from app.market_data.store import market_data_store
from app.research.company_researcher import company_researcher
from app.research.company_resolver import company_resolver
from app.schemas.historical_data import Exchange, HistoricalBar
from app.schemas.market import DataClassification, FreshnessStatus, MarketQuote
from app.sources.enhanced_registry import enhanced_source_registry

client = TestClient(app)


def test_company_resolution_exact_symbols():
    """Verifies resolution of canonical NSE symbols."""
    res_tcs = company_resolver.resolve("TCS")
    assert res_tcs.is_resolved is True
    assert res_tcs.is_ambiguous is False
    assert res_tcs.resolved_company is not None
    assert res_tcs.resolved_company.nse_symbol == "TCS"
    assert res_tcs.resolved_company.isin == "INE467B01029"

    res_rel = company_resolver.resolve("RELIANCE.NS")
    assert res_rel.is_resolved is True
    assert res_rel.resolved_company.nse_symbol == "RELIANCE"


def test_company_resolution_isin_and_historical_names():
    """Verifies resolution via ISIN and historical corporate names."""
    res_isin = company_resolver.resolve("INE002A01018")
    assert res_isin.is_resolved is True
    assert res_isin.resolved_company.nse_symbol == "RELIANCE"

    res_telco = company_resolver.resolve("TELCO")
    assert res_telco.is_resolved is True
    assert res_telco.resolved_company.nse_symbol == "TATAMOTORS"

    res_tisco = company_resolver.resolve("TISCO")
    assert res_tisco.is_resolved is True
    assert res_tisco.resolved_company.nse_symbol == "TATASTEEL"


def test_company_resolution_ambiguity_detection():
    """Verifies that multi-entity conglomerate queries trigger ambiguity flags and clarification prompts."""
    res_tata = company_resolver.resolve("Tata")
    assert res_tata.is_resolved is False
    assert res_tata.is_ambiguous is True
    assert len(res_tata.candidates) >= 3
    assert res_tata.clarification_prompt is not None
    assert "TCS" in res_tata.clarification_prompt

    res_bajaj = company_resolver.resolve("Bajaj")
    assert res_bajaj.is_resolved is False
    assert res_bajaj.is_ambiguous is True
    assert len(res_bajaj.candidates) >= 2


def test_company_resolution_unresolved():
    """Verifies clean non-hallucinatory failure for unknown securities."""
    res = company_resolver.resolve("UNKNOWN_XYZ_CORP_123")
    assert res.is_resolved is False
    assert res.is_ambiguous is False
    assert res.resolved_company is None
    assert "No matching" in res.ambiguity_reason


def test_enhanced_source_registry_metadata():
    """Verifies source registry completeness, licenses, rate limits, and health tracking."""
    sources = enhanced_source_registry.list_sources()
    assert len(sources) >= 6
    source_ids = {s.source_id for s in sources}
    assert "SRC_NSE_BSE" in source_ids
    assert "SRC_AMFI" in source_ids
    assert "SRC_RBI" in source_ids
    assert "SRC_ALPHA_VANTAGE" in source_ids
    assert "SRC_BENCHMARK_ARCHIVE" in source_ids

    # Update fetch status
    enhanced_source_registry.update_fetch_status("SRC_NSE_BSE", success=True, observation_time="2026-10-13T10:00:00Z")
    src = enhanced_source_registry.get_source("SRC_NSE_BSE")
    assert src.health_status.value == "HEALTHY"
    assert src.last_observation_time == "2026-10-13T10:00:00Z"


def test_market_data_store_persistence(tmp_path):
    """Verifies SQLite persistence for quotes, historical bars, and financial statements."""
    quote = MarketQuote(
        symbol="TEST.NS",
        clean_ticker="TEST",
        instrument_name="Test Instruments Limited",
        exchange="NSE",
        data_provider="Test Provider",
        source_reference="https://test.nseindia.com",
        classification=DataClassification.LIVE_VERIFIED,
        freshness=FreshnessStatus.FRESH,
        current_price=500.0,
        retrieval_timestamp="2026-10-13T10:00:00Z",
        pe_ratio=20.0,
    )
    market_data_store.upsert_quote(quote)
    retrieved = market_data_store.get_quote("TEST.NS")
    assert retrieved is not None
    assert retrieved.clean_ticker == "TEST"
    assert retrieved.current_price == 500.0

    # Historical Bars
    bars = [
        HistoricalBar(
            symbol="TEST.NS",
            exchange=Exchange.NSE,
            trading_date="2026-10-01",
            timestamp_iso="2026-10-01T15:30:00+05:30",
            open=490.0,
            high=505.0,
            low=488.0,
            close=500.0,
            volume=100000,
            data_provider="Test Provider",
            retrieval_timestamp_iso="2026-10-13T10:00:00Z",
            classification=DataClassification.HISTORICAL_VERIFIED,
            freshness=FreshnessStatus.STALE_ACCEPTABLE,
        )
    ]
    market_data_store.insert_historical_bars(bars)
    ret_bars = market_data_store.get_historical_bars("TEST.NS")
    assert len(ret_bars) >= 1
    assert ret_bars[0].close == 500.0


def test_company_quant_engine_calculations():
    """Verifies deterministic calculation of returns, volatility, and trend regime."""
    # Synthetic bar series: 25 bars with steady upward trend
    bars = []
    base_price = 100.0
    for i in range(25):
        p = base_price + (i * 2.0)
        bars.append(
            HistoricalBar(
                symbol="SYNTH.NS",
                exchange=Exchange.NSE,
                trading_date=f"2026-09-{i+1:02d}",
                timestamp_iso=f"2026-09-{i+1:02d}T15:30:00+05:30",
                open=p - 1.0,
                high=p + 2.0,
                low=p - 1.5,
                close=p,
                volume=50000,
                data_provider="Synthetic",
                retrieval_timestamp_iso="2026-10-13T10:00:00Z",
                classification=DataClassification.SYNTHETIC,
                freshness=FreshnessStatus.OFFLINE_FROZEN,
            )
        )

    metrics = company_quant_engine.calculate_price_and_trend_metrics(bars)
    assert metrics["returns_1m_pct"] is not None
    assert metrics["returns_1m_pct"] > 0.0
    assert metrics["sma_20"] is not None
    assert metrics["trend_regime"] in ["STRONG_BULLISH", "MILD_BULLISH", "NEUTRAL"]
    assert metrics["avg_daily_volume"] == 50000

    # Fundamental metrics test
    stmts = [
        {"fiscal_period": "FY24-Q3", "period_end_date": "2023-12-31", "revenue_cr": 1000.0, "ebitda_cr": 250.0, "pat_cr": 180.0, "total_debt_cr": 100.0, "net_worth_cr": 1200.0},
        {"fiscal_period": "FY24-Q4", "period_end_date": "2024-03-31", "revenue_cr": 1200.0, "ebitda_cr": 300.0, "pat_cr": 220.0, "total_debt_cr": 90.0, "net_worth_cr": 1400.0},
    ]
    f_metrics = company_quant_engine.calculate_fundamental_metrics(stmts)
    assert f_metrics["ebitda_margin_pct"] == 25.0
    assert f_metrics["revenue_growth_yoy_pct"] == 20.0
    assert f_metrics["debt_to_equity"] == round(90.0 / 1400.0, 2)


def test_company_researcher_full_workflow():
    """Verifies that company research generates a comprehensive report with specialist perspectives and ticket."""
    report = company_researcher.conduct_research("TCS")
    assert report.report_id.startswith("REP-")
    assert report.company.nse_symbol == "TCS"
    assert report.current_price is not None
    assert report.current_price > 0

    # 6 Specialist perspectives verified
    roles = {p.role for p in report.specialist_perspectives}
    assert "Fundamentals" in roles
    assert "Technicals & Trend" in roles
    assert "Valuation & Quality" in roles
    assert "Corporate Actions & Events" in roles
    assert "Downside Risk & Liquidity" in roles
    assert "Adversarial Counter-Thesis" in roles

    # Scenario analysis
    assert report.scenarios.bull_case != ""
    assert report.scenarios.bear_case != ""
    assert report.scenarios.bull_fair_value_est is not None
    assert report.scenarios.bear_fair_value_est is not None

    # Paper trading ticket
    assert report.paper_trading_ticket.ticker == "TCS"
    assert isinstance(report.paper_trading_ticket.is_eligible, bool)
    assert "VALID_ACTIVE_LISTING" in report.paper_trading_ticket.gate_checks_passed
    assert report.paper_trading_ticket.max_recommended_allocation_pct <= 30.0


def test_api_company_endpoints():
    """Verifies HTTP API endpoints for resolution, sources, and research."""
    # Resolve
    resp_res = client.get("/api/v1/company/resolve?q=RELIANCE")
    assert resp_res.status_code == 200
    data_res = resp_res.json()
    assert data_res["is_resolved"] is True
    assert data_res["resolved_company"]["nse_symbol"] == "RELIANCE"

    # Ambiguous resolve
    resp_amb = client.get("/api/v1/company/resolve?q=Tata")
    assert resp_amb.status_code == 200
    data_amb = resp_amb.json()
    assert data_amb["is_resolved"] is False
    assert data_amb["is_ambiguous"] is True

    # Sources
    resp_src = client.get("/api/v1/company/sources")
    assert resp_src.status_code == 200
    data_src = resp_src.json()
    assert len(data_src) >= 6

    # Research
    resp_rep = client.get("/api/v1/company/research/RELIANCE")
    assert resp_rep.status_code == 200
    data_rep = resp_rep.json()
    assert data_rep["company"]["nse_symbol"] == "RELIANCE"
    assert isinstance(data_rep["paper_trading_ticket"]["is_eligible"], bool)
