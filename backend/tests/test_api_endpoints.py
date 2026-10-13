"""End-to-end API integration tests using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["real_trading_enabled"] is False  # Safety control verified
    assert "registered_models" in data


def test_api_market_quote():
    response = client.get("/api/v1/market/quote/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert "market_data" in data
    assert "deterministic_valuation" in data
    val = data["deterministic_valuation"]
    assert val["ticker"] == "RELIANCE"
    assert val["current_price"] > 0
    assert val["graham_number"] > 0
    assert data["market_data"]["classification"] in ["SYNTHETIC_BENCHMARK", "THIRD_PARTY_DELAYED", "LIVE_EXCHANGE"]


def test_api_research_sync():
    req_body = {
        "ticker": "INFY",
        "query": "Evaluate margin defense and digital transformation momentum.",
        "asset_class": "equity",
        "horizon": "medium_term",
        "risk_tolerance": "moderate",
    }
    response = client.post("/api/v1/research/sync", json=req_body)
    assert response.status_code == 200
    finding = response.json()
    assert finding["objective"]["ticker"] == "INFY"
    assert len(finding["claims"]) > 0
    assert finding["recommendation"] in ["ACCUMULATE", "HOLD", "AVOID", "ABSTAIN_DATA_DEFICIENT"]
    assert finding["audit_id"].startswith("AUD-")


def test_api_audit_records():
    response = client.get("/api/v1/audit/records")
    assert response.status_code == 200
    records = response.json()
    assert isinstance(records, list)


def test_api_audit_integrity():
    response = client.get("/api/v1/audit/integrity")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["error"] is None


def test_api_companion_context():
    req_body = {
        "manual_text": "Live screen shows TCS and INFY rallying on order book news.",
        "paused": False,
    }
    response = client.post("/api/v1/companion/context", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTIVE"
    assert "TCS" in data["detected_symbols"]
    assert "INFY" in data["detected_symbols"]
    assert data["user_consent_status"] == "EXPLICIT_USER_CONSENT_REQUIRED"
