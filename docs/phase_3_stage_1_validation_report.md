# AURXONQuant — Phase 3, Stage 1 Validation Report
## Deterministic Backtesting Engine: Verification, Safety Gates, & Statutory Accounting Audit

**Document Version:** 1.0.0  
**Verification Date:** 2026-10-13  
**Verified Baseline:** Commit `738eed4`  
**Target Architecture:** AURXON Adaptive Evidence Intelligence Architecture (AEIA) — Phase 3 Simulation Engine  
**Classification:** Research & Simulation Engineering Gate (Simulation Only — Live Order Routing Blocked)  

---

## 1. Executive Summary & Gate Status

In compliance with the **Phase 3, Stage 1 Implementation Directive**, the quantitative research backtesting engine has been implemented, validated, and hardened for Indian financial market strategies.

### Gate Clearance Summary

| Gate Requirement | Status | Verification Summary |
|---|---|---|
| **Preserve Existing Subsystems** | **VERIFIED** | IPO research, mutual fund analytics, primary AMFI connector, SEC/SEBI lineage, model adapters, and SQLite audit ledger operate unchanged. |
| **Typed Historical Data Contract** | **VERIFIED** | Enforces `HistoricalBar`, OHLC validation ($Low \le Close, Open \le High$), timezone metadata (`Asia/Kolkata`), adjustment metadata, and data classification. |
| **Data Source Reality Check** | **VERIFIED** | Explicitly documents that AMFI supplies mutual fund NAVs, **not** equity OHLCV. Equity backtesting uses validated benchmark fixtures (`RELIANCE`, `TCS`, `NIFTY50`). Empirical backtesting on uncurated stocks is recorded as **BLOCKED** until licensed Bhavcopy/tick feeds are connected. |
| **Deterministic Next-Bar Engine** | **VERIFIED** | Lookahead bias structurally eliminated: Signals generated at Bar $T$ Close execute strictly at Bar $T+1$ Open. Same-bar fills are forbidden. Replay is 100% bit-exact across multiple runs. |
| **Indian Statutory Cost Model** | **VERIFIED** | Independent validation of STT (0.1% buy/sell delivery), Stamp Duty (0.015% buy only), NSE transaction charges (0.00297%), SEBI turnover charges (₹10/Cr), GST (18% on fees), and bid-ask slippage. |
| **Corporate Action Handling** | **VERIFIED** | Cash dividends credited to cash on Ex-Date; stock splits and bonus issues adjust position quantities and base price without double-adjusting price series. |
| **Risk & Return Metrics** | **VERIFIED** | Gross vs Net CAGR, Maximum Drawdown, Sharpe & Sortino ratios calculated with Indian risk-free rate ($R_f = 6.5\%$). Degenerate volatility ($=0$) and zero-trade scenarios handled safely without exceptions. |
| **Audit Ledger Recording** | **VERIFIED** | Every backtest run records its parameter hash, dataset hash, metric summary, and strategy metadata into the SHA-256 tamper-evident SQLite audit ledger. |
| **Scope Boundary & Real-Money Guard** | **VERIFIED** | `ENABLE_REAL_TRADING = false`. No live broker connectors or real capital routing are implemented. Paper trading portfolio management is paused until Stage 2 review. |

---

## 2. Test Execution & Build Verification

### 2.1 Backend Automated Test Suite
- **Command:** `PYTHONPATH=backend .venv/bin/pytest backend/tests/`
- **Output:**
  ```text
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
  rootdir: /home/karann/Documents/AURXONQuant
  plugins: anyio-4.15.1, asyncio-1.4.0, platformdirs-4.13.0
  asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collected 96 items

  backend/tests/test_api_endpoints.py ...........                          [ 11%]
  backend/tests/test_audit_ledger.py ..                                    [ 13%]
  backend/tests/test_document_ingestion.py ..                              [ 15%]
  backend/tests/test_evidence_loop.py ....                                 [ 19%]
  backend/tests/test_fund_analyzer.py ......                               [ 26%]
  backend/tests/test_ipo_analyzer.py ....                                  [ 30%]
  backend/tests/test_model_registry.py ......                              [ 36%]
  backend/tests/test_nse_connector.py ....                                 [ 40%]
  backend/tests/test_phase_2_1_extraction_security.py ....                 [ 44%]
  backend/tests/test_phase_2_1_fund_math.py .....                          [ 50%]
  backend/tests/test_phase_2_1_ipo_math.py .....                           [ 55%]
  backend/tests/test_phase_2_2_semantics_and_connectors.py ..............  [ 69%]
  backend/tests/test_phase_3_stage_1_backtesting.py ................       [ 86%]
  backend/tests/test_screen_ocr.py ...                                     [ 89%]
  backend/tests/test_source_registry.py ..                                 [ 91%]
  backend/tests/test_valuation.py ........                                 [100%]

  ======================== 96 passed, 1 warning in 1.62s =========================
  ```
