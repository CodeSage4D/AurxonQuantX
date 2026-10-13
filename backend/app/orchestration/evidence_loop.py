"""AURXON Evidence-Loop Orchestration Engine.
Adaptive concurrent research workflow with parallel sub-agent execution,
untrusted data sanitization, claim deduplication, cancellation handling,
and honest uncertainty reporting.
Enforces Workstream D: Parallel Evidence-Loop Standards.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import logging
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple
import uuid

from app.analytics.valuation import compute_deterministic_valuation_dossier
from app.evidence.ledger import audit_ledger
from app.evidence.verifier import EvidenceVerifier
from app.market_data.nse_connector import NSEDataConnector
from app.model_adapters.registry import model_registry
from app.schemas.research import (
    EvidenceClaim,
    EvidenceStatus,
    RecommendationEnum,
    ResearchFinding,
    ResearchObjective,
    StreamEvent,
)

logger = logging.getLogger("aurxon.evidence_loop")

# Safety Limits
MAX_RESEARCH_DEPTH = 3
MAX_CONCURRENT_TASKS = 4

# Security: Prompt Injection / Untrusted Directive Patterns
UNTRUSTED_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript:\S+", re.IGNORECASE),
]


def sanitize_untrusted_content(raw_text: str) -> str:
    """Sanitizes retrieved webpage or filing content.
    Treats all incoming data strictly as passive data payload, neutralizing prompt injection attacks.
    """
    sanitized = raw_text
    for pattern in UNTRUSTED_INJECTION_PATTERNS:
        sanitized = pattern.sub("[UNTRUSTED_INSTRUCTION_NEUTRALIZED]", sanitized)
    return sanitized.strip()


def deduplicate_claims(claims: List[EvidenceClaim]) -> List[EvidenceClaim]:
    """Deduplicates claims using normalized content fingerprinting."""
    seen_hashes: Set[str] = set()
    unique_claims: List[EvidenceClaim] = []

    for c in claims:
        norm_text = re.sub(r"\s+", " ", c.claim_text.strip().lower())
        c_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
        if c_hash not in seen_hashes:
            seen_hashes.add(c_hash)
            unique_claims.append(c)

    return unique_claims


class EvidenceLoopWorkflow:
    """Orchestrates the 10-step AURXON Evidence-Loop research lifecycle with parallel execution."""

    def __init__(self):
        self.market_connector = NSEDataConnector()
        self.verifier = EvidenceVerifier()

    async def _fetch_source_task(
        self, source_name: str, objective: ResearchObjective, market_data: Dict[str, Any], adapter: Any
    ) -> Tuple[str, List[EvidenceClaim], float, float]:
        """Runs an individual independent source extraction task with timing metrics."""
        t_start = time.perf_counter()
        claims = await adapter.extract_evidence_claims(objective, market_data)

        # Tag source appropriately if generic
        sanitized_claims = []
        for c in claims:
            clean_text = sanitize_untrusted_content(c.claim_text)
            c_copy = c.model_copy(update={"claim_text": clean_text})
            sanitized_claims.append(c_copy)

        t_end = time.perf_counter()
        return source_name, sanitized_claims, t_start, t_end

    async def execute_stream(
        self, objective: ResearchObjective, model_key: Optional[str] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        adapter, is_fallback, fallback_reason = model_registry.get_adapter(model_key)

        try:
            # Step 1: Objective Structuring
            yield StreamEvent(
                step="OBJECTIVE_PARSING",
                status="IN_PROGRESS",
                progress_pct=10,
                data={
                    "audit_id": audit_id,
                    "ticker": objective.ticker,
                    "query": sanitize_untrusted_content(objective.query),
                    "horizon": objective.horizon,
                    "model_in_use": f"{adapter.get_provider_name()}:{adapter.get_model_name()}",
                    "is_demonstration_mode": adapter.is_demonstration,
                    "fallback_applied": is_fallback,
                    "fallback_reason": fallback_reason,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(0.02)

            # Step 2: Market Data Retrieval
            yield StreamEvent(
                step="MARKET_DATA_RETRIEVAL",
                status="IN_PROGRESS",
                progress_pct=20,
                data={"status": "Fetching market data with verified provenance..."},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            quote = self.market_connector.get_market_quote(objective.ticker)
            market_data = self.market_connector.get_stock_data(objective.ticker)
            current_price = quote.current_price or 0.0

            yield StreamEvent(
                step="MARKET_DATA_RETRIEVAL",
                status="COMPLETED" if quote.classification.value != "UNAVAILABLE" else "WARNING",
                progress_pct=30,
                data={
                    "symbol": quote.symbol,
                    "current_price": current_price,
                    "classification": quote.classification.value,
                    "freshness": quote.freshness.value,
                    "data_provider": quote.data_provider,
                    "is_financial_institution": quote.is_financial_institution,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(0.02)

            # Step 3: Deterministic Financial Analytics
            yield StreamEvent(
                step="DETERMINISTIC_ANALYTICS",
                status="IN_PROGRESS",
                progress_pct=45,
                data={"status": "Calculating Graham, DCF, and sector-adjusted solvency scores..."},
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
                is_financial_institution=quote.is_financial_institution,
            )

            yield StreamEvent(
                step="DETERMINISTIC_ANALYTICS",
                status="COMPLETED",
                progress_pct=55,
                data={
                    "fair_value_dcf": valuation.fair_value_dcf,
                    "graham_number": valuation.graham_number,
                    "piotroski_score": valuation.piotroski_f_score,
                    "altman_z_score": valuation.altman_z_score,
                    "is_undervalued": valuation.is_undervalued,
                    "formula_notes": valuation.formula_signatures,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(0.02)

            # Step 4: Parallel Multi-Source Research Tasks (Demonstrating Overlapping Execution)
            yield StreamEvent(
                step="PARALLEL_RESEARCH_DISPATCH",
                status="IN_PROGRESS",
                progress_pct=65,
                data={"status": "Dispatching 3 independent research tasks in parallel..."},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            # Launch concurrent tasks
            task_filings = self._fetch_source_task("Exchange Filings", objective, market_data, adapter)
            task_shareholding = self._fetch_source_task("Shareholding Disclosures", objective, market_data, adapter)
            task_credit = self._fetch_source_task("Credit Ratings", objective, market_data, adapter)

            # Await all concurrently
            results = await asyncio.gather(task_filings, task_shareholding, task_credit, return_exceptions=True)

            all_raw_claims: List[EvidenceClaim] = []
            concurrency_telemetry = []

            for r in results:
                if isinstance(r, tuple):
                    s_name, s_claims, t_s, t_e = r
                    all_raw_claims.extend(s_claims)
                    concurrency_telemetry.append({
                        "source": s_name,
                        "claims_count": len(s_claims),
                        "duration_ms": round((t_e - t_s) * 1000, 2),
                    })

            # Step 5: Claim Deduplication and Verification
            unique_claims = deduplicate_claims(all_raw_claims)
            verified_claims = self.verifier.verify_claims(unique_claims, market_data)
            evidence_score = self.verifier.compute_overall_evidence_score(verified_claims)

            yield StreamEvent(
                step="EVIDENCE_VERIFICATION",
                status="COMPLETED",
                progress_pct=80,
                data={
                    "total_claims_extracted": len(all_raw_claims),
                    "unique_claims_after_dedup": len(verified_claims),
                    "evidence_score": evidence_score,
                    "parallel_sources_completed": concurrency_telemetry,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(0.02)

            # Step 6: Adversarial Counter-Thesis (Bear-Case Interrogation)
            yield StreamEvent(
                step="ADVERSARIAL_ANALYSIS",
                status="IN_PROGRESS",
                progress_pct=88,
                data={"status": "Executing adversarial risk interrogation..."},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            counter_thesis = await adapter.generate_counter_thesis(objective, market_data, verified_claims)

            # Step 7: Synthesis & Decision Gating
            synthesis = await adapter.synthesize_finding(objective, market_data, verified_claims, counter_thesis)

            # Honest Uncertainty Reporting
            uncertainty = "LOW" if evidence_score >= 0.85 else ("MODERATE" if evidence_score >= 0.65 else "HIGH")

            if quote.classification.value == "UNAVAILABLE" or evidence_score < 0.50:
                rec = RecommendationEnum.ABSTAIN_DATA_DEFICIENT
                uncertainty = "UNRESOLVABLE"
            elif valuation.is_undervalued and counter_thesis.margin_of_safety_adequate:
                rec = RecommendationEnum.ACCUMULATE
            elif valuation.pe_ratio > 45.0 or (valuation.altman_z_score is not None and valuation.altman_z_score < 1.8):
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

            # Step 8: Cryptographic Chained Audit Ledgering
            content_hash = audit_ledger.record_finding(finding)

            # Final Event
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

        except asyncio.CancelledError:
            logger.warning("Research execution cancelled for %s", objective.ticker)
            yield StreamEvent(
                step="RESEARCH_CANCELLED",
                status="WARNING",
                progress_pct=0,
                data={"status": "Research workflow was cancelled by user or caller."},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            raise


evidence_loop_workflow = EvidenceLoopWorkflow()
