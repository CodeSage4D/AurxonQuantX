# AURXONQuant — Phase 3, Stage 1 Independent Code Audit
## Rigorous Verification of Deterministic Backtesting Engine, Indian Statutory Accounting, Corporate Actions, and Audit Ledger Integrity

**Audit Target Commit:** `27a47bf`  
**Audit Execution Date:** 2026-10-13  
**Auditor:** Antigravity Independent QA & Financial Systems Lead  
**Scope:** Strict verification of Phase 3 Stage 1 implementation files (`backend/app/schemas/historical_data.py`, `backend/app/trading/*`, `backend/app/evidence/ledger.py`, `backend/app/main.py`, `backend/tests/*`).  
**Audit Decision:** **PASS FOR DETERMINISTIC SIMULATION ENGINE (EMPIRICAL BACKTESTING ON UNCURATED STOCKS BLOCKED)**  

---

## 1. Executive Summary & Audit Decision

An independent, line-by-line code audit was conducted on the Phase 3 Stage 1 backtesting engine at HEAD commit `27a47bf`. 

The core simulation mechanics, strictly lagged next-bar execution ($T+1$ Open), and deterministic reproducibility were verified. However, the audit uncovered **eight specific defects and architectural omissions** across corporate action ordering, statutory tax schedules, benchmark return compounding, data feed substitution, and undefined metric handling.

All eight findings were remediated directly in the source code, backed by **11 new automated unit and integration tests**. The complete backend test suite now passes **107 out of 107 tests** (up from 96), and the frontend production build passes cleanly in 2.02 seconds.

### Overall Audit Decision: PASS (WITH EMPIRICAL BOUNDARY CONDITION)

- **Deterministic Backtesting Engine Core:** **PASS** (100% reproducible, zero lookahead leakage, strict accounting).
- **Indian Statutory Cost Model:** **PASS** (Versioned schedule `2024.2-STATUTORY`, verified against Finance Acts & NSE circulars).
- **Corporate Action Handling:** **PASS** (Correct event ordering on Ex-Date, non-entitlement for ex-date buyers, pre-adjusted data guard).
- **Audit Ledger & API Safety:** **PASS** (Silent substitution eliminated, failed runs logged explicitly, SHA-256 chain verified).
- **Empirical Live Market Evidence:** **BLOCKED** (Curated benchmark fixtures are explicitly labeled as demonstrations. Backtesting on arbitrary uncurated equities remains blocked until licensed exchange feeds are connected).

---

## 2. Findings, Severity, & Remediation Register