- **Test Count Progression:** 80 passing (Phase 2.2) $\rightarrow$ **96 passing** (Phase 3 Stage 1) across 16 test suites.

### 2.2 Frontend Production Build
- **Command:** `npm run build` (within `frontend/`)
- **Output:**
  ```text
  > aurxon-desktop-frontend@1.0.0 build
  > tsc && vite build

  vite v6.4.4 building for production...
  ✓ 1596 modules transformed.
  dist/index.html                   1.12 kB │ gzip:  0.63 kB
  dist/assets/index-dFPiwz-p.css    9.42 kB │ gzip:  2.53 kB
  dist/assets/index-DZFUcrbn.js   222.67 kB │ gzip: 63.42 kB │ map: 544.60 kB
  ✓ built in 2.06s
  ```
- **Diagnostics:** Zero TypeScript compilation errors, zero packaging defects.

---

## 3. Detailed Component Verification

### 3.1 Historical Data Contract (`app/schemas/historical_data.py`)
- **Schema Design:**
  - `HistoricalBar`: Requires `instrument_id`, `exchange`, `timestamp` (with timezone), `open`, `high`, `low`, `close`, `volume`. Validates $low \le min(open, close)$ and $high \ge max(open, close)$ and $volume \ge 0$.
  - `CorporateAction`: Supports `CASH_DIVIDEND`, `STOCK_SPLIT`, `BONUS_ISSUE`, `RIGHTS_ISSUE` with `ratio_from`, `ratio_to`, `cash_amount`, and `ex_date`.
  - `HistoricalSeriesContract`: Encapsulates instrument metadata, adjustment methodology (`RAW_UNADJUSTED` default for simulation execution), source classification (`BENCHMARK_FIXTURE`, `HISTORICAL_BHAVCOPY`, `SYNTHETIC_DEMO`), and data quality report.
- **Validation Engine:**
  - Detects duplicate timestamps, chronological sequencing violations, price inversions, zero volume anomalies, and missing gaps.

### 3.2 Indian Statutory Transaction Cost Model (`app/trading/costs.py`)
- **Statutory Rules Applied:**
  - **Securities Transaction Tax (STT):** $0.10\%$ on both BUY and SELL turnover for equity delivery under Finance Act 2004.
  - **Stamp Duty:** $0.015\%$ on BUY turnover only under the Indian Stamp Act amendment (July 2020). Zero on SELL.
  - **Exchange Transaction Charges:** $0.00297\%$ on total turnover (NSE standard equity rate).
  - **SEBI Turnover Charges:** ₹10 per ₹1 Crore of turnover ($0.0001\%$).
  - **Goods and Services Tax (GST):** $18\%$ levied on brokerage, exchange transaction charges, and SEBI turnover fees. (Statutorily not levied on STT or Stamp Duty).
  - **Bid-Ask Slippage:** Configurable model (default $0.05\%$) applied adversely to execution prices.
- **Verification Example (Buy ₹1,00,000 Equity Delivery @ Zero Brokerage):**
  - Turnover: ₹100,000.00
  - STT: ₹100.00
  - Stamp Duty: ₹15.00
  - Exchange Fee: ₹2.97
  - SEBI Fee: ₹0.10
  - GST ($18\%$ of ₹3.07): ₹0.55
  - Statutory Total: ₹118.62 (plus slippage ₹50.00 $\rightarrow$ Total Friction ₹168.62).
  - Unit tests confirm exact calculations across buy and sell legs.

