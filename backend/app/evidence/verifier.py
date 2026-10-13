"""AURXON Evidence Verification and Contradiction Detection Engine.
Validates extracted claims against deterministic ground truth and exchange filings.
"""

from typing import Any, Dict, List
from app.schemas.research import EvidenceClaim, EvidenceStatus


class EvidenceVerifier:
    """Independent auditor verifying claims against numerical market facts."""

    @staticmethod
    def verify_claims(claims: List[EvidenceClaim], market_data: Dict[str, Any]) -> List[EvidenceClaim]:
        verified_claims: List[EvidenceClaim] = []
        actual_price = market_data.get("current_price", 0.0)
        actual_pe = market_data.get("pe_ratio", 0.0)

        for claim in claims:
            updated_claim = claim.model_copy()

            # Check for numeric contradictions in supporting metrics
            metrics = claim.supporting_metrics
            if "pe_ratio" in metrics and actual_pe > 0:
                reported_pe = float(metrics["pe_ratio"])
                # Discrepancy > 25% marks contradiction
                if abs(reported_pe - actual_pe) / actual_pe > 0.25:
                    updated_claim.verification_status = EvidenceStatus.CONTRADICTED
                    updated_claim.contradiction_notes = (
                        f"Claim cites P/E of {reported_pe:.1f}x, but actual market data verifies {actual_pe:.1f}x."
                    )
                    updated_claim.confidence_score = max(0.2, updated_claim.confidence_score - 0.4)

            # Check for stale data if publication date is ancient
            if claim.publication_date:
                try:
                    pub_year = int(claim.publication_date.split("-")[0])
                    # If older than 2024, flag as uncertain
                    if pub_year < 2024:
                        if updated_claim.verification_status != EvidenceStatus.CONTRADICTED:
                            updated_claim.verification_status = EvidenceStatus.UNCERTAIN
                            updated_claim.contradiction_notes = f"Source publication date ({claim.publication_date}) is potentially stale (>2 years old)."
                except Exception:
                    pass

            verified_claims.append(updated_claim)

        return verified_claims

    @staticmethod
    def compute_overall_evidence_score(claims: List[EvidenceClaim]) -> float:
        """Computes aggregate evidence score between 0.0 and 1.0."""
        if not claims:
            return 0.0

        score_sum = 0.0
        for claim in claims:
            weight = 1.0
            if claim.verification_status == EvidenceStatus.VERIFIED:
                weight = 1.0
            elif claim.verification_status == EvidenceStatus.UNCERTAIN:
                weight = 0.6
            elif claim.verification_status == EvidenceStatus.UNVERIFIED:
                weight = 0.4
            elif claim.verification_status == EvidenceStatus.CONTRADICTED:
                weight = 0.0

            score_sum += claim.confidence_score * weight

        return round(score_sum / len(claims), 2)
