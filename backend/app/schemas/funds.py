"""AURXON Mutual Fund & ETF Intelligence Schemas.
Pydantic schemas for Indian mutual fund schemes, risk-adjusted returns,
rolling metrics, portfolio overlap, and disciplined factor allocations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FundCategory(str, Enum):
    LARGE_CAP = "LARGE_CAP"
    MID_CAP = "MID_CAP"
    SMALL_CAP = "SMALL_CAP"
    FLEXI_CAP = "FLEXI_CAP"
    INDEX_ETF = "INDEX_ETF"
    LIQUID = "LIQUID"
    ARBITRAGE = "ARBITRAGE"
    SECTORAL = "SECTORAL"


class FundPlan(str, Enum):
    DIRECT = "DIRECT"
    REGULAR = "REGULAR"


class FundOption(str, Enum):
    GROWTH = "GROWTH"
    IDCW = "IDCW"  # Income Distribution cum Capital Withdrawal


class HoldingItem(BaseModel):
    company_name: str
    symbol: str
    weight_pct: float
    sector: str


class FundIdentity(BaseModel):
    scheme_code: str
    scheme_name: str
    amc_name: str
    category: FundCategory
    benchmark_index: str
    plan: FundPlan
    option: FundOption
    expense_ratio_pct: float = Field(ge=0.0, description="Total Expense Ratio (TER) %")
    regular_expense_ratio_pct: Optional[float] = None
    aum_crores: float = Field(ge=0.0, description="Assets Under Management (INR Cr)")
    exit_load: str
    inception_date: str
    is_passive: bool
    tracking_index: Optional[str] = None


class FundRiskReturnMetrics(BaseModel):
    cagr_1y_pct: float
    cagr_3y_pct: float
    cagr_5y_pct: float
    cagr_since_inception_pct: float

    rolling_return_3y_min_pct: float
    rolling_return_3y_median_pct: float
    rolling_return_3y_max_pct: float

    annualized_volatility_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float = Field(description="Sharpe ratio using RBI 10Y G-Sec 6.8% benchmark")
    sortino_ratio: float
    alpha_vs_benchmark_pct: float
    beta_vs_benchmark: float

    tracking_error_pct: Optional[float] = Field(default=None, description="Annualized Tracking Error for ETFs/Index funds")
    tracking_difference_pct: Optional[float] = Field(default=None, description="Trailing 1Y Tracking Difference for ETFs")

    top_10_holdings_pct: float
    top_3_sectors_pct: float
    holdings: List[HoldingItem] = Field(default_factory=list)


class FundComparisonResult(BaseModel):
    schemes: List[FundIdentity]
    metrics: Dict[str, FundRiskReturnMetrics]
    pairwise_overlap_pct: Dict[str, float] = Field(
        default_factory=dict, description="Mutual fund holding overlap matrix (% shared holdings)"
    )
    direct_vs_regular_savings_10y_lakhs: float = Field(
        description="Compound fee difference on ₹10 Lakhs over 10 years"
    )
    comparison_notes: List[str]


class PortfolioAllocationPlan(BaseModel):
    audit_id: str
    goal_name: str
    horizon_years: int
    risk_profile: str
    recommended_equity_pct: float
    recommended_debt_pct: float
    recommended_gold_pct: float
    allocated_schemes: List[Dict[str, Any]]
    downside_stress_scenario_drawdown_pct: float
    key_risks_and_caveats: List[str]
    created_at: str
