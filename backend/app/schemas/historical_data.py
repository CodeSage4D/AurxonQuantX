"""AURXON Historical Market Data Contract & Schemas.
Establishes the typed contract for historical equity OHLCV data, corporate actions,
adjustment methodologies, and data quality validation for deterministic backtesting.
"""

from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.market import DataClassification, FreshnessStatus


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"


class BarInterval(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    HOURLY = "HOURLY"
    MINUTE_15 = "15M"
    MINUTE_5 = "5M"
    MINUTE_1 = "1M"


class AdjustmentMethod(str, Enum):
    RAW_UNADJUSTED = "RAW_UNADJUSTED"
    SPLIT_BONUS_ADJUSTED = "SPLIT_BONUS_ADJUSTED"
    TOTAL_RETURN_ADJUSTED = "TOTAL_RETURN_ADJUSTED"


class CorporateActionType(str, Enum):
    STOCK_SPLIT = "STOCK_SPLIT"
    BONUS_ISSUE = "BONUS_ISSUE"
    CASH_DIVIDEND = "CASH_DIVIDEND"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    SPIN_OFF = "SPIN_OFF"


class CorporateAction(BaseModel):
    """Statutory corporate action record affecting price and share capitalization."""
    action_type: CorporateActionType
    ex_date: str  # YYYY-MM-DD
    record_date: Optional[str] = None
    ratio_numerator: Optional[float] = Field(
        default=None, description="e.g., 2 for 2:1 bonus or 10 for 10:1 split"
    )
    ratio_denominator: Optional[float] = Field(
        default=None, description="e.g., 1 for 2:1 bonus or 1 for 10:1 split"
    )
    total_share_multiplier: Optional[float] = Field(
        default=None, description="Explicit post-action multiplier (e.g. 2.0 for 1:1 bonus, 10.0 for 10:1 split)"
    )
    dividend_amount_inr: Optional[float] = Field(
        default=None, description="Cash dividend in INR per share"
    )
    description: str
    source_filing: Optional[str] = None

    def get_multiplier(self) -> float:
        """Computes unambiguous share multiplier for split or bonus issue."""
        if self.total_share_multiplier is not None and self.total_share_multiplier > 0:
            return float(self.total_share_multiplier)

        num = self.ratio_numerator or 1.0
        den = self.ratio_denominator or 1.0
        if den <= 0:
            return 1.0

        if self.action_type == CorporateActionType.STOCK_SPLIT:
            return num / den

        if self.action_type == CorporateActionType.BONUS_ISSUE:
            # If specified as 1:1 statutory (1 bonus share for 1 held), multiplier is 2.0
            if num == 1.0 and den == 1.0:
                return 2.0
            # If already provided as post-action ratio 2:1 (doubling)
            if num == 2.0 and den == 1.0 and ("doubling" in self.description.lower() or "1:1" in self.description.lower()):
                return 2.0
            # General statutory formula: (D + N) / D
            return (den + num) / den

        return 1.0


class HistoricalBar(BaseModel):
    """Typed historical bar representing a single trading period."""
    symbol: str
    exchange: Exchange = Exchange.NSE
    trading_date: str  # YYYY-MM-DD
    timestamp_iso: str  # Full ISO-8601 with timezone (Asia/Kolkata or UTC)
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover_crores: Optional[float] = None
    vwap: Optional[float] = None
    is_trading_halt: bool = False
    adjustment_method: AdjustmentMethod = AdjustmentMethod.RAW_UNADJUSTED
    corporate_actions: List[CorporateAction] = Field(default_factory=list)
    source: str = "NSE_BHAVCOPY_ARCHIVE"
    data_classification: DataClassification = DataClassification.HISTORICAL_VERIFIED
    validation_flags: List[str] = Field(default_factory=list)


class DataQualityReport(BaseModel):
    """Validation report verifying data integrity before backtesting."""
    symbol: str
    total_bars: int
    start_date: str
    end_date: str
    is_chronological: bool
    has_duplicates: bool
    duplicate_dates: List[str] = Field(default_factory=list)
    has_ohlc_inconsistencies: bool
    inconsistency_dates: List[str] = Field(default_factory=list)
    missing_calendar_dates: List[str] = Field(default_factory=list)
    anomalous_return_dates: List[str] = Field(default_factory=list)
    data_classification: DataClassification
    is_ready_for_backtest: bool
    rejection_reasons: List[str] = Field(default_factory=list)


class HistoricalSeriesContract(BaseModel):
    """Complete dataset bundle satisfying the historical data contract."""
    symbol: str
    exchange: Exchange = Exchange.NSE
    interval: BarInterval = BarInterval.DAILY
    start_date: str
    end_date: str
    bars: List[HistoricalBar]
    quality_report: DataQualityReport
    provenance_notes: str


def validate_historical_series(
    symbol: str, bars: List[HistoricalBar], max_single_day_return_pct: float = 40.0
) -> DataQualityReport:
    """Strictly validates historical OHLCV bars against integrity rules:
    1. Chronological order (no backward time jumps).
    2. No duplicate trading dates.
    3. OHLC mathematical bounds: High >= max(Open, Close), Low <= min(Open, Close), Low > 0.
    4. Volume non-negativity.
    5. Detection of anomalous price jumps (>40%) without documented corporate action.
    """
    if not bars:
        return DataQualityReport(
            symbol=symbol,
            total_bars=0,
            start_date="N/A",
            end_date="N/A",
            is_chronological=False,
            has_duplicates=False,
            has_ohlc_inconsistencies=False,
            data_classification=DataClassification.UNAVAILABLE,
            is_ready_for_backtest=False,
            rejection_reasons=["Empty historical dataset provided"],
        )

    is_chronological = True
    seen_dates = set()
    duplicate_dates = []
    inconsistency_dates = []
    anomalous_return_dates = []
    rejection_reasons = []

    for i, b in enumerate(bars):
        # 1. Date uniqueness
        if b.trading_date in seen_dates:
            duplicate_dates.append(b.trading_date)
        seen_dates.add(b.trading_date)

        # 2. Chronological sequence
        if i > 0:
            if b.trading_date <= bars[i - 1].trading_date:
                is_chronological = False

            # 5. Anomalous single-day jump without corporate action
            prev_close = bars[i - 1].close
            if prev_close > 0:
                ret_pct = abs((b.close - prev_close) / prev_close) * 100.0
                if ret_pct > max_single_day_return_pct and not b.corporate_actions:
                    anomalous_return_dates.append(
                        f"{b.trading_date} (return: {ret_pct:.1f}% without corporate action)"
                    )

        # 3. OHLC bounds
        if b.low <= 0 or b.open <= 0 or b.high <= 0 or b.close <= 0:
            inconsistency_dates.append(f"{b.trading_date}: Non-positive prices")
        elif b.high < max(b.open, b.close) or b.low > min(b.open, b.close):
            inconsistency_dates.append(f"{b.trading_date}: High/Low violated (H:{b.high}, L:{b.low}, O:{b.open}, C:{b.close})")

        # 4. Volume check
        if b.volume < 0:
            inconsistency_dates.append(f"{b.trading_date}: Negative volume ({b.volume})")

        # 5. Timestamp and Timezone verification
        try:
            parsed_dt = datetime.fromisoformat(b.timestamp_iso)
            if parsed_dt.tzinfo is None:
                inconsistency_dates.append(f"{b.trading_date}: Missing timezone in timestamp '{b.timestamp_iso}'")
        except Exception as e:
            inconsistency_dates.append(f"{b.trading_date}: Malformed ISO timestamp '{b.timestamp_iso}' ({e})")

    if not is_chronological:
        rejection_reasons.append("Historical series is not strictly chronological")
    if duplicate_dates:
        rejection_reasons.append(f"Found {len(duplicate_dates)} duplicate trading dates")
    if inconsistency_dates:
        rejection_reasons.append(f"Found {len(inconsistency_dates)} OHLC structural inconsistencies")

    is_ready = len(rejection_reasons) == 0

    # Aggregate classification
    classifications = {b.data_classification for b in bars}
    if DataClassification.SYNTHETIC in classifications:
        overall_classification = DataClassification.SYNTHETIC
    elif DataClassification.CACHED in classifications:
        overall_classification = DataClassification.CACHED
    else:
        overall_classification = DataClassification.HISTORICAL_VERIFIED

    return DataQualityReport(
        symbol=symbol,
        total_bars=len(bars),
        start_date=bars[0].trading_date,
        end_date=bars[-1].trading_date,
        is_chronological=is_chronological,
        has_duplicates=len(duplicate_dates) > 0,
        duplicate_dates=duplicate_dates,
        has_ohlc_inconsistencies=len(inconsistency_dates) > 0,
        inconsistency_dates=inconsistency_dates,
        anomalous_return_dates=anomalous_return_dates,
        data_classification=overall_classification,
        is_ready_for_backtest=is_ready,
        rejection_reasons=rejection_reasons,
    )
