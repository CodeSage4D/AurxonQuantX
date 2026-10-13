"""AURXON IPO Prospectus Intelligence Schemas.
Pydantic data models for Indian DRHP/RHP issue structures, risk factor taxonomies,
peer comparisons, deterministic IPO arithmetic, and 7-point decision verdicts.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class IPORiskCategory(str, Enum):
    LITIGATION_REGULATORY = "LITIGATION_REGULATORY"
    CUSTOMER_CONCENTRATION = "CUSTOMER_CONCENTRATION"
    INDEBTEDNESS = "INDEBTEDNESS"
    OPERATING_HISTORY = "OPERATING_HISTORY"
    SUPPLIER_DEPENDENCY = "SUPPLIER_DEPENDENCY"
    PROMOTER_GOVERNANCE = "PROMOTER_GOVERNANCE"
    MACRO_CURRENCY = "MACRO_CURRENCY"


class IPORiskSeverity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IPOVerdictEnum(str, Enum):
    SUBSCRIBE_LONG_TERM = "SUBSCRIBE_LONG_TERM"
    SUBSCRIBE_LISTING_GAINS_ONLY = "SUBSCRIBE_LISTING_GAINS_ONLY"
    AVOID_OVERVALUED = "AVOID_OVERVALUED"
    AVOID_GOVERNANCE_CONCERN = "AVOID_GOVERNANCE_CONCERN"
    ABSTAIN_DATA_DEFICIENT = "ABSTAIN_DATA_DEFICIENT"


class IssueStructure(BaseModel):
    issuer_name: str
    symbol: Optional[str] = None
    issue_open_date: Optional[str] = None
    issue_close_date: Optional[str] = None
    price_band_floor: float = Field(ge=0.0, description="Floor price in INR")
    price_band_cap: float = Field(ge=0.0, description="Cap price in INR")
    face_value: float = Field(default=10.0, ge=1.0, description="Face value per share in INR")
    lot_size: int = Field(default=1, ge=1, description="Minimum bid lot quantity")

    fresh_issue_crores: float = Field(ge=0.0, description="Fresh capital to the company (INR Cr)")
    offer_for_sale_crores: float = Field(ge=0.0, description="Promoter/PE exit capital (INR Cr)")
    total_issue_crores: float = Field(ge=0.0, description="Total offering size (INR Cr)")

    pre_issue_shares_cr: float = Field(ge=0.0)
    post_issue_shares_cr: float = Field(ge=0.0)
    dilution_percent: float = Field(description="Percentage dilution of equity base")

    promoter_holding_pre_percent: float = Field(ge=0.0, le=100.0)
    promoter_holding_post_percent: float = Field(ge=0.0, le=100.0)

    use_of_proceeds: Dict[str, float] = Field(
        default_factory=dict, description="Allocation breakdown of fresh issue proceeds (INR Cr)"
    )

    reservation_qib_pct: float = Field(default=50.0)
    reservation_nii_pct: float = Field(default=15.0)
    reservation_retail_pct: float = Field(default=35.0)


class DisclosedRiskFactor(BaseModel):
    risk_id: str
    category: IPORiskCategory
    severity: IPORiskSeverity
    title: str
    description: str
    page_reference: Optional[int] = None
    financial_impact_note: str
    is_corroborated_independently: bool = False


class IPOFinancials(BaseModel):
    periods: List[str]  # e.g. ["FY24", "FY25", "FY26"]
    revenue_crores: List[float]
    ebitda_crores: List[float]
    pat_crores: List[float]
    operating_cash_flow_crores: List[float]

    revenue_cagr_3y_pct: float
    ebitda_margin_latest_pct: float
    pat_margin_latest_pct: float
    roe_latest_pct: float
    roce_latest_pct: float
    debt_to_equity: float
    customer_concentration_top5_pct: float


class PeerComparison(BaseModel):
    peer_name: str
    pe_ratio: float
    pb_ratio: float
    roe_pct: float
    revenue_crores: float
    pat_margin_pct: float


class IPOValuationAnalysis(BaseModel):
    market_cap_at_cap_crores: float
    pe_at_floor: float
    pe_at_cap: float
    industry_average_pe: float
    valuation_premium_discount_pct: float
    peers: List[PeerComparison] = Field(default_factory=list)
    scenarios: Dict[str, float] = Field(
        default_factory=dict,
        description="Scenario targets: conservative_fair_value, base_fair_value, aggressive_fair_value",
    )


class IPODossier(BaseModel):
    audit_id: str
    issuer_name: str
    filing_type: str = Field(default="RHP", description="DRHP or RHP")
    structure: IssueStructure
    financials: IPOFinancials
    risks: List[DisclosedRiskFactor]
    valuation: IPOValuationAnalysis

    # 7 Distinct Mandated Conclusions
    business_quality_verdict: str
    financial_quality_verdict: str
    governance_risk_verdict: str
    valuation_verdict: str
    proceeds_utility_verdict: str
    listing_speculation_vs_long_term: str
    key_unresolved_facts: List[str]

    overall_recommendation: IPOVerdictEnum
    evidence_score: float = Field(ge=0.0, le=1.0)
    created_at: str
