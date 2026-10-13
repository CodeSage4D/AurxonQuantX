"""Tests for Tamper-Evident Cryptographic Chained Audit Ledger.
Enforces Workstream F: Security & Audit Integrity.
"""

import sqlite3
from pathlib import Path
import pytest
from app.analytics.valuation import compute_deterministic_valuation_dossier
from app.evidence.ledger import AuditLedger
from app.schemas.research import (
    AdversarialCounterThesis,
    RecommendationEnum,
    ResearchFinding,
    ResearchObjective,
)


@pytest.fixture
def temp_ledger(tmp_path: Path):
    db_file = tmp_path / "test_ledger.sqlite"
    return AuditLedger(db_path=db_file)


def create_sample_finding(ticker: str, audit_id: str) -> ResearchFinding:
    objective = ResearchObjective(
        ticker=ticker,
        query="Test query",
        asset_class="equity",
        horizon="long_term",
        risk_tolerance="moderate",
    )
    val = compute_deterministic_valuation_dossier(
        ticker=ticker,
        current_price=1000.0,
        eps=50.0,
        bvps=200.0,
        fcf=5000.0,
        shares_outstanding=50.0,
        cash=1000.0,
        debt=200.0,
        pe_ratio=20.0,
        pb_ratio=5.0,
    )
    counter = AdversarialCounterThesis(
        bear_case_summary="Test bear case",
        key_vulnerabilities=["Risk 1"],
        downside_risk_factors=["Risk 2"],
        margin_of_safety_adequate=True,
    )
    return ResearchFinding(
        audit_id=audit_id,
        objective=objective,
        valuation=val,
        claims=[],
        counter_thesis=counter,
        synthesis_summary="Test synthesis",
        recommendation=RecommendationEnum.ACCUMULATE,
        uncertainty_level="LOW",
        overall_evidence_score=0.92,
        created_at="2026-10-13T10:00:00Z",
    )


def test_hash_chain_sequential_integrity(temp_ledger):
    f1 = create_sample_finding("RELIANCE", "AUD-1")
    f2 = create_sample_finding("TCS", "AUD-2")
    f3 = create_sample_finding("INFY", "AUD-3")

    h1 = temp_ledger.record_finding(f1)
    h2 = temp_ledger.record_finding(f2)
    h3 = temp_ledger.record_finding(f3)

    records = temp_ledger.list_records(limit=10)
    assert len(records) == 3

    # Verify chain: record 2's prev_hash must equal record 1's chained_hash
    # Records are listed DESC (3, 2, 1)
    rec3, rec2, rec1 = records[0], records[1], records[2]
    assert rec1["prev_hash"] == "0" * 64
    assert rec2["prev_hash"] == rec1["chained_hash"]
    assert rec3["prev_hash"] == rec2["chained_hash"]

    # Verify overall integrity
    is_valid, count, err = temp_ledger.verify_chain_integrity()
    assert is_valid is True
    assert count == 3
    assert err is None


def test_tampering_detection(temp_ledger):
    f1 = create_sample_finding("RELIANCE", "AUD-1")
    f2 = create_sample_finding("TCS", "AUD-2")

    temp_ledger.record_finding(f1)
    temp_ledger.record_finding(f2)

    # Intentionally tamper with record 1 in SQLite
    with sqlite3.connect(temp_ledger.db_path) as conn:
        conn.execute(
            "UPDATE audit_chain SET payload_json = ? WHERE sequence_id = 1",
            ('{"tampered": true}',),
        )
        conn.commit()

    # Integrity verification must detect the tampering
    is_valid, count, err = temp_ledger.verify_chain_integrity()
    assert is_valid is False
    assert "tampered" in err.lower() or "mismatch" in err.lower()
