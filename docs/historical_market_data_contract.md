# AURXON Historical Market Data Contract
**Project:** AURXONQuant  
**Milestone:** Phase 3, Stage 1 — Deterministic Backtesting Engine  
**Status:** ENFORCED & AUDITED  
**Date:** 2026-10-13  

---

## 1. Scope & Core Principle

The historical market data contract governs the ingestion, validation, and serialization of equity and ETF price series used for quantitative backtesting.

**Crucial Mandate:** Mutual fund daily NAV feeds (such as the AMFI statutory feed) do not supply intraday or daily equity OHLCV data. Equity series require distinct statutory exchange contracts (Bhavcopy, corporate announcements, exchange trade records) and cannot be conflated with NAV series.

---

## 2. Typed Schema Specification

### 2.1 HistoricalBar

```python
class HistoricalBar(BaseModel):
    symbol: str                                    # Normalized ticker (e.g. RELIANCE, TCS)
    exchange: Exchange = Exchange.NSE              # Primary Indian exchange (NSE, BSE)
    trading_date: str                              # Calendar trading date (YYYY-MM-DD)
    timestamp_iso: str                             # Full ISO-8601 with timezone (+05:30)
    open: float                                    # Official market open price in INR
    high: float                                    # Highest price traded in the bar
    low: float                                     # Lowest price traded in the bar
    close: float                                   # Official closing / settlement price
    volume: int                                    # Total executed share volume
    turnover_crores: Optional[float] = None        # Turnover in INR Crores
    vwap: Optional[float] = None                   # Volume-weighted average price
    is_trading_halt: bool = False                  # Circuit filter / trading suspension flag
    adjustment_method: AdjustmentMethod            # RAW_UNADJUSTED, SPLIT_BONUS_ADJUSTED
    corporate_actions: List[CorporateAction]       # Corporate actions effective on this date
    source: str                                    # "NSE_BHAVCOPY_ARCHIVE", "BENCHMARK_FIXTURE"
    data_classification: DataClassification        # HISTORICAL_VERIFIED, CACHED, SYNTHETIC
    validation_flags: List[str]                    # Diagnostic validation notes
```

### 2.2 CorporateAction

```python
class CorporateAction(BaseModel):
    action_type: CorporateActionType               # STOCK_SPLIT, BONUS_ISSUE, CASH_DIVIDEND, etc.
    ex_date: str                                   # Ex-Date on which adjustments take effect
    record_date: Optional[str] = None              # Regulatory record date
    ratio_numerator: Optional[float] = None        # e.g., 2.0 for 2:1 bonus or 10.0 for 10:1 split
    ratio_denominator: Optional[float] = None      # e.g., 1.0
    dividend_amount_inr: Optional[float] = None    # Dividend per share in INR
    description: str                               # Official corporate announcement text
    source_filing: Optional[str] = None            # Exchange circular or corporate filing URL
```

---

## 3. Data Integrity & Validation Rules

Before any bar series can enter the event-driven backtesting engine, it must pass `validate_historical_series()`:

1. **Strict Chronology:** Bar dates must be strictly monotonic ($T_{i} > T_{i-1}$). Backward time jumps trigger immediate dataset rejection.
2. **Date Uniqueness:** Duplicate trading dates trigger rejection.
3. **OHLC Structural Bounds:** 
   - $High \ge \max(Open, Close)$
   - $Low \le \min(Open, Close)$
   - $Low > 0$, $Open > 0$, $Close > 0$
4. **Volume Non-Negativity:** $Volume \ge 0$.
5. **Anomalous Single-Day Jump Detection:** Daily price moves $>40\%$ without an accompanying corporate action trigger diagnostic flagging.
6. **Trading Halts:** Suspended or circuit-halted bars are marked with `is_trading_halt: True`, preventing order execution during the suspension window.

---

## 4. Current Implementation State & Limitations

- **Implemented & Verified Fixtures:**
  - `RELIANCE` (70 daily bars, interim cash dividend on day 35) $\rightarrow$ `HISTORICAL_VERIFIED` / `CACHED`
  - `TCS` (70 daily bars, 1:1 bonus issue on day 50) $\rightarrow$ `HISTORICAL_VERIFIED` / `CACHED`
  - `NIFTY50_INDEX` (70 daily bars benchmark series) $\rightarrow$ `HISTORICAL_VERIFIED` / `CACHED`
- **Real-Time Market Feeds:** Real-time equity tick feeds from exchange brokers remain **BLOCKED** due to lack of licensed broker credentials and the mandatory loopback safety lock (`ENABLE_REAL_TRADING=false`).
- **Empirical Backtesting Status:** Backtests execute deterministically on curated historical benchmark fixtures. Empirical live backtesting across uncurated tickers requires licensed Bhavcopy ingestion before claims of out-of-sample live performance can be made.
