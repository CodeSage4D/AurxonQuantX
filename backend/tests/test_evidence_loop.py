"""Integration tests for the AURXON Evidence-Loop research workflow,
claim verification, contradiction detection, and immutable audit ledgering.
"""

import pytest
from app.evidence.ledger import audit_ledger
from app.evidence.verifier import EvidenceVerifier
from app.orchestration.evidence_loop import evidence_loop_workflow
from app.schemas.research import (
    EvidenceClaim,
    EvidenceStatus,
    ResearchObjective,
)


@pytest.mark.asyncio
async def test_evidence_loop_streaming_execution():
    objective = ResearchObjective(
        ticker="RELIANCE",
        query="Analyze operating cash flow durability and retail capital expenditure outlook.",
        asset_class="equity",
        horizon="long_term",
        risk_tolerance="moderate",
    )

    events = []
    async for event in evidence_loop_workflow.execute_stream(objective):
        events.append(event)

    # Verify event progression
    assert len(events) >= 6
    assert events[0].step == "OBJECTIVE_PARSING"
    assert events[-1].step == "RESEARCH_COMPLETE"
    assert events[-1].progress_pct == 100

    # Verify final dossier
    final_data = events[-1].data
    assert "finding" in final_data
    assert "content_hash" in final_data
    finding = final_data["finding"]
    assert finding["objective"]["ticker"] == "RELIANCE"
    assert len(finding["claims"]) > 0
    assert finding["valuation"]["current_price"] > 0
    assert finding["recommendation"] in ["ACCUMULATE", "HOLD", "AVOID", "ABSTAIN_DATA_DEFICIENT"]

    # Verify audit ledger retrieval
    audit_id = final_data["audit_id"]
    ledger_record = audit_ledger.get_record_by_id(audit_id)
    assert ledger_record is not None
    assert ledger_record["audit_id"] == audit_id


def test_contradiction_detection():
    # Construct a contradictory claim asserting P/E is 10.0 when market data says 30.0
    contradictory_claim = EvidenceClaim(
        claim_id="CLM-TEST-1",
        claim_text="Company is extremely cheap trading at 10x P/E.",
        source_name="Anonymous Research Blog",
        retrieval_timestamp="2026-10-13T10:00:00Z",
        confidence_score=0.90,
        verification_status=EvidenceStatus.UNVERIFIED,
        supporting_metrics={"pe_ratio": 10.0},
    )

    market_data = {"current_price": 2500.0, "pe_ratio": 30.0}
    verified = EvidenceVerifier.verify_claims([contradictory_claim], market_data)

    assert len(verified) == 1
    assert verified[0].verification_status == EvidenceStatus.CONTRADICTED
    assert "discrepancy" in verified[0].contradiction_notes.lower() or "cites p/e" in verified[0].contradiction_notes.lower()
    assert verified[0].confidence_score < 0.90
