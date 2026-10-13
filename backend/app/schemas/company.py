"""AURXON Company Identity, Source Metadata, and Research Dossier Schemas.
Enforces rigorous resolution, source lineage, disambiguation, and structured research reporting.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.market import DataClassification, FreshnessStatus


class ListingStatus(str, Enum):
    ACTIVE_LISTED = "ACTIVE_LISTED"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"
    UNLISTED = "UNLISTED"


class SecurityType(str, Enum):
    EQUITY_SHARES = "EQUITY_SHARES"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    DEBENTURE = "DEBENTURE"
    REIT_INVIT = "REIT_INVIT"


class CompanyIdentity(BaseModel):
    """Authoritative canonical corporate and listed security identity."""
    cin: Optional[str] = Field(default=None, description="Corporate Identification Number (MCA)")
    isin: Optional[str] = Field(default=None, description="International Securities Identification Number")
    legal_name: str = Field(description="Full official statutory company name")
    trade_name: str = Field(description="Recognized corporate or brand trade name")
    nse_symbol: Optional[str] = Field(default=None, description="Primary NSE symbol without exchange suffix")
    bse_code: Optional[str] = Field(default=None, description="BSE Scrip Code (e.g. 500325)")
    primary_exchange: str = Field(default="NSE", description="Primary trading venue (NSE or BSE)")
    listing_status: ListingStatus = Field(default=ListingStatus.ACTIVE_LISTED)
    security_type: SecurityType = Field(default=SecurityType.EQUITY_SHARES)
    sector: str = Field(default="Conglomerate")
    industry: str = Field(default="Diversified")
    aliases: List[str] = Field(default_factory=list, description="Common aliases, ticker shortforms, brand names")
    historical_names: List[str] = Field(default_factory=list, description="Verifiable historical names or past symbols")
    website_ir: Optional[str] = Field(default=None, description="Official Investor Relations portal")
    is_financial_institution: bool = Field(default=False, description="True for Banks, NBFCs, Insurance")


class CompanyResolutionResult(BaseModel):
    """Result of resolving a company query against canonical security master."""
    query: str
    is_resolved: bool
    is_ambiguous: bool
    resolved_company: Optional[CompanyIdentity] = None
    candidates: List[CompanyIdentity] = Field(default_factory=list)
    ambiguity_reason: Optional[str] = None
    clarification_prompt: Optional[str] = None


class SourceHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    OFFLINE_ONLY = "OFFLINE_ONLY"
    UNCONFIGURED = "UNCONFIGURED"


class EnhancedSourceMetadata(BaseModel):
    """Comprehensive source registry record meeting Stage 1 specifications."""
    source_id: str
    name: str
    category: str
    supported_asset_classes: List[str]
    supported_symbols_or_scope: str
    data_fields: List[str]
    history_depth: str
    geographic_coverage: str = "India (IN)"
    update_frequency: str
    rate_limits: str
    authentication_required: bool
    license_status: str
    permitted_usage_notes: str
    last_successful_fetch: Optional[str] = None
    last_observation_time: Optional[str] = None
    health_status: SourceHealthStatus = SourceHealthStatus.HEALTHY
    known_limitations: List[str] = Field(default_factory=list)
    fallback_policy: str


class SpecialistPerspective(BaseModel):
    """Structured assessment from an independent research specialist."""
    role: str  # Fundamentals, Technicals, Valuation, Corporate Actions, Risk, Adversarial
    analyst_name: str
    sentiment: str  # BULLISH, NEUTRAL, BEARISH, CAUTIONARY
    confidence_score: float = Field(ge=0.0, le=1.0)
    key_findings: List[str]
    supporting_citations: List[str]
    missing_data_warnings: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)


class ScenarioAnalysis(BaseModel):
    """Bull, Base, and Bear scenarios with explicit assumptions and price ranges."""
    bull_case: str
    bull_fair_value_est: Optional[float] = None
    bull_catalysts: List[str]
    
    base_case: str
    base_fair_value_est: Optional[float] = None
    base_assumptions: List[str]
    
    bear_case: str
    bear_fair_value_est: Optional[float] = None
    bear_risks: List[str]
    
    downside_protection_buffer_pct: Optional[float] = None


class PaperTradingEligibilityTicket(BaseModel):
    """Strict gate for paper trading consideration after research passes data and risk checks."""
    is_eligible: bool
    ticker: str
    exchange: str = "NSE"
    as_of_price: Optional[float] = None
    price_freshness: FreshnessStatus
    data_classification: DataClassification
    gate_checks_passed: List[str]
    veto_reasons: List[str] = Field(default_factory=list)
    max_recommended_allocation_pct: float = Field(default=0.0, le=30.0)
    audit_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComprehensiveCompanyResearchReport(BaseModel):
    """Source-linked, uncertainty-aware company research dossier."""
    report_id: str
    company: CompanyIdentity
    as_of_timestamp: str
    retrieval_timestamp: str
    data_freshness: FreshnessStatus
    data_classification: DataClassification
    data_provider: str = "AURXON_BENCHMARK_ARCHIVE"
    historical_bars_count: Optional[int] = None
    historical_date_range: Optional[str] = None
    calculation_methodology: str = "Deterministic Pure-Python Analytics (No look-ahead bias)"
    
    # Financial snapshot
    current_price: Optional[float] = None
    market_cap_cr: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    eps_ttm: Optional[float] = None
    book_value_per_share: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe_pct: Optional[float] = None
    roce_pct: Optional[float] = None
    fcf_cr: Optional[float] = None
    
    # Trend and quantitative indicators
    returns_1m_pct: Optional[float] = None
    returns_6m_pct: Optional[float] = None
    returns_1y_pct: Optional[float] = None
    volatility_annualized_pct: Optional[float] = None
    max_drawdown_1y_pct: Optional[float] = None
    relative_strength_vs_nifty: Optional[str] = None
    trend_regime: str = "NEUTRAL"
    
    # Evidence & Specialist perspectives
    specialist_perspectives: List[SpecialistPerspective]
    scenarios: ScenarioAnalysis
    key_catalysts: List[str]
    downside_risks: List[str]
    adversarial_counterarguments: List[str]
    data_uncertainties_and_gaps: List[str]
    
    # Verification & Citations
    source_citations: List[Dict[str, str]]
    paper_trading_ticket: PaperTradingEligibilityTicket
    provenance_disclaimer: str
