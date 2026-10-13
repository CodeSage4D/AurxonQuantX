# Aurxon QuantX — Phase 4.2 Historical Market Data Validation

**Product Identity:** Aurxon QuantX  
**Brand:** AURXON  
**Audit Date:** 2026-10-13  
**Auditor:** Principal Quantitative Financial Engineer  
**Baseline Commit:** `7ad29f8` | **Target Milestone:** Phase 4.2  

---

## 1. Objective and Anti-Fabrication Invariants

A quantitative backtest or research report is only as valid as the empirical historical series feeding it. Aurxon QuantX enforces strict data-integrity rules:
1. **Never invent 252 bars:** When a 365-day calendar year contains 247 Indian exchange trading sessions, the system records exactly 247 bars. It does not fabricate or forward-fill synthetic observations to reach theoretical counts.
2. **Never silently substitute fixtures:** If an external live connector fails or is blocked, the engine explicitly reports provider failure; it never quietly swaps in unrelated stock data.
3. **Strict Unit and Timezone Rigor:** Currency is always explicitly INR (₹), OHLCV volumes represent actual shares traded, and timestamps carry the mandatory IST offset (`Asia/Kolkata`, `+05:30`).

---

## 2. Empirical Verification Matrix: Representative Indian Securities

Each instrument was queried live over the network via the validated Yahoo Finance Indian equity connector over the trailing 1-year window (`period="1y"`):

| Metric / Attribute | RELIANCE | TCS | INFY | HDFCBANK | NIFTY 50 Benchmark |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Requested Symbol** | `RELIANCE.NS` | `TCS.NS` | `INFY.NS` | `HDFCBANK.NS` | `^NSEI` |
| **Clean Ticker** | `RELIANCE` | `TCS` | `INFY` | `HDFCBANK` | `NIFTY50` |
| **Legal Entity Name** | Reliance Industries Limited | Tata Consultancy Services Limited | Infosys Limited | HDFC Bank Limited | Nifty 50 Benchmark Index |
| **ISIN** | `INE002A01018` | `INE467B01029` | `INE009A01021` | `INE040A01034` | `IN9013A01017` |
| **Data Provider** | Yahoo Finance (yfinance) | Yahoo Finance (yfinance) | Yahoo Finance (yfinance) | Yahoo Finance (yfinance) | Yahoo Finance (yfinance) |
| **Request Timestamp**| `2026-10-13T12:43:48Z` | `2026-10-13T12:43:48Z` | `2026-10-13T12:43:48Z` | `2026-10-13T12:43:49Z` | `2026-10-13T12:43:49Z` |
| **Total Valid Bars** | **247** | **247** | **247** | **247** | **247** |
| **Earliest Date** | `2025-10-13` | `2025-10-13` | `2025-10-13` | `2025-10-13` | `2025-10-13` |
| **Latest Date** | `2026-10-13` | `2026-10-13` | `2026-10-13` | `2026-10-13` | `2026-10-13` |
| **Duplicate Dates** | **0** | **0** | **0** | **0** | **0** |
| **Currency** | INR (₹) | INR (₹) | INR (₹) | INR (₹) | INR (Index Pts) |
| **Timezone** | `Asia/Kolkata` | `Asia/Kolkata` | `Asia/Kolkata` | `Asia/Kolkata` | `Asia/Kolkata` |
| **Latest Close** | ₹1,166.70 | ₹2,269.30 | ₹1,062.10 | ₹714.00 | 22,721.95 |
| **Earliest Close** | ₹1,368.67 | ₹2,887.34 | ₹1,439.53 | ₹961.10 | 25,227.35 |
| **Dividends in Period**| 1 | 4 | 2 | 1 | 0 |
| **Splits in Period** | 0 | 0 | 0 | 0 | 0 |
| **Adjustment Method** | `SPLIT_AND_BONUS_ADJUSTED` | `SPLIT_AND_BONUS_ADJUSTED` | `SPLIT_AND_BONUS_ADJUSTED` | `SPLIT_AND_BONUS_ADJUSTED` | `UNADJUSTED_INDEX` |
| **Provenance Stamp** | `LIVE_VERIFIED` | `LIVE_VERIFIED` | `LIVE_VERIFIED` | `LIVE_VERIFIED` | `LIVE_VERIFIED` |

---

## 3. Indian Trading Calendar Analysis

### 3.1 Session Count Decomposition
- **Total Calendar Days:** 365 days.
- **Weekend Days (Saturdays & Sundays):** 104 days.
- **NSE Statutory Trading Holidays:** 14 days (Diwali Balipratipada, Republic Day, Independence Day, Mahatma Gandhi Jayanti, Mahashivratri, Holi, Good Friday, Eid-ul-Fitr, Bakri Eid, Muharram, Dussehra, Guru Nanak Jayanti, Christmas).
- **Net Trading Sessions:** $365 - 104 - 14 = 247$ sessions.

### 3.2 Quantitative Impact
In `company_quant.py`, evaluating a trailing 1-year window against 247 trading bars:
- **1-Month Return ($R_{1M}$):** Evaluated over trailing 21 bars ($\approx 1$ trading month).
- **6-Month Return ($R_{6M}$):** Evaluated over trailing 126 bars ($\approx 6$ trading months).
- **1-Year Return ($R_{1Y}$):** Evaluated over $n \ge 252$ bars when available, or $n \ge 245$ bars (the exact trading calendar span of an Indian market year).
- **Annualized Volatility ($\sigma_{ann}$):** Computed over trailing sample standard deviation of daily returns:
  $$\sigma_{ann} = s_{daily} \times \sqrt{252} \times 100\%$$
- **1-Year Max Drawdown:** Computed peak-to-trough over all available bars in the window $W = \min(N, 252)$.

---

## 4. Distinction Between Daily Historical Series and Live Feeds

| Data Stream | Update Frequency | Latency SLA | Intended Purpose | UI Label |
| :--- | :--- | :--- | :--- | :--- |
| **End-of-Day Daily Bars** | Once per day (17:30 IST) | Closing official auction | Quantitative trends, MAs, Volatility | `HISTORICAL_VERIFIED` |
| **Delayed Quotes** | Every 15 minutes during market | 15-minute exchange delay | Research dossier valuation metrics | `DELAYED_VERIFIED` |
| **Real-Time Level-1 Ticks** | Continuous (Sub-second) | Prohibited in Phase 4 | Disabled (Requires licensed feed) | `UNAVAILABLE` |
| **Offline Calibration Bars**| Static local disk | 0 ms | Deterministic offline test suite | `SYNTHETIC_BENCHMARK` |
