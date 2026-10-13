"""AURXON Evidence-Loop Orchestration Engine.
Adaptive 10-step concurrent research workflow with evidence verification,
deterministic analytics, adversarial counter-theses, and audit trail ledgering.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any
import uuid

from app.analytics.valuation import compute_deterministic_valuation_dossier
from app.evidence.ledger import audit_ledger
from app.evidence.verifier import EvidenceVerifier
from app.market_data.nse_connector import NSEDataConnector
from app.model_adapters.registry import model_registry
from app.schemas.research import (
    EvidenceStatus,
    RecommendationEnum,
    ResearchFinding,
    ResearchObjective,
    StreamEvent,
)


class EvidenceLoopWorkflow:
    """Orchestrates the 10-step AURXON Evidence-Loop research lifecycle."""

    def __init__(self):
        self.market_connector = NSEDataConnector()
        self.verifier = EvidenceVerifier()

    async def execute_stream(
        self, objective: ResearchObjective, model_key: str = None
    ) -> AsyncGenerator[StreamEvent, None]:
        audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        adapter = model_registry.get_adapter(model_key)

        # Step 1: Objective Structuring
        yield StreamEvent(
            step="OBJECTIVE_PARSING",
            status="IN_PROGRESS",
            progress_pct=10,
            data={
                "audit_id": audit_id,
                "ticker": objective.ticker,
                "query": objective.query,
                "horizon": objective.horizon,
                "model_in_use": f"{adapter.get_provider_name()}:{adapter.get_model_name()}",
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await asyncio.sleep(0.05)

        # Step 2: Market Data Retrieval
        yield StreamEvent(
            step="MARKET_DATA_RETRIEVAL",
            status="IN_PROGRESS",
            progress_pct=25,
            data={"status": "Fetching verified exchange disclosures & market quotes..."},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        market_data = self.market_connector.get_stock_data(objective.ticker)
        current_price = market_data.get("current_price", 1000.0)

        yield StreamEvent(
            step="MARKET_DATA_RETRIEVAL",
            status="COMPLETED",
            progress_pct=35,
            data={
                "current_price": current_price,
                "symbol": market_data.get("symbol"),
                "short_name": market_data.get("short_name"),
                "source": market_data.get("source"),
                "pe_ratio": market_data.get("pe_ratio"),
                "pb_ratio": market_data.get("pb_ratio"),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await asyncio.sleep(0.05)

        # Step 3: Deterministic Financial Analytics (100% reproducible math)
        yield StreamEvent(
            step="DETERMINISTIC_ANALYTICS",
            status="IN_PROGRESS",
            progress_pct=50,
            data={"status": "Executing Graham, DCF, Piotroski, and Altman Z algorithms..."},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        valuation = compute_deterministic_valuation_dossier(
            ticker=objective.ticker.upper(),
            current_price=current_price,
            eps=market_data.get("eps", 50.0),
            bvps=market_data.get("bvps", 300.0),
            fcf=market_data.get("fcf", 2000.0),
            shares_outstanding=market_data.get("shares_outstanding", 50.0),
            cash=market_data.get("cash", 1000.0),
            debt=market_data.get("debt", 200.0),
            pe_ratio=market_data.get("pe_ratio", 20.0),
            pb_ratio=market_data.get("pb_ratio", 3.0),
            piotroski_metrics=market_data.get("piotroski"),
            dividend_yield_percent=market_data.get("dividend_yield", 1.0),
        )

        yield StreamEvent(
            step="DETERMINISTIC_ANALYTICS",
            status="COMPLETED",
            progress_pct=60,
            data={
                "fair_value_dcf": valuation.fair_value_dcf,
                "dcf_upside_percent": valuation.dcf_upside_percent,
                "graham_number": valuation.graham_number,
                "graham_upside_percent": valuation.graham_upside_percent,
                "piotroski_score": valuation.piotroski_f_score,
                "altman_z_score": valuation.altman_z_score,
                "is_undervalued": valuation.is_undervalued,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await asyncio.sleep(0.05)

        # Step 4: Concurrent Claim Extraction & Evidence Linking
        yield StreamEvent(
            step="CLAIM_EXTRACTION",
            status="IN_PROGRESS",
            progress_pct=70,
            data={"status": "Extracting citation-backed claims from filings & disclosures..."},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        raw_claims = await adapter.extract_evidence_claims(objective, market_data)

        # Step 5: Contradiction & Uncertainty Gating
        verified_claims = self.verifier.verify_claims(raw_claims, market_data)
        evidence_score = self.verifier.compute_overall_evidence_score(verified_claims)

        yield StreamEvent(
            step="EVIDENCE_VERIFICATION",
            status="COMPLETED",
            progress_pct=80,
            data={
                "claims_count": len(verified_claims),
                "evidence_score": evidence_score,
                "claims": [c.model_dump() for c in verified_claims],
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await asyncio.sleep(0.05)

        # Step 6: Adversarial Counter-Thesis (Stress-Testing Bear Case)
        yield StreamEvent(
            step="ADVERSARIAL_ANALYSIS",
            status="IN_PROGRESS",
            progress_pct=85,
            data={"status": "Interrogating downside vulnerabilities and margin of safety..."},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        counter_thesis = await adapter.generate_counter_thesis(objective, market_data, verified_claims)

        # Step 7: Final Synthesis & Recommendation Decision Logic
        synthesis = await adapter.synthesize_finding(objective, market_data, verified_claims, counter_thesis)

        # Gated recommendation logic based on evidence score and valuation
        uncertainty = "LOW" if evidence_score >= 0.85 else ("MODERATE" if evidence_score >= 0.65 else "HIGH")

        if evidence_score < 0.50:
            rec = RecommendationEnum.ABSTAIN_DATA_DEFICIENT
            uncertainty = "UNRESOLVABLE"
        elif valuation.is_undervalued and counter_thesis.margin_of_safety_adequate and valuation.piotroski_f_score >= 5:
            rec = RecommendationEnum.ACCUMULATE
        elif valuation.pe_ratio > 45.0 or valuation.altman_z_score < 1.8:
            rec = RecommendationEnum.AVOID
        else:
            rec = RecommendationEnum.HOLD

        finding = ResearchFinding(
            audit_id=audit_id,
            objective=objective,
            valuation=valuation,
            claims=verified_claims,
            counter_thesis=counter_thesis,
            synthesis_summary=synthesis,
            recommendation=rec,
            uncertainty_level=uncertainty,
            overall_evidence_score=evidence_score,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Step 8: Audit Ledger Recording
        content_hash = audit_ledger.record_finding(finding)

        # Step 9 & 10: Complete Event with Complete Dossier Payload
        yield StreamEvent(
            step="RESEARCH_COMPLETE",
            status="COMPLETED",
            progress_pct=100,
            data={
                "audit_id": audit_id,
                "content_hash": content_hash,
                "finding": finding.model_dump(),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


evidence_loop_workflow = EvidenceLoopWorkflow()
