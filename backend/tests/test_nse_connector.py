"""Tests for NSE market data connector and symbol normalization."""

from app.market_data.nse_connector import NSEDataConnector


def test_symbol_normalization():
    connector = NSEDataConnector()
    assert connector.normalize_symbol("reliance") == "RELIANCE"
    assert connector.normalize_symbol("RELIANCE.NS") == "RELIANCE"
    assert connector.normalize_symbol("TCS.BO") == "TCS"
    assert connector.normalize_symbol(" infy ") == "INFY"


def test_offline_benchmark_fixture_retrieval():
    connector = NSEDataConnector()
    data = connector.get_stock_data("TCS")
    assert data is not None
    assert data["symbol"] == "TCS.NS"
    assert data["current_price"] > 3000.0
    assert data["eps"] > 100.0
    assert data["debt"] == 0.0  # TCS zero debt attribute preserved
