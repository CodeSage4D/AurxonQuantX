# AURXONQuant — Phase 4.1 Paper-Trading Risk Policy Review

**Audit Date:** 2026-10-13  
**Auditor:** Principal Risk Architect & Quantitative Systems Auditor  
**Baseline Commit:** `2d9b533` | **Target Milestone:** Phase 4.1  
**Scope:** Review and tightening of paper trading safety gates, drawdown ceilings, position allocation limits, and fail-closed controls.

---

## 1. Absolute Real-Trading Guard

**Hard Safety Invariant:**  
Real-money trading and live broker API order routing remain strictly disabled across all modules.
```python
ENABLE_REAL_TRADING = False
```
Any simulated ticket emitted by research or backtesting is explicitly stamped with:
`"RESEARCH & SIMULATION ONLY. Deterministic financial calculations. No live capital execution."`

---

## 2. Drawdown Ceiling Review & Tightening

### 2.1 Deficiency of Prior 50% Universal Ceiling
A universal 50% maximum drawdown ceiling is unacceptable for institutional and prudent quantitative research:
- A 50% drawdown requires a subsequent 100% gain merely to break even.
- In volatile emerging markets, high drawdown indicates structural capital impairment or distressed equity regimes.

### 2.2 Implemented Phase 4.1 Risk Thresholds
1. **Maximum Safe 1-Year Drawdown Ceiling:**
   $$\text{MAX\_SAFE\_DRAWDOWN\_PCT} = 30.0\%$$
   Any company exhibiting an annualized maximum drawdown $> 30.0\%$ is immediately disqualified from paper trading consideration.
2. **Maximum Single-Stock Allocation Cap:**
   $$\text{MAX\_RECOMMENDED\_ALLOCATION\_PCT} \le 15.0\%$$
   No single equity position recommendation may exceed 15% of the virtual portfolio cash equity ledger.
3. **Daily Loss Risk Limit:**
   Exceeding a 5% intraday portfolio loss triggers immediate paper-trading order halt.
4. **Emergency Kill-Switch:**
   System operators can activate the persistent kill switch via `POST /api/v1/paper-trading/kill-switch`, immediately cancelling active limit orders and vetoing new submissions.

---

## 3. Fail-Closed Safety Contracts

Paper trading eligibility tickets strictly enforce fail-closed invariants:

| Condition | System Action | Veto Reason Logged |
| :--- | :---: | :--- |
| **Missing Price Bars** | VETO | `"Insufficient historical price bars to compute 1-Year maximum drawdown risk limit"` |
| **Drawdown $> 30\%$** | VETO | `"1-Year maximum drawdown (X.X%) exceeds safety ceiling (30.0%)"` |
| **Stale Price Warning** | VETO | `"Market price is flagged as STALE_WARNING"` |
| **Unlisted / Delisted** | VETO | `"Instrument listing status is NOT_LISTED / SUSPENDED"` |
| **Zero / Negative Price** | VETO | `"No valid current market price available"` |
| **Insufficient Cash** | VETO | `"Order rejected: Required virtual capital exceeds available cash balance"` |

---

## 4. Test Verification Summary

Automated tests in `backend/tests/test_phase_4_1_live_providers.py` and `backend/tests/test_phase_3_stage_2_paper_trading.py` verify:
1. `test_paper_trading_risk_gate_drawdown_limit_enforcement`: Injected 38.5% drawdown triggers immediate veto with `"drawdown exceeds safety ceiling"`.
2. `test_paper_trading_risk_gate_fails_closed_on_missing_drawdown`: Null drawdown triggers fail-closed veto with `"insufficient historical price bars"`.
3. `test_paper_trading_cash_conservation_buy_and_sell`: Virtual cash conservation verified over buy/sell sequences including Indian statutory costs (STT, Stamp Duty, GST, Exchange charges).
4. `test_paper_trading_kill_switch_veto`: Kill-switch activation verified to block simulated execution.
