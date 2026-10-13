"""AURXON Financial Semantics, Data Freshness & Evidence Lineage Schemas.
Enforces Phase 2.2 Workstream A, B, C, F, and G:
- Typed representations for non-applicable / missing / invalid metrics (no zero sentinels).
- Strict provenance data states.
- Field-level document extraction lineage records.
- Explicit data freshness gates by financial data type.
- Recommendation readiness qualification gates.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    """Explicit status for financial metrics eliminating misleading zero sentinels."""
    VALID = "VALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"  # e.g., P/E for loss-making firms, Altman Z for banks
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"  # Input field was missing from disclosure
    CALCULATION_ERROR = "CALCULATION_ERROR"  # Division by zero, non-positive denominator, math error


class TypedFinancialMetric(BaseModel):
    """Typed financial metric carrying value, unit, validity status, and rationale."""
    value: Optional[float] = None
    status: MetricStatus = MetricStatus.VALID
    reason: Optional[str] = None
    unit: Optional[str] = None

    @classmethod
    def valid(cls, val: float, unit: Optional[str] = None) -> "TypedFinancialMetric":
        return cls(value=round(val, 2), status=MetricStatus.VALID, unit=unit)

    @classmethod
    def not_applicable(cls, reason: str, unit: Optional[str] = None) -> "TypedFinancialMetric":
        return cls(value=None, status=MetricStatus.NOT_APPLICABLE, reason=reason, unit=unit)

    @classmethod
    def unavailable(cls, reason: str = "Data field missing in filing", unit: Optional[str] = None) -> "TypedFinancialMetric":
        return cls(value=None, status=MetricStatus.DATA_UNAVAILABLE, reason=reason, unit=unit)

    @classmethod
    def calculation_error(cls, reason: str, unit: Optional[str] = None) -> "TypedFinancialMetric":
        return cls(value=None, status=MetricStatus.CALCULATION_ERROR, reason=reason, unit=unit)


class ClaimType(str, Enum):
    """Taxonomy of evidence claims distinguishing facts from interpretations."""
    SOURCE_FACT = "SOURCE_FACT"  # Directly quoted from official disclosure/regulatory filing
    CORROBORATED_FACT = "CORROBORATED_FACT"  # Verified by at least two independent primary sources
    DETERMINISTIC_CALCULATION = "DETERMINISTIC_CALCULATION"  # Computed in verified Python math
    ANALYST_INTERPRETATION = "ANALYST_INTERPRETATION"  # Qualitative synthesis of facts
    FORECAST_SCENARIO = "FORECAST_SCENARIO"  # Sensitivity model or projection
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"  # Lacks primary evidence; must be flagged


class FieldLineageRecord(BaseModel):
    """Field-level lineage tracking exact prospectus origin and verification state."""
    field_name: str
    issuer: str
    filing_name: str
    publication_date: str
    source_url: str
    page_number: int
    table_or_section: str
    original_extracted_text: str
    normalized_value: Any
    original_units: str
    normalized_units: str
    extraction_method: str  # "PYPDF_DIGITAL", "REGEX_TABLE", "MANUAL_VERIFIED"
    verification_status: str  # "VERIFIED_PRIMARY", "UNDER_REVIEW", "CORRECTED"
    reviewer_notes: Optional[str] = None


class FreshnessCategory(str, Enum):
    INTRADAY_PRICE = "INTRADAY_PRICE"  # Max 15 mins during trading hours
    END_OF_DAY_PRICE = "END_OF_DAY_PRICE"  # Max 24 hours
    MUTUAL_FUND_NAV = "MUTUAL_FUND_NAV"  # Max 24 hours on business days
    PORTFOLIO_HOLDINGS = "PORTFOLIO_HOLDINGS"  # Max 35 days (Monthly disclosure)
    FINANCIAL_STATEMENTS = "FINANCIAL_STATEMENTS"  # Max 100 days (Quarterly disclosure)
    IPO_PROSPECTUS = "IPO_PROSPECTUS"  # Milestone valid until listing/allotment


class DataFreshnessRecord(BaseModel):
    """Tracks time decay and freshness by financial data type, with legal document versioning."""
    data_type: FreshnessCategory
    observation_date: str
    as_of_timestamp: str
    max_permitted_age_hours: float
    age_hours: float
    is_stale: bool
    stale_warning: Optional[str] = None
    is_versioned_legal_document: bool = False
    filing_version: Optional[str] = None  # e.g., "RHP", "DRHP", "ADDENDUM"
    is_superseded: bool = False


class RecommendationStatus(str, Enum):
    """Transparent qualification states for research conclusions."""
    ACTIVE_UNQUALIFIED = "ACTIVE_UNQUALIFIED"
    QUALIFIED_STALE_DATA = "QUALIFIED_STALE_DATA"
    QUALIFIED_UNVERIFIED_ASSUMPTIONS = "QUALIFIED_UNVERIFIED_ASSUMPTIONS"
    BLOCKED_DATA_INSUFFICIENT = "BLOCKED_DATA_INSUFFICIENT"
    BLOCKED_CONTRADICTORY_EVIDENCE = "BLOCKED_CONTRADICTORY_EVIDENCE"


class RecommendationReadinessGate(BaseModel):
    """Explicit multi-dimensional gate evaluating whether a recommendation may be issued."""
    is_ready: bool
    status: RecommendationStatus
    blocking_reasons: List[str] = Field(default_factory=list)
    qualification_warnings: List[str] = Field(default_factory=list)
    dimension_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Granular dimension assessments: business_quality, financial_quality, governance, valuation, evidence_integrity",
    )
