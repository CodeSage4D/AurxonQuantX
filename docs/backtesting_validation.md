# AURXON Backtesting Engine Validation & Verification
**Project:** AURXONQuant  
**Milestone:** Phase 3, Stage 1 — Deterministic Backtesting Engine  
**Status:** VERIFIED & PASSING  
**Date:** 2026-10-13  

---

## 1. Summary of Quantitative & Algorithmic Controls

The backtesting engine has been validated against 16 automated tests covering 7 core domains:

| Validation Domain | Test Assertion Method | Verification Result |
| :--- | :--- | :--- |
| **Historical Data Integrity** | Monotonicity, non-negative volume, OHLC structural bounds, anomalous moves | **PASSED** (`test_historical_series_validation_clean`, `test_historical_series_validation_detects_ohlc_violation`, `test_historical_series_validation_detects_duplicate_dates`) |
| **Indian Statutory Cost Math** | Line-item comparison against statutory rates (STT, Stamp Duty, GST, NSE Txn, SEBI Fee) | **PASSED** (`test_indian_cost_model_buy_delivery`, `test_indian_cost_model_sell_delivery_stamp_duty_exemption`) |
| **Bid-Ask Slippage Model** | Execution price shift relative to trade direction | **PASSED** (`test_slippage_adjustment`) |
| **Deterministic Replay** | Bit-for-bit identity across repeated identical backtest executions | **PASSED** (`test_deterministic_replay_identical_output`) |
| **Lookahead Prevention** | Execution date strictly greater than signal decision date ($T+1 > T$) | **PASSED** (`test_strictly_lagged_next_bar_execution`) |
| **Corporate Action Math** | Dividend cash credit and 1:1 bonus share doubling | **PASSED** (`test_corporate_actions_cash_dividend`, `test_corporate_actions_bonus_split_adjustment`) |
| **Order Rejection & Safety** | Insufficient cash rejection preventing negative balance | **PASSED** (`test_insufficient_cash_order_rejection`) |
| **Performance Reporting** | Net return < Gross return due to tax drag; drawdown in $[0\%, 100\%]$ | **PASSED** (`test_gross_vs_net_return_separation`, `test_drawdown_bounds`) |
| **API Endpoints & Audit** | Strategies, fixtures, and backtest run endpoints return valid JSON and chained hashes | **PASSED** (`test_api_backtest_strategies`, `test_api_backtest_fixtures`, `test_api_backtest_run_endpoint`) |

---

## 2. Independent Reference Check: Tax Schedule Verification

**Scenario:** Buy 100 shares of equity @ ₹1,000.00 on delivery (Turnover: ₹100,000.00).

$$\text{STT (0.1\%)} = 100,000 \times 0.001 = ₹100.00$$
$$\text{Stamp Duty (0.015\%)} = 100,000 \times 0.00015 = ₹15.00$$
$$\text{NSE Transaction Charges (0.00297\%)} = 100,000 \times 0.0000297 = ₹2.97$$
$$\text{SEBI Turnover Fee (₹10/Cr = 0.0001\%)} = 100,000 \times 0.000001 = ₹0.10$$
$$\text{GST (18\% on NSE Txn ₹2.97 + SEBI Fee ₹0.10)} = 3.07 \times 0.18 = ₹0.55$$
$$\text{Total Statutory Charges} = 100.00 + 15.00 + 2.97 + 0.10 + 0.55 = \mathbf{₹118.62}$$
$$\text{Total Cash Impact} = -(100,000 + 118.62) = \mathbf{-₹100,118.62}$$

*Engine Output:* `total_costs: 118.62`, `total_cash_impact: -100118.62` $\rightarrow$ **100% exact numerical match**.

---

## 3. Lookahead Leakage Audit

To verify that the engine is completely free of lookahead bias:
1. Every executed trade records both `signal_date` (the date of the bar whose close produced the signal) and `execution_date` (the date of the bar whose open filled the order).
2. The assertion `assert trade.execution_date > trade.signal_date` passes for all executed trades across all strategies.
3. No strategy has access to `bars[i+1]` or future prices during signal calculation.
