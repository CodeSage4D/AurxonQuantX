"""AURXON Paper Trading Schemas & Lifecycle Contracts.
Defines persistent virtual portfolio entities, order lifecycle states,
risk parameters, and provenance labeling for Phase 3 Stage 2.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.market import DataClassification, FreshnessStatus
from app.trading.costs import InstrumentType, TradeAction, TradeCostBreakdown


class PaperOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PaperOrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class PaperOrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PaperEventType(str, Enum):
    PORTFOLIO_CREATED = "PORTFOLIO_CREATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    CORPORATE_ACTION_APPLIED = "CORPORATE_ACTION_APPLIED"
    KILL_SWITCH_TOGGLED = "KILL_SWITCH_TOGGLED"
    RISK_LIMITS_UPDATED = "RISK_LIMITS_UPDATED"
    PORTFOLIO_RESET = "PORTFOLIO_RESET"


class RiskLimits(BaseModel):
    """Independent risk boundaries enforced before simulated order acceptance."""
    max_order_value_inr: float = Field(
        default=500000.0, description="Maximum single order turnover limit (₹5,00,000)"
    )
    max_position_weight_pct: float = Field(
        default=30.0, description="Maximum portfolio exposure weight in a single instrument (30%)"
    )
    max_daily_loss_inr: float = Field(
        default=50000.0, description="Daily stop-loss limit (₹50,000)"
    )
    kill_switch_active: bool = Field(
        default=False, description="Emergency kill switch blocking all new simulated orders"
    )


class PaperOrderRequest(BaseModel):
    """Simulated order placement request."""
    portfolio_id: str = Field(default="DEFAULT", description="Target paper portfolio identifier")
    symbol: str = Field(description="Trading symbol (e.g. RELIANCE, TCS)")
    side: PaperOrderSide = Field(description="BUY or SELL")
    quantity: int = Field(gt=0, description="Number of shares/units to trade")
    order_type: PaperOrderType = Field(default=PaperOrderType.MARKET, description="MARKET or LIMIT")
    limit_price: Optional[float] = Field(default=None, description="Price threshold for LIMIT orders")
    idempotency_key: Optional[str] = Field(
        default=None, description="Unique client key preventing duplicate order processing"
    )
    instrument_type: InstrumentType = Field(
        default=InstrumentType.EQUITY_DELIVERY, description="Statutory instrument classification"
    )


class PaperOrderRecord(BaseModel):
    """Immutable audit record of a paper order throughout its lifecycle."""
    order_id: str
    idempotency_key: Optional[str] = None
    portfolio_id: str
    symbol: str
    side: PaperOrderSide
    order_type: PaperOrderType
    quantity: int
    limit_price: Optional[float] = None
    status: PaperOrderStatus
    submitted_at: str
    filled_at: Optional[str] = None
    fill_price: Optional[float] = None
    executed_quantity: int = 0
    turnover: float = 0.0
    transaction_costs: float = 0.0
    cost_breakdown: Optional[Dict[str, float]] = None
    rejection_reason: Optional[str] = None
    data_provenance: str = "UNAVAILABLE"
    data_classification: DataClassification = DataClassification.UNVERIFIED
    freshness_status: FreshnessStatus = FreshnessStatus.UNKNOWN
    is_demonstration: bool = True
    notes: str = ""


class PaperPositionRecord(BaseModel):
    """Aggregated instrument position within a virtual portfolio."""
    symbol: str
    quantity: int = 0
    average_cost: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    realized_pnl: float = 0.0
    portfolio_weight_pct: float = 0.0
    last_updated_at: str


class PaperPortfolioState(BaseModel):
    """Complete snapshot of a persistent paper trading portfolio."""
    portfolio_id: str
    name: str
    initial_cash: float
    current_cash: float
    positions_value: float
    total_equity: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    total_transaction_costs_paid: float
    kill_switch_active: bool
    risk_limits: RiskLimits
    is_paper_trading: bool = True
    environment_banner: str = "PAPER TRADING ONLY — SIMULATION ENVIRONMENT"
    data_provenance_note: str = (
        "Strictly simulated virtual ledger. No broker order routing or real-money capital. "
        "Fills are computed against validated market data or benchmark fixtures."
    )
    positions: Dict[str, PaperPositionRecord] = Field(default_factory=dict)
    open_orders_count: int = 0
    total_orders_count: int = 0
    created_at: str
    updated_at: str


class KillSwitchRequest(BaseModel):
    portfolio_id: str = "DEFAULT"
    active: bool = True
    reason: str = "Emergency kill switch toggled by operator"


class CancelOrderRequest(BaseModel):
    portfolio_id: str = "DEFAULT"
    order_id: str


class PaperCorporateActionRequest(BaseModel):
    portfolio_id: str = "DEFAULT"
    symbol: str
    action_type: str  # CASH_DIVIDEND, STOCK_SPLIT, BONUS_ISSUE
    dividend_amount_inr: Optional[float] = None
    split_ratio: Optional[float] = None
    description: str = "Manual simulated corporate action event"
