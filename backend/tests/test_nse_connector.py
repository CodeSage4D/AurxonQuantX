"""Tests for NSE market data connector, provenance metadata, and classification.
Enforces Workstream B: Data Provenance Standards.
"""

from app.market_data.nse_connector import NSEDataConnector
from app.schemas.market import DataClassification, FreshnessStatus


def test_symbol_normalization():
    connector = NSEDataConnector()
    assert connector.normalize_symbol("reliance") == "RELIANCE"
    assert connector.normalize_symbol("RELIANCE.NS") == "RELIANCE"
    assert connector.normalize_symbol("TCS.BO") == "TCS"
    assert connector.normalize_symbol(" infy ") == "INFY"


def test_curated_benchmark_fixture_provenance():
    connector = NSEDataConnector()
    quote = connector.get_market_quote("TCS")
    assert quote.symbol == "TCS.NS"
    assert quote.clean_ticker == "TCS"
    assert quote.exchange == "NSE"
    assert quote.classification == DataClassification.SYNTHETIC_BENCHMARK
    assert quote.freshness == FreshnessStatus.OFFLINE_FROZEN
    assert quote.current_price == 4210.00
    assert quote.currency == "INR"
    assert quote.price_units == "INR per share"
    assert "Benchmark" in quote.data_provider
    assert quote.is_financial_institution is False


def test_financial_institution_detection():
    connector = NSEDataConnector()
    quote = connector.get_market_quote("HDFCBANK")
    assert quote.clean_ticker == "HDFCBANK"
    assert quote.is_financial_institution is True
    assert quote.sector == "Banking & Financial Services"


def test_unknown_ticker_unavailable_state():
    connector = NSEDataConnector(use_cache=False)
    # Query an imaginary unlisted ticker
    quote = connector.get_market_quote("NONEXISTENT_TICKER_XYZ")
    assert quote.classification == DataClassification.UNAVAILABLE
    assert quote.current_price is None
    assert "unavailable" in quote.provenance_notes.lower()
