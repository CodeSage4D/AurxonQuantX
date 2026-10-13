# AURXONQuant — Phase 3, Stage 1 Starting Baseline
**Project:** AURXONQuant  
**Milestone:** Phase 3, Stage 1 — Deterministic Backtesting Engine  
**Date:** 2026-10-13  
**Repository Path:** `/home/karann/Documents/AURXONQuant`  
**Starting Commit:** `738eed4`  
**Branch:** `main` (clean working tree)  

---

## 1. Verified Starting State

1. **Git Commit & Tree:**
   - Commit: `738eed4` (`feat(preflight): Phase 3 Mandatory Pre-Flight Gate, AMFI 8-col live feed & prospectus versioning`)
   - Working Tree: 100% clean, zero uncommitted or untracked changes.
2. **Backend Regression Status:**
   - Pytest execution: **80 passed out of 80 tests in 1.89s** (`PYTHONPATH=backend .venv/bin/pytest backend/tests/ -v`).
   - Zero test failures, zero regressions across earlier milestones (Phase 0, 1, 1.5, 2, 2.1, 2.2).
3. **Frontend Build Status:**
   - Production Vite bundle: **Clean build in 2.17s** (`npm run build`).
   - Zero TypeScript compiler diagnostics.
4. **Prerequisites & Capabilities In Place:**
   - Typed financial semantics (`MetricStatus`, `TypedFinancialMetric`, `DataFreshnessRecord`, `FieldLineageRecord`).
   - Cryptographic SHA-256 hash-chained audit ledger (`audit_ledger`).
   - AMFI statutory mutual fund NAV connector (live 8-col & 6-col parsing with 14,374 schemes, cached fallback).
   - IPO prospectus intelligence and peer valuation engine.
   - Loopback-only service binding (`127.0.0.1`) and trading hard-lock (`ENABLE_REAL_TRADING=false`).

---

## 2. Objective for Stage 1

Implement a deterministic, reproducible event-driven backtesting engine for Indian-market strategies.
- Define a typed historical-market-data contract for equity OHLCV series.
- Implement strictly lagged signal generation ($T$) and next-bar execution ($T+1$) to eliminate lookahead bias.
- Model transparent, configurable Indian transaction cost schedules (STT, exchange turnover fees, GST, stamp duty, SEBI turnover fees, slippage).
- Compute robust portfolio accounting (gross vs net returns, drawdowns, Sharpe, Sortino, win rates).
- Record all backtest runs into the auditable SHA-256 hash-chain ledger.
