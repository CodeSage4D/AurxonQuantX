"""AURXON Research Schemas.
Rigorous Pydantic models for structured research objectives, timestamped evidence claims,
deterministic valuation results, adversarial counter-theses, and streaming events.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNCERTAIN = "UNCERTAIN"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"


class RecommendationEnum(str, Enum):
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    AVOID = "AVOID"
    ABSTAIN_DATA_DEFICIENT = "ABSTAIN_DATA_DEFICIENT"


class EvidenceClaim(BaseModel):
    """An individual extracted claim linked immutably to its source evidence."""

    claim_id: str = Field(description="Unique identifier for the claim")
    claim_text: str = Field(description="Specific verifiable statement of fact")
    source_name: str = Field(description="Name of source (e.g. NSE Filings, BSE, Annual Report, Screener)")
    source_url: str = Field(default="", description="Originating URL or document pointer")
    publication_date: Optional[str] = Field(default=None, description="Date the source was published")
    retrieval_timestamp: str = Field(description="ISO 8601 timestamp when evidence was fetched")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Verification confidence score (0 to 1)")
    verification_status: EvidenceStatus = Field(default=EvidenceStatus.UNVERIFIED)
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict, description="Deterministic numeric data backing the claim")
    contradiction_notes: Optional[str] = Field(default=None, description="Detailed notes if any contradiction was detected")


class DeterministicValuation(BaseModel):
    """Deterministically calculated financial valuation metrics (100% reproducible math)."""

    ticker: str
    currency: str = "INR"
    current_price: float = Field(ge=0.0)
    fair_value_dcf: float = Field(ge=0.0, description="Conservative 2-stage DCF fair value")
    dcf_upside_percent: float = Field(description="Upside / downside percentage relative to DCF")
    graham_number: float = Field(ge=0.0, description="Classic Benjamin Graham fair value threshold")
    graham_upside_percent: float = Field(description="Upside / downside percentage relative to Graham Number")
    pe_ratio: float = Field(description="Price to Earnings ratio")
    pb_ratio: float = Field(description="Price to Book ratio")
    piotroski_f_score: int = Field(ge=0, le=9, description="Piotroski 9-point fundamental accounting score")
    altman_z_score: float = Field(description="Altman Z-Score financial distress metric")
    dividend_yield_percent: float = Field(ge=0.0, description="Annual dividend yield percentage")
    is_undervalued: bool = Field(description="Whether price is below conservative margin-of-safety threshold")
    calculation_timestamp: str = Field(description="ISO 8601 calculation timestamp")
    formula_signatures: Dict[str, str] = Field(
        default_factory=dict,
        description="Explicit mathematical formula descriptions used for transparent verification",
    )


class AdversarialCounterThesis(BaseModel):
    """Adversarial stress-testing and bear-case interrogation."""

    bear_case_summary: str = Field(description="Toughest negative thesis for the asset")
    key_vulnerabilities: List[str] = Field(default_factory=list, description="Primary failure modes or execution risks")
    downside_risk_factors: List[str] = Field(default_factory=list, description="Macro or regulatory headwinds")
    margin_of_safety_adequate: bool = Field(description="Whether the margin of safety covers identified downside risks")


class ResearchObjective(BaseModel):
    """Structured founder research request."""

    ticker: str = Field(min_length=1, max_length=20, description="Indian ticker symbol, e.g. RELIANCE, TCS, INFY")
    query: str = Field(min_length=3, description="Specific research question or hypothesis")
    asset_class: str = Field(default="equity", description="Asset class: equity, etf, dividend, ipo, mutual_fund")
    horizon: str = Field(default="long_term", description="Investment horizon: short_term, medium_term, long_term")
    risk_tolerance: str = Field(default="moderate", description="conservative, moderate, aggressive")


class ResearchFinding(BaseModel):
    """Complete, auditable research dossier produced by the AURXON Evidence-Loop."""

    audit_id: str = Field(description="Unique cryptographic audit identifier")
    objective: ResearchObjective
    valuation: DeterministicValuation
    claims: List[EvidenceClaim] = Field(default_factory=list)
    counter_thesis: AdversarialCounterThesis
    synthesis_summary: str = Field(description="Clear, evidence-backed narrative synthesis")
    recommendation: RecommendationEnum
    uncertainty_level: str = Field(description="LOW, MODERATE, HIGH, or UNRESOLVABLE")
    overall_evidence_score: float = Field(ge=0.0, le=1.0, description="Aggregate evidence quality score")
    created_at: str = Field(description="ISO 8601 completion timestamp")


class StreamEvent(BaseModel):
    """Event emitted during live Server-Sent Events (SSE) research streaming."""

    step: str = Field(description="Current pipeline stage name")
    status: str = Field(description="IN_PROGRESS, COMPLETED, WARNING, ERROR")
    progress_pct: int = Field(ge=0, le=100)
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