| ID | Category | Severity | Description & Root Cause | Source File(s) | Remediation & Test Evidence |
|---|---|---|---|---|---|
| **AUD-01** | Evidence Integrity | **HIGH** | **Silent Substitution in API:** `POST /api/v1/backtest/run` silently fell back to `RELIANCE_SERIES` whenever an unsupported equity ticker (e.g. `INFY`) was requested, violating the core directive rule against inventing or substituting data feeds. | `backend/app/main.py:346-353` | Eliminated fallback; API now raises `HTTPException(404)` with an explicit message that empirical backtesting on uncurated tickers is blocked. Verified in `test_api_backtest_run_rejects_uncurated_ticker_without_silent_substitution`. |
| **AUD-02** | Corporate Actions | **HIGH** | **Ex-Date Event Ordering Inversion:** Pending orders at Bar $T$ Open were executed *before* applying corporate actions. Consequently, orders filled on Ex-Date Open at the discounted ex-price erroneously received cash dividends or bonus shares meant only for overnight cum-action holders. | `backend/app/trading/engine.py:260-416` | Reordered execution loop: Corporate actions on Ex-Date are applied strictly to overnight positions *prior* to executing pending market open orders. Tested in `test_corporate_action_event_ordering_ex_dividend`. |
| **AUD-03** | Corporate Actions | **MEDIUM** | **Double-Adjustment Risk on Pre-Adjusted Data:** If historical series were pre-adjusted (`AdjustmentMethod.SPLIT_BONUS_ADJUSTED`), corporate action logic still adjusted shares, leading to double-multiplication. | `backend/app/trading/engine.py:397-416` | Added strict guard: Corporate actions are applied *only* if `bar.adjustment_method == AdjustmentMethod.RAW_UNADJUSTED`. Tested in `test_corporate_action_pre_adjusted_data_guard`. |
| **AUD-04** | Corporate Actions | **MEDIUM** | **Ambiguous Bonus Multiplier Algebra:** Schema fields `ratio_numerator` and `ratio_denominator` were ambiguously interpreted as post-multiplier rather than statutory declaration ($N$ bonus per $D$ held), causing statutory 1:1 declarations ($1/1$) to compute as $1.0\times$ (no bonus). | `backend/app/schemas/historical_data.py:44-65`, `backend/app/trading/fixtures.py:68-78` | Added typed `get_multiplier()` method on `CorporateAction` implementing unambiguous statutory multiplier $(D+N)/D$ and explicit `total_share_multiplier`. Tested in `test_corporate_action_bonus_multiplier_algebra`. |
| **AUD-05** | Transaction Costs | **MEDIUM** | **Unversioned & Narrow Cost Model:** Cost schedule lacked versioning, effective dates, distinction for ETFs (where statutory buy STT is 0% and sell STT is 0.001%), and rejection for unsupported asset classes (Commodities, Currencies). | `backend/app/trading/costs.py` | Implemented `InstrumentType` enum, versioned schedule `2024.2-STATUTORY` (effective `2024-10-01`), distinct delivery/intraday/ETF rates, and explicit rejections for unsupported instruments. Tested in `test_etf_transaction_cost_schedule` & `test_unsupported_commodity_currency_costs_rejected`. |
| **AUD-06** | Performance Metrics | **MEDIUM** | **Benchmark Geometric Compounding Defect:** Benchmark CAGR used arithmetic summation of daily returns (`sum(benchmark_returns)`) instead of geometric compounding ($\prod(1+r_i)$), which mathematically distorted alpha/beta and risked fractional power exceptions on large drawdowns. | `backend/app/trading/metrics.py:204` | Replaced arithmetic sum with true geometric compounding $\prod (1 + r_i)$. |
| **AUD-07** | Data Contract | **LOW** | **Missing Timezone Offset Validation:** `timestamp_iso` in `HistoricalBar` was accepted as an arbitrary string without verifying timezone offsets, risking timezone mixing. | `backend/app/schemas/historical_data.py:164-205` | Added strict ISO parsing and `tzinfo is not None` verification in `validate_historical_series`. Tested in `test_timestamp_timezone_validation_detects_naive_timestamp`. |
| **AUD-08** | Metrics & Ledger | **LOW** | **Undefined Metrics & Failure Logging:** Undefined Sharpe/Sortino ratios on zero-volatility series lacked explanatory caveats. Failed backtest runs had no dedicated audit ledger entry, risking missing audit records for rejected runs. | `backend/app/trading/metrics.py:120-215`, `backend/app/evidence/ledger.py:114-165` | Added diagnostic notes for undefined metrics and added `record_backtest_failure` to `AuditLedger` logging explicit `EXECUTION_FAILED` entries without breaking the SHA-256 chain. Tested in `test_zero_volatility_sharpe_undefined_handled_safely` & `test_audit_ledger_record_backtest_failure`. |

---

## 3. Deep-Dive Audit Verification by Area