### 3.3 Deterministic Backtest Engine (`app/trading/engine.py`)
- **Lookahead Prevention Protocol:**
  - Step 1: Process corporate actions on Ex-Date before open.
  - Step 2: Execute pending orders queued from previous bar ($T-1$) at current bar ($T$) Open price (adjusted for slippage).
  - Step 3: Check cash sufficiency ($Cash \ge Cost$). If insufficient, reject order explicitly with audit reason.
  - Step 4: Mark portfolio to market at current bar Close price.
  - Step 5: Execute strategy `on_bar(T)` with access only to bars $\le T$. Generated orders are placed in the pending queue for bar $T+1$.
- **Reproducibility Test:**
  - 10 consecutive runs with identical parameters produced identical trade records, portfolio final values (₹1,02,464.72 on Dual MA), and identical SHA-256 run fingerprints.

### 3.4 Corporate Actions Execution Engine
- **Cash Dividend:**
  - On Ex-Date, credited directly to portfolio cash: $Cash_{new} = Cash_{old} + (Quantity \times DividendPerShare)$.
  - Position quantity and average purchase price remain unchanged.
- **Stock Split / Bonus Issue:**
  - On Ex-Date, share quantity scales: $Quantity_{new} = Quantity_{old} \times (Ratio_{to} / Ratio_{from})$.
  - Cost basis per share scales inversely: $Cost_{new} = Cost_{old} \times (Ratio_{from} / Ratio_{to})$.
  - Cash balance and total invested capital remain strictly preserved.

### 3.5 Quantitative Risk & Return Statistics (`app/trading/metrics.py`)
- **Metrics Computed:**
  - **Total Return:** $\frac{Equity_{final} - Equity_{initial}}{Equity_{initial}}$ (Gross and Net reported separately).
  - **CAGR:** $(1 + R_{total})^{365 / Days} - 1$.
  - **Maximum Drawdown:** Calculated from peak running equity series.
  - **Annualized Volatility:** $\sigma_{daily} \times \sqrt{252}$.
  - **Sharpe Ratio:** $\frac{CAGR - R_f}{Annualized\ Volatility}$ with Indian Risk-Free Rate $R_f = 6.50\%$.
  - **Sortino Ratio:** Computed using downside semi-deviation below $0.0$.
  - **Cost Drag:** Difference between Gross and Net Return in basis points.

---

## 4. API & Ledger Verification

### 4.1 REST API Surface
- `GET /api/v1/backtest/strategies`: Returns list of available versioned strategies (`dual_ma_strategy_v1`, `buy_and_hold_v1`).
- `GET /api/v1/backtest/fixtures`: Returns available validated fixtures (`RELIANCE_DEMO`, `TCS_BONUS_DEMO`, `NIFTY50_BENCHMARK`).
- `POST /api/v1/backtest/run`: Executes simulation, updates audit ledger, and returns full metrics report and trade execution logs.

### 4.2 Audit Ledger Traceability
- All backtests executed via engine or API record an entry into the SQLite WAL `audit_chain` table with:
  - Event type: `BACKTEST_EXECUTION_COMPLETED`
  - Canonical JSON payload including: `run_id`, `strategy_name`, `strategy_version`, `dataset_id`, `dataset_source`, `parameter_hash`, `net_return_pct`, `max_drawdown_pct`, and `audit_timestamp`.
  - Sequential SHA-256 cryptographic chaining verifying tamper evidence.

---

## 5. Scope Boundary & Issue Register Status

1. **Empirical Historical Data Gap:**
   - **Status:** **BLOCKED for empirical uncurated equity trading.**
   - **Reason:** The AMFI connector provides mutual fund NAVs, not equity tick or daily OHLCV. The platform lacks an official licensed exchange feed for uncurated Indian equity tickers.
   - **Mitigation:** High-quality benchmark fixtures (`RELIANCE`, `TCS`, `NIFTY50`) are provided with documented lineage. Empirical backtesting on uncurated stocks is flagged as blocked until Phase 3 Stage 2/3 exchange data connectors are onboarded.
2. **Real-Money Trading Prohibition:**
   - **Status:** Strictly Enforced.
   - `ENABLE_REAL_TRADING = false` in configuration.
   - No broker APIs or real money order execution mechanisms exist.

---

## 6. Stage 1 Sign-Off

The **Phase 3, Stage 1 Deterministic Backtesting Engine** has fulfilled all architectural, mathematical, statutory, and reproducibility requirements.

Execution is paused at the Stage 1 boundary. Proceeding to Stage 2 (Paper Trading & Portfolio Allocation) awaits founder/stakeholder review and approval.
