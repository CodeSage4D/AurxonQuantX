"""AURXON Mock Research Adapter.
Provides deterministic, citation-backed, offline research generation for testing,
development, and offline operations without requiring external API keys.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid

from app.model_adapters.base import BaseModelAdapter
from app.schemas.research import (
    AdversarialCounterThesis,
    EvidenceClaim,
    EvidenceStatus,
    ResearchObjective,
)


class MockResearchAdapter(BaseModelAdapter):
    """Deterministic, citation-backed adapter for reliable testing and offline development."""

    def get_provider_name(self) -> str:
        return "aurxon_offline"

    def get_model_name(self) -> str:
        return "heuristic_evidence_v1"

    def is_available(self) -> bool:
        return True

    @property
    def is_demonstration(self) -> bool:
        return True

    async def extract_evidence_claims(
        self, objective: ResearchObjective, market_data: Dict[str, Any]
    ) -> List[EvidenceClaim]:
        now_iso = datetime.now(timezone.utc).isoformat()
        ticker = objective.ticker.upper()
        price = market_data.get("current_price", 1000.0)
        eps = market_data.get("eps", 50.0)
        pe = market_data.get("pe_ratio", 20.0)
        fcf = market_data.get("fcf", 5000.0)
        debt = market_data.get("debt", 0.0)
        sector = market_data.get("sector", "Equities")

        claims = [
            EvidenceClaim(
                claim_id=f"CLM-{uuid.uuid4().hex[:8].upper()}",
                claim_text=f"{ticker} trades at ₹{price:.2f} with trailing twelve-month EPS of ₹{eps:.2f} (P/E {pe:.1f}x) in the {sector} sector.",
                source_name="NSE / BSE Exchange Disclosure",
                source_url=f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}",
                publication_date="2026-06-30",
                retrieval_timestamp=now_iso,
                confidence_score=0.98,
                verification_status=EvidenceStatus.VERIFIED,
                supporting_metrics={"price": price, "eps": eps, "pe_ratio": pe},
            ),
            EvidenceClaim(
                claim_id=f"CLM-{uuid.uuid4().hex[:8].upper()}",
                claim_text=f"Reported Free Cash Flow stands at approximately ₹{fcf:,.1f} Cr against total recorded balance-sheet debt of ₹{debt:,.1f} Cr.",
                source_name=f"{ticker} Q1 FY27 Audited Financial Results",
                source_url=f"https://www.bseindia.com/corporates/results.aspx?Code={ticker}",
                publication_date="2026-07-15",
                retrieval_timestamp=now_iso,
                confidence_score=0.94,
                verification_status=EvidenceStatus.VERIFIED,
                supporting_metrics={"fcf_cr": fcf, "debt_cr": debt},
            ),
            EvidenceClaim(
                claim_id=f"CLM-{uuid.uuid4().hex[:8].upper()}",
                claim_text="Domestic Institutional Investors (DII) and Mutual Funds increased aggregate stake by 42 bps over the trailing two quarters.",
                source_name="Shareholding Pattern Disclosure (Regulation 31 LODR)",
                source_url="https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern",
                publication_date="2026-07-08",
                retrieval_timestamp=now_iso,
                confidence_score=0.91,
                verification_status=EvidenceStatus.VERIFIED,
                supporting_metrics={"dii_change_bps": 42},
            ),
        ]

        # Add a conditional risk/uncertainty claim if debt is high
        if debt > 50000.0:
            claims.append(
                EvidenceClaim(
                    claim_id=f"CLM-{uuid.uuid4().hex[:8].upper()}",
                    claim_text=f"Capital expenditure cycle carries substantial debt load (₹{debt:,.1f} Cr), demanding close interest coverage monitoring in elevated interest rate regimes.",
                    source_name="Credit Rating Agency Rating Rationale (CRISIL/ICRA)",
                    source_url="https://www.crisil.com/ratings",
                    publication_date="2026-05-18",
                    retrieval_timestamp=now_iso,
                    confidence_score=0.88,
                    verification_status=EvidenceStatus.UNCERTAIN,
                    contradiction_notes="Debt amortisation schedule depends on continuous operating cash flow growth.",
                )
            )

        return claims

    async def generate_counter_thesis(
        self, objective: ResearchObjective, market_data: Dict[str, Any], claims: List[EvidenceClaim]
    ) -> AdversarialCounterThesis:
        ticker = objective.ticker.upper()
        pe = market_data.get("pe_ratio", 20.0)
        debt = market_data.get("debt", 0.0)

        vulnerabilities = [
            f"Valuation sensitivity: Multiple contraction if earnings growth decelerates below {pe * 0.4:.1f}% CAGR.",
            "Raw material price volatility and input cost inflation impacting operating EBITDA margins.",
            "Competitive entry in domestic Indian retail/digital and overseas markets.",
        ]

        if debt > 30000.0:
            vulnerabilities.append(f"Leverage overhang: High debt of ₹{debt:,.1f} Cr limits flexibility during credit tightening.")

        return AdversarialCounterThesis(
            bear_case_summary=f"Bear case for {ticker}: Growth deceleration and multiple compression risk if margin expansion stalls or regulatory oversight tightens.",
            key_vulnerabilities=vulnerabilities,
            downside_risk_factors=[
                "RBI interest rate policy shifts and systemic liquidity constraints.",
                "Global macro slowdown affecting export-dependent and cyclical revenue streams.",
                "Execution delays in planned capital expenditure expansions.",
            ],
            margin_of_safety_adequate=(pe < 35.0),
        )

    async def synthesize_finding(
        self,
        objective: ResearchObjective,
        market_data: Dict[str, Any],
        claims: List[EvidenceClaim],
        counter_thesis: AdversarialCounterThesis,
    ) -> str:
        ticker = objective.ticker.upper()
        price = market_data.get("current_price", 1000.0)
        verified_count = sum(1 for c in claims if c.verification_status == EvidenceStatus.VERIFIED)

        return (
            f"Comprehensive analysis of {ticker} at ₹{price:.2f} confirms solid fundamental backing "
            f"with {verified_count} independently verified exchange disclosures. "
            f"Primary investment thesis: Robust domestic operating cash flows provide capital expenditure buffer. "
            f"Adversarial risk check: {counter_thesis.bear_case_summary}"
        )
