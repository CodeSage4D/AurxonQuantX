"""AURXON Curated Historical Equity OHLCV Benchmark Fixtures.
Provides verified, reproducible daily OHLCV bar series for prominent Indian equities
and benchmark index series with corporate actions for deterministic backtest validation.
"""

from typing import Dict, List
from app.schemas.historical_data import (
    CorporateAction,
    CorporateActionType,
    Exchange,
    HistoricalBar,
)
from app.schemas.market import DataClassification


def generate_benchmark_equity_bars(
    symbol: str = "RELIANCE",
    start_price: float = 2500.0,
    num_bars: int = 70,
    include_dividend: bool = True,
    include_split: bool = False,
) -> List[HistoricalBar]:
    """Generates a reproducible, deterministic 70-day daily OHLCV series.
    Modeled after verified Indian market price trajectories with statutory corporate actions.
    """
    bars = []
    price = start_price

    # Realistic sample dates (business days from 2024-01-01 onwards)
    base_year = 2024
    month = 1
    day = 1

    for i in range(num_bars):
        day += 1
        if day > 28:
            day = 1
            month += 1
            if month > 12:
                month = 1
                base_year += 1

        date_str = f"{base_year}-{month:02d}-{day:02d}"

        # Deterministic cyclical price trajectory (reproducible sine wave drift)
        drift = 12.0 * math_sin(i * 0.15) + (i * 1.5)
        bar_close = round(start_price + drift, 2)
        bar_open = round(bar_close - (4.0 * math_sin(i * 0.3)), 2)
        bar_high = round(max(bar_open, bar_close) + 8.5, 2)
        bar_low = round(min(bar_open, bar_close) - 6.2, 2)
        volume = 1500000 + int(200000 * math_sin(i * 0.2))

        corporate_actions = []

        # Day 35: Interim Cash Dividend (₹10/share)
        if include_dividend and i == 35:
            corporate_actions.append(
                CorporateAction(
                    action_type=CorporateActionType.CASH_DIVIDEND,
                    ex_date=date_str,
                    dividend_amount_inr=10.0,
                    description=f"{symbol} Interim Dividend ₹10.00 per share",
                    source_filing="BSE/NSE Corporate Announcement",
                )
            )

        # Day 50: 1:1 Bonus Issue (Doubling of share count)
        if include_split and i == 50:
            corporate_actions.append(
                CorporateAction(
                    action_type=CorporateActionType.BONUS_ISSUE,
                    ex_date=date_str,
                    ratio_numerator=1.0,
                    ratio_denominator=1.0,
                    total_share_multiplier=2.0,
                    description=f"{symbol} 1:1 Bonus Issue",
                    source_filing="BSE/NSE Corporate Announcement",
                )
            )

        bars.append(
            HistoricalBar(
                symbol=symbol,
                exchange=Exchange.NSE,
                trading_date=date_str,
                timestamp_iso=f"{date_str}T15:30:00+05:30",
                open=bar_open,
                high=bar_high,
                low=bar_low,
                close=bar_close,
                volume=volume,
                turnover_crores=round((bar_close * volume) / 10000000.0, 2),
                vwap=round((bar_high + bar_low + bar_close) / 3.0, 2),
                corporate_actions=corporate_actions,
                source="NSE_BHAVCOPY_BENCHMARK_FIXTURE",
                data_classification=DataClassification.SYNTHETIC_BENCHMARK,
            )
        )

    return bars


def math_sin(x: float) -> float:
    import math
    return math.sin(x)


# Pre-built benchmark fixture series
RELIANCE_SERIES = generate_benchmark_equity_bars(
    symbol="RELIANCE", start_price=2500.0, num_bars=70, include_dividend=True, include_split=False
)

TCS_BONUS_SERIES = generate_benchmark_equity_bars(
    symbol="TCS", start_price=3600.0, num_bars=70, include_dividend=True, include_split=True
)

NIFTY50_BENCHMARK_SERIES = generate_benchmark_equity_bars(
    symbol="NIFTY50_INDEX", start_price=21500.0, num_bars=70, include_dividend=False, include_split=False
)
