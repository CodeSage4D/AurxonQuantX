"""AURXON Portfolio Intelligence, Factor Attribution & Rebalancing Schemas.
Enforces Workstreams A, B, C, D, E for Phase 4.4:
- Portfolio inventory, multi-portfolio accounting, and concentration analysis.
- Performance metrics: TWR, MWR, tracking error, benchmark relative returns.
- Transparent factor attribution: Beta, Momentum, Value, Quality, Volatility, Size.
- Paper-only rebalancing engine: Target allocations, integer lots, transaction drag.
- Stress testing: Hypothetical market, sector, and liquidity stress scenarios.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.market import DataClassification, FreshnessStatus


class PricingStatus(str, Enum):
    """Pricing fidelity and verification state of an individual holding."""
    LIVE_VERIFIED = "LIVE_VERIFIED"
    DELAYED_VERIFIED = "DELAYED_VERIFIED"
    CACHED = "CACHED"
    BENCHMARK_FIXTURE = "BENCHMARK_FIXTURE"
    STALE_PRICED = "STALE_PRICED"
    UNPRICED = "UNPRICED"


class PortfolioHolding(BaseModel):
    """Granular holding record with sector, cost basis, and pricing provenance."""
    symbol: str = Field(description="Trading symbol (e.g. RELIANCE, TCS)")
    instrument_name: str = Field(default="", description="Full company name")
    sector: str = Field(default="Unclassified", description="Industry sector")
    asset_class: str = Field(default="EQUITY", description="EQUITY, CASH, MUTUAL_FUND, etc.")
    quantity: int = Field(ge=0, description="Total units held")
    average_cost: float = Field(ge=0.0, description="Volume-weighted average buy price per unit")
    current_price: Optional[float] = Field(default=None, description="Latest verified market price")
    market_value: Optional[float] = Field(default=None, description="Quantity * current_price")
    cost_basis_total: float = Field(description="Quantity * average_cost")
    unrealized_pnl: Optional[float] = Field(default=None, description="market_value - cost_basis_total")
    unrealized_pnl_pct: Optional[float] = Field(default=None, description="Percentage return on cost")
    realized_pnl: float = Field(default=0.0, description="Cumulative realized gains/losses from sales")
    portfolio_weight_pct: float = Field(default=0.0, description="Weight percentage of total portfolio equity")
    pricing_status: PricingStatus = Field(default=PricingStatus.UNPRICED)
    data_provider: str = Field(default="Unknown", description="Source of current market quote")
    price_timestamp: Optional[str] = Field(default=None, description="ISO timestamp of price quote")


class ConcentrationAnalysis(BaseModel):
    """Exposure concentration across individual holdings, sectors, and asset classes."""
    top_position_symbol: Optional[str] = None
    top_position_weight_pct: float = 0.0
    top_3_positions_weight_pct: float = 0.0
    herfindahl_index: float = Field(
        default=0.0, description="Herfindahl-Hirschman Index (0 to 10,000 scale) measuring concentration"
    )
    sector_weights: Dict[str, float] = Field(default_factory=dict, description="Sector name to weight %")
    asset_class_weights: Dict[str, float] = Field(default_factory=dict, description="Asset class to weight %")
    max_position_weight_limit_pct: float = 30.0
    max_sector_weight_limit_pct: float = 50.0
    has_concentration_breach: bool = False
    breach_details: List[str] = Field(default_factory=list)


class PerformanceMetrics(BaseModel):
    """Audit-grounded portfolio performance and benchmark comparisons."""
    initial_capital: float
    current_equity: float
    total_cash: float
    cash_reserve_pct: float
    absolute_return_inr: float
    total_return_pct: float
    
    # Time-Weighted and Money-Weighted Returns
    time_weighted_return_pct: Optional[float] = Field(
        default=None, description="Time-Weighted Return (TWR) insulating against cash flow timing"
    )
    money_weighted_return_pct: Optional[float] = Field(
        default=None, description="Money-Weighted Return (MWR / IRR) reflecting cash flow timing"
    )
    
    # Volatility and Drawdown
    annualized_volatility_pct: Optional[float] = None
    max_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    peak_equity: float = 0.0
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    risk_free_rate_pct: float = 6.5
    
    # Benchmark-relative (vs NIFTY 50)
    benchmark_symbol: str = "^NSEI"
    benchmark_total_return_pct: Optional[float] = None
    active_return_pct: Optional[float] = None
    tracking_error_pct: Optional[float] = None
    information_ratio: Optional[float] = None
    portfolio_beta: Optional[float] = None
    portfolio_alpha_pct: Optional[float] = None
    
    # Observation metadata
    observation_window_bars: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    methodology_notes: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class FactorTile(BaseModel):
    """Transparent factor exposure with input definition and uncertainty disclosures."""
    factor_name: str
    factor_category: str  # Market Beta, Momentum, Value, Quality, Low Volatility, Size
    portfolio_exposure_score: Optional[float] = None
    benchmark_exposure_score: Optional[float] = None
    tilt_status: str = "NEUTRAL"  # OVERWEIGHT, UNDERWEIGHT, NEUTRAL, UNAVAILABLE
    input_description: str
    sample_size_observations: int
    return_frequency: str = "Daily"
    confidence_level: str = "Descriptive Characteristic"
    data_origin: str = "COMPUTED_HISTORICAL"  # COMPUTED_HISTORICAL, AUDITED_REFERENCE_PROFILE, ILLUSTRATIVE_BASELINE
    is_available: bool = True
    unavailability_reason: Optional[str] = None
    methodology_notes: str
    limitations_disclaimer: str = (
        "Factor exposures represent descriptive cross-sectional characteristics, not causal forward forecasts. "
        "Historical relationships may break down under structural Indian macroeconomic shifts."
    )


class FactorAttributionReport(BaseModel):
    """Collection of validated factor exposures across portfolio assets."""
    portfolio_id: str
    benchmark_symbol: str = "NIFTY50"
    as_of_date: str
    factors: List[FactorTile] = Field(default_factory=list)
    methodology_summary: str = (
        "Bottom-up holdings-weighted factor aggregation calibrated against NIFTY 50 empirical distributions."
    )
    limitations: List[str] = Field(default_factory=list)


class RebalanceConstraints(BaseModel):
    """Configurable boundaries for simulated portfolio rebalancing."""
    max_position_weight_pct: float = Field(default=30.0, description="Hard ceiling for any single security")
    max_sector_weight_pct: float = Field(default=50.0, description="Hard ceiling for any single industry sector")
    target_cash_reserve_pct: float = Field(default=10.0, description="Minimum virtual cash reserve buffer")
    min_trade_size_inr: float = Field(default=1000.0, description="Minimum turnover threshold to avoid micro-churn")
    slippage_bps: float = Field(default=5.0, description="Simulated execution slippage in basis points")
    allow_short_selling: bool = Field(default=False, description="Strictly false: Long-only delivery simulator")


class ProposedTrade(BaseModel):
    """Individual trade instruction generated by the rebalancing engine."""
    symbol: str
    action: str  # BUY or SELL
    current_quantity: int
    target_quantity: int
    share_delta: int  # Absolute units to trade
    estimated_price: float
    estimated_turnover: float
    estimated_transaction_costs: float
    pre_trade_weight_pct: float
    post_trade_weight_pct: float
    reason: str
    pricing_status: PricingStatus
    is_actionable: bool = True
    block_reason: Optional[str] = None


class RebalancingSimulationResult(BaseModel):
    """Complete simulated rebalancing proposal before execution."""
    portfolio_id: str
    simulation_timestamp: str
    status: str  # FEASIBLE, QUALIFIED, BLOCKED
    proposed_trades: List[ProposedTrade] = Field(default_factory=list)
    total_buy_turnover: float = 0.0
    total_sell_turnover: float = 0.0
    total_estimated_turnover: float = 0.0
    total_estimated_transaction_costs: float = 0.0
    current_cash: float
    projected_post_rebalance_cash: float
    projected_cash_reserve_pct: float
    portfolio_turnover_pct: float = 0.0
    pre_rebalance_weights: Dict[str, float] = Field(default_factory=dict)
    post_rebalance_weights: Dict[str, float] = Field(default_factory=dict)
    pre_sector_weights: Dict[str, float] = Field(default_factory=dict)
    post_sector_weights: Dict[str, float] = Field(default_factory=dict)
    constraints_applied: RebalanceConstraints
    qualifications_and_warnings: List[str] = Field(default_factory=list)
    execution_disclaimer: str = (
        "SIMULATION ONLY. No real-money broker orders are routed. Trades are simulated in the virtual paper ledger."
    )


class StressScenarioType(str, Enum):
    BROAD_MARKET_CRASH_10 = "BROAD_MARKET_CRASH_10"
    BROAD_MARKET_CRASH_20 = "BROAD_MARKET_CRASH_20"
    SECTOR_SHOCK_IT_15 = "SECTOR_SHOCK_IT_15"
    SECTOR_SHOCK_FINANCIALS_15 = "SECTOR_SHOCK_FINANCIALS_15"
    SINGLE_STOCK_SHOCK_25 = "SINGLE_STOCK_SHOCK_25"
    VOLATILITY_SURGE_50 = "VOLATILITY_SURGE_50"
    LIQUIDITY_HAIRCUT = "LIQUIDITY_HAIRCUT"
    CUSTOM = "CUSTOM"


class StressScenarioResult(BaseModel):
    """Outcome of a reproducible stress scenario against the active portfolio."""
    scenario_type: StressScenarioType
    scenario_name: str
    description: str
    baseline_equity: float
    stressed_equity: float
    estimated_loss_inr: float
    stressed_loss_pct: float
    stressed_drawdown_pct: float
    var_95_pct: float
    var_99_pct: float
    risk_limit_breaches: List[str] = Field(default_factory=list)
    holding_impacts: Dict[str, float] = Field(default_factory=dict, description="Symbol to estimated loss INR")
    disclaimer: str = (
        "Hypothetical stress scenario simulation. Past historical correlations and beta estimates may diverge "
        "sharply under acute liquidity dry-ups or systemic events. Diversification does not guarantee against losses."
    )


class PortfolioIntelligenceSnapshot(BaseModel):
    """Aggregated portfolio intelligence payload powering the unified workstation view."""
    portfolio_id: str
    portfolio_name: str
    as_of_timestamp: str
    holdings: List[PortfolioHolding]
    concentration: ConcentrationAnalysis
    performance: PerformanceMetrics
    factor_attribution: FactorAttributionReport
    stress_scenarios_summary: List[StressScenarioResult]
    environment_banner: str = "PAPER TRADING ONLY — SIMULATION ENVIRONMENT"
    data_provenance_note: str