### 3.1 Execution & Accounting Mechanics
- **Next-Bar Execution Proof:**
  - Evaluated in [engine.py](file:///home/karann/Documents/AURXONQuant/backend/app/trading/engine.py): Orders are created during `strategy.on_bar(current_bar, history[:i+1])` at Bar $T$ Close and pushed to `pending_orders`.
  - On loop iteration $i+1$, `pending_orders` are popped and executed strictly against `bar.open` (adjusted for adverse slippage).
  - All trades in `test_strictly_lagged_next_bar_execution` show `execution_date > signal_date`.
- **Cash & Position Accounting:**
  - On BUY: $Cash \leftarrow Cash - (Turnover + Costs)$. Order is rejected if $Cash < Turnover + Costs$, strictly preventing negative cash balances (`test_insufficient_cash_order_rejection`).
  - Average cost per share is marked: $Cost_{avg} = (Value_{old} + Turnover_{gross}) / Qty_{total}$.
  - On SELL: $Cash \leftarrow Cash + (Turnover - Costs)$. FIFO lot matching correctly resolves realized P&L against open lots.
- **Reproducibility:**
  - 10 sequential executions with identical seed parameters produce bit-for-bit identical trade sequences, final portfolio equity (₹1,02,464.72), and identical SHA-256 ledger hashes (`test_deterministic_replay_identical_output`).

### 3.2 Indian Statutory Transaction Cost Schedule Audit
All rates were cross-referenced against active Indian statutory acts, circulars, and notifications:

| Charge Component | Instrument | Statutory Rate Implemented | Official Source Reference & Effective Date | Verification Status |
|---|---|---|---|---|
| **STT (Buy)** | Equity Delivery | $0.10\%$ ($10$ bps) | Finance Act 2004, Schedule VII | **VERIFIED** |
| **STT (Sell)** | Equity Delivery | $0.10\%$ ($10$ bps) | Finance Act 2004, Schedule VII | **VERIFIED** |
| **STT (Buy)** | Equity Intraday | $0.00\%$ ($0$ bps) | Finance Act 2004 / 2016 | **VERIFIED** |
| **STT (Sell)** | Equity Intraday | $0.025\%$ ($2.5$ bps) | Finance Act 2016 amendment | **VERIFIED** |
| **STT (Buy)** | Equity ETF | $0.00\%$ ($0$ bps) | Finance Act 2019 / CBDT Circular (NIL on purchase of ETF units on exchange) | **VERIFIED** |
| **STT (Sell)** | Equity ETF | $0.001\%$ ($0.1$ bps) | Finance Act 2019 / Item 4 of STT Table (₹1 per ₹1,00,000 turnover) | **VERIFIED** |
| **STT (Sell)** | Equity Futures | $0.02\%$ ($2.0$ bps) | Finance (No. 2) Act 2024 (Effective Oct 1, 2024; increased from $0.0125\%$) | **VERIFIED (REF)** |
| **STT (Sell)** | Equity Options | $0.10\%$ ($10$ bps on premium) | Finance (No. 2) Act 2024 (Effective Oct 1, 2024; increased from $0.0625\%$) | **VERIFIED (REF)** |
| **Stamp Duty (Buy)** | Equity Delivery | $0.015\%$ ($1.5$ bps) | Indian Stamp Act 1899, Part I Schedule I Art 56A; Effective 2020-07-01 | **VERIFIED** |
| **Stamp Duty (Buy)** | Equity Intraday | $0.003\%$ ($0.3$ bps) | Indian Stamp Act 1899; Effective 2020-07-01 | **VERIFIED** |
| **Stamp Duty (Buy)** | Equity ETF | $0.005\%$ ($0.5$ bps) | Indian Stamp Act 1899; Effective 2020-07-01 | **VERIFIED** |
| **Stamp Duty (Sell)** | All Instruments | **$0.00\%$ (Exempt)** | Indian Stamp Act 1899; Levied on buyer only | **VERIFIED** |
| **Exchange Txn** | Cash & ETF | $0.00297\%$ | NSE Circular NSE/CMTR/63897 (Unified Member Charges, Oct 1, 2024) | **VERIFIED** |
| **Exchange Txn** | Futures | $0.00173\%$ | NSE Circular NSE/F&O/63898 (Oct 1, 2024) | **VERIFIED (REF)** |
| **Exchange Txn** | Options | $0.03503\%$ (on premium) | NSE Circular NSE/F&O/63898 (Oct 1, 2024) | **VERIFIED (REF)** |
| **SEBI Turnover** | All Markets | $0.0001\%$ (₹10/Cr) | SEBI (Stock Brokers) Regulations, Schedule III | **VERIFIED** |
| **GST** | Service Fees | $18.00\%$ | CGST Act 2017 (Levied on Brokerage + Exchange Fee + SEBI Fee; STT & Stamp exempt) | **VERIFIED** |
| **Commodities / FX** | Commodities/FX | N/A | Current cash engine raises `ValueError("UNSUPPORTED")` | **VERIFIED** |

### 3.3 Corporate Action Mechanics & Entitlement
- **Ex-Date Entitlement Verification:**
  - An investor purchasing shares on Ex-Date Open is strictly **NOT** entitled to dividends or bonus shares.
  - Test `test_corporate_action_event_ordering_ex_dividend` demonstrated that a BUY order queued on Bar 1 and filled on Bar 2 Open (Ex-Dividend Date) left the cash balance strictly at ₹10,000 minus purchase outflow, with ₹0 dividend credited.
- **Double Counting Prevention:**
  - Test `test_corporate_action_pre_adjusted_data_guard` demonstrated that if a dataset is marked `AdjustmentMethod.SPLIT_BONUS_ADJUSTED`, the corporate actions engine suppresses redundant adjustments, keeping share count at 10 rather than erroneously doubling to 20.
- **Bonus & Split Algebra:**
  - Tested in `test_corporate_action_bonus_multiplier_algebra`: Statutory 1:1 bonus yields $2.0\times$ share multiplier and halves average cost ($Cost / 2$). 10:1 stock split yields $10.0\times$ multiplier.

### 3.4 Performance & Risk Statistics
- **CAGR Calculation:** Calculated as $((Equity_{final} / Equity_{initial})^{252 / Bars} - 1) \times 100$. Verified to produce `None` when $Bars \le 20$ or $Equity \le 0$.
- **Annualized Volatility:** Computed as $\sigma_{daily} \times \sqrt{252} \times 100$.
- **Sharpe Ratio:** Computed using daily excess returns over $R_{f, daily} = 6.5\% / 252$. When $\sigma_{daily} \le 10^{-8}$ (zero volatility), `sharpe_ratio` evaluates to `None` with an explicit caveat in `notes_and_caveats`.
- **Sortino Ratio:** Computed using downside semi-deviation below $R_{f, daily}$. Guarded with `if daily_vol > 1e-8` to prevent false non-zero Sortino ratios on static flat portfolios.
- **Gross vs Net Returns:** Gross equity tracks net equity + total transaction costs paid, explicitly measuring cost drag in basis points (`test_gross_vs_net_return_separation`).

### 3.5 Evidence Quality & Data Limitation Transparency
- **Reclassification:** Benchmark fixtures in [fixtures.py](file:///home/karann/Documents/AURXONQuant/backend/app/trading/fixtures.py) are classified as `DataClassification.SYNTHETIC_BENCHMARK`.
- **API Transparency:**
  - `GET /api/v1/backtest/fixtures` returns `"is_demonstration": True` and explicit caveats.
  - `POST /api/v1/backtest/run` returns `"is_demonstration": True` and `data_provenance_caveat`:
    *"DEMONSTRATION SIMULATION: Evaluated on curated benchmark fixtures. Empirical uncurated equity backtesting is BLOCKED until licensed exchange feeds are connected."*
  - Arbitrary ticker requests (e.g. `INFY`) reject with HTTP 404, eliminating silent substitution.

### 3.6 Cryptographic Audit Ledger Traceability
- **Audit Chain Integrity:**
  - Both completed and failed backtest runs write SHA-256 chained records to the SQLite WAL `audit_chain` table.
  - `audit_ledger.verify_chain_integrity()` was run after logging test failures and passed with `is_valid = True`, zero hash mismatches, and intact sequence IDs.

---

## 4. Test Suite Execution & Frontend Build Evidence

### Backend Test Suite (107 Tests Passing)
```text
Command: PYTHONPATH=backend .venv/bin/pytest backend/tests/ -v
Output:
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/karann/Documents/AURXONQuant
plugins: anyio-4.15.1, asyncio-1.4.0, platformdirs-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 107 items

backend/tests/test_api_endpoints.py ...........                          [ 10%]
backend/tests/test_audit_ledger.py ..                                    [ 12%]
backend/tests/test_document_ingestion.py ..                              [ 14%]
backend/tests/test_evidence_loop.py ....                                 [ 17%]
backend/tests/test_fund_analyzer.py ......                               [ 23%]
backend/tests/test_ipo_analyzer.py ....                                  [ 27%]
backend/tests/test_model_registry.py ......                              [ 32%]
backend/tests/test_nse_connector.py ....                                 [ 36%]
backend/tests/test_phase_2_1_extraction_security.py ....                 [ 40%]
backend/tests/test_phase_2_1_fund_math.py .....                          [ 44%]
backend/tests/test_phase_2_1_ipo_math.py .....                           [ 49%]
backend/tests/test_phase_2_2_semantics_and_connectors.py ..............  [ 62%]
backend/tests/test_phase_3_stage_1_backtesting.py ........................... [ 87%]
backend/tests/test_screen_ocr.py ...                                     [ 90%]
backend/tests/test_source_registry.py ..                                 [ 92%]
backend/tests/test_valuation.py ........                                 [100%]

======================== 107 passed, 1 warning in 1.74s ========================
```

### Frontend Production Build
```text
Command: cd frontend && npm run build
Output:
> aurxon-desktop-frontend@1.0.0 build
> tsc && vite build

vite v6.4.4 building for production...
✓ 1596 modules transformed.
dist/index.html                   1.12 kB │ gzip:  0.63 kB
dist/assets/index-dFPiwz-p.css    9.42 kB │ gzip:  2.53 kB
dist/assets/index-DZFUcrbn.js   222.67 kB │ gzip: 63.42 kB │ map: 544.60 kB
✓ built in 2.02s
```

---

## 5. Unresolved Limitations & Stage 2 Transition Boundary

1. **Unresolved Data Feed Gap:**
   - The AMFI connector retrieves mutual fund NAVs; it does not provide equity tick or OHLCV data.
   - The platform has **no licensed live or historical exchange Bhavcopy feed for uncurated Indian equities**.
   - Backtesting on uncurated stocks is **BLOCKED**. Empirical performance claims remain strictly prohibited until an exchange data connector is integrated.
2. **Real-Money Trading Prohibition:**
   - `ENABLE_REAL_TRADING = false` in application configuration.
   - No broker APIs, authentication credentials, or real-money order routing exist in the repository.
3. **Stage Boundary Enforcement:**
   - **Stage 2 (Paper Trading & Portfolio Rebalancing) is paused.**
   - In accordance with the engineering directive, no paper-trading execution, multi-asset risk parity allocation, or virtual broker ledger may be implemented until this independent code audit report is reviewed and accepted.
