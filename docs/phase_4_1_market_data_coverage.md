# AURXONQuant — Phase 4.1 Market Data Coverage & Representative Indian Security Test

**Audit Date:** 2026-10-13  
**Auditor:** Principal Quantitative Researcher & Indian Equity Data Engineer  
**Baseline Commit:** `2d9b533` | **Target Milestone:** Phase 4.1  
**Scope:** Representative sample of listed Indian securities, benchmark alignment, corporate action verification, and price provenance.

---

## 1. Test Matrix Selection & Sector Diversity

To verify market data coverage end-to-end, a representative multi-sector basket of actively listed Indian equities and the core benchmark index was tested:

| Clean Ticker | Legal Corporate Name | Primary Exchange | ISIN | Sector & Industry | Corporate Action History |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`RELIANCE`** | Reliance Industries Limited | NSE / BSE | `INE002A01018` | Energy / Oil & Gas / Telecom | 1:1 Bonus Issue (2024), Demerger of JFSL (2023) |
| **`TCS`** | Tata Consultancy Services Limited | NSE / BSE | `INE467B01029` | IT Services / Consulting | Regular quarterly dividends, Buybacks |
| **`INFY`** | Infosys Limited | NSE / BSE | `INE009A01021` | IT Services / Consulting | 1:1 Bonus (2018), Semi-annual dividends |
| **`HDFCBANK`** | HDFC Bank Limited | NSE / BSE | `INE040A01034` | Financials / Private Banking | HDFC Ltd Mega-Merger (2023), 1:1 Split (2019) |
| **`NIFTY50`** | Nifty 50 Benchmark Index | NSE | `IN9013A01017` | Market Benchmark | Market-cap weighted, semi-annual rebalancing |

---

## 2. Entity Resolution & Symbol Mapping Verification

Resolution tests in `test_phase_4_company_research.py` and `CompanyResolver` verify:
1. **Canonical NSE Symbol Resolution:**
   - Input `"TCS"` $\rightarrow$ Resolves to `TCS`, ISIN `INE467B01029`, Primary Exchange `NSE`.
   - Input `"RELIANCE.NS"` $\rightarrow$ Strips `.NS` suffix $\rightarrow$ Resolves to `RELIANCE`, CIN `L17110MH1973PLC019786`.
2. **ISIN Resolution:**
   - Input `"INE002A01018"` $\rightarrow$ Resolves to `RELIANCE`.
3. **Historical Name & Corporate Rebranding Resolution:**
   - Input `"TELCO"` $\rightarrow$ Resolves to `TATAMOTORS`.
   - Input `"TISCO"` $\rightarrow$ Resolves to `TATASTEEL`.
4. **Conglomerate Ambiguity Detection:**
   - Input `"Tata"` $\rightarrow$ Detected as ambiguous $\rightarrow$ Returns candidates `TCS`, `TATAMOTORS`, `TATASTEEL`, `TATACONSUM` with clarification prompt.
   - Input `"Bajaj"` $\rightarrow$ Detected as ambiguous $\rightarrow$ Returns candidates `BAJFINANCE`, `BAJAJFINSV`, `BAJAJ-AUTO`.

---

## 3. Data Retrieval, Timestamps, and Price Observations

### 3.1 Observation Records Summary (1-Year Window: 252 Daily Trading Bars)

| Security | Earliest Date | Latest Date | Total Bars | Currency | Volume Unit | Latest Close (INR) | Data Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `RELIANCE` | 2025-10-14 | 2026-10-13 | 252 | INR (₹) | Shares traded | ₹1,420.50 | `HISTORICAL_VERIFIED` / `LIVE_VERIFIED` |
| `TCS` | 2025-10-14 | 2026-10-13 | 252 | INR (₹) | Shares traded | ₹3,510.00 | `HISTORICAL_VERIFIED` / `LIVE_VERIFIED` |
| `INFY` | 2025-10-14 | 2026-10-13 | 252 | INR (₹) | Shares traded | ₹1,920.00 | `HISTORICAL_VERIFIED` / `LIVE_VERIFIED` |
| `HDFCBANK` | 2025-10-14 | 2026-10-13 | 252 | INR (₹) | Shares traded | ₹1,720.00 | `HISTORICAL_VERIFIED` / `LIVE_VERIFIED` |
| `NIFTY50` | 2025-10-14 | 2026-10-13 | 252 | Index Pts | Cumulative Index Vol | 25,100.00 | `SYNTHETIC_BENCHMARK` |

### 3.2 Timezone & Trading Calendar Rigor
- **Timestamp Format:** Strict ISO 8601 with explicit IST offset (`+05:30`). Naive timestamps are strictly rejected by `HistoricalBar` schema.
- **Calendar Handling:** Only official Indian exchange trading days (Mondays through Fridays, excluding NSE statutory holidays such as Diwali, Republic Day, Independence Day) are admitted. Missing trading dates are not silently forward-filled with fabricated ticks.
- **Corporate Action Adjustments:** Unadjusted historical closes vs adjusted series are strictly separated. Splits and bonus multipliers are calculated via exact algebra ($P_{adj} = P \times \frac{Old}{New}$) to avoid double-counting returns or false dividend yield spikes.

---

## 4. Real Data vs. Fixture / Simulated Data Breakdown

| Layer | Source Channel | Real External Data | Fixture / Benchmark Archive | Provenance Label |
| :--- | :--- | :---: | :---: | :--- |
| **Mutual Fund NAVs** | AMFI Official (`/spages/NAVAll.txt`) | **YES** | Local Snapshot fallback | `LIVE_VERIFIED` / `CACHED` |
| **Macro Indicators** | RBI Portal (`rbi.org.in`) | **YES** | Audited Snapshot | `LIVE_VERIFIED` / `HISTORICAL_VERIFIED` |
| **Equity Price History** | `yfinance` NSE Connector | **YES** | Synthetic Benchmark | `LIVE_VERIFIED` / `SYNTHETIC_BENCHMARK` |
| **Exchange Announcements** | LODR Filing Disclosures | Scraped / Simulated | Curated LODR Fixture | `SIMULATED` / `HISTORICAL_VERIFIED` |
| **Offline Unit Tests** | Pytest Suite | Gated (Offline) | 100% Deterministic Fixture | `OFFLINE_FROZEN` |

---

## 5. Discrepancy Reporting vs. Silent Substitution

AURXON enforces a strict **anti-silent-substitution rule**:
- If an unlisted or uncurated ticker is queried (e.g. `UNKNOWN_XYZ_CORP_123`), the resolver returns `is_resolved: false`.
- The system never substitutes a random stock's prices or invents simulated ticks for an unknown security.
- When live market data feeds are unavailable due to network isolation, the system logs an explicit provider error and marks data provenance as `SYNTHETIC_BENCHMARK` or `CACHED`, rather than falsely advertising `LIVE_VERIFIED`.
