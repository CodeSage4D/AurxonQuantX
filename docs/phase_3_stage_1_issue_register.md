# AURXON Phase 3, Stage 1 Issue Register
**Project:** AURXONQuant  
**Milestone:** Phase 3, Stage 1 — Deterministic Backtesting Engine  
**Date:** 2026-10-13  

---

## 1. Resolved Issues in Stage 1

| Issue ID | Category | Severity | Description | Resolution | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-3.1-01** | Data Contract | HIGH | Inability to distinguish equity OHLCV series from statutory mutual fund NAV data. | Instituted `HistoricalBar` and `HistoricalSeriesContract` schemas with strict OHLC structural validation. | **RESOLVED** |
| **ISSUE-3.1-02** | Lookahead Bias | CRITICAL | Same-bar order generation and fill leakage could inflate backtest performance. | Enforced lagged execution queue where Bar T close signals execute strictly on Bar T+1 Open. | **RESOLVED** |
| **ISSUE-3.1-03** | Indian Tax Model | HIGH | Lack of statutory Indian transaction cost schedules (STT, Stamp Duty, GST, NSE Txn, SEBI fee). | Built `IndianTransactionCostModel` with statutory defaults and exact line-item audit breakdowns. | **RESOLVED** |
| **ISSUE-3.1-04** | Corporate Actions | MEDIUM | Share splits and cash dividends could distort position quantity and cost basis. | Implemented Ex-Date cash dividend credit and bonus/split position multiplier with proportional lot scaling. | **RESOLVED** |
| **ISSUE-3.1-05** | Audit Integration | MEDIUM | Backtest results were not recorded in the cryptographic audit ledger. | Added `record_backtest_run` to `AuditLedger` writing to SQLite WAL `audit_chain` with SHA-256 chaining. | **RESOLVED** |

---

## 2. Active Technical Constraints & Limitations

| Constraint ID | Component | Operational Limit | Mitigation / Future Path |
| :--- | :--- | :--- | :--- |
| **CONSTR-3.1-01** | Historical Data Feed | Full historical equity tick/minute data from NSE requires licensed data feed access. | Deterministic backtesting verified on curated benchmark fixtures; empirical validation across all Indian tickers blocked until licensed data ingestion is integrated. |
| **CONSTR-3.1-02** | Trading Lock | Real-money execution and broker routing strictly disabled. | `ENABLE_REAL_TRADING=false` hardcoded; system restricted to research and paper simulation. |
