# Phase 4.3 Independent Quantitative Correctness Audit

**Document Reference:** `docs/phase_4_3_quantitative_independent_audit.md`  
**Milestone:** Phase 4.3 — Gate E Acceptance  
**Date:** 2026-10-13  
**Auditor:** Role C (Quantitative Research Auditor)  
**Status:** PASS & INDEPENDENTLY REPRODUCED  

---

## 1. Executive Summary

Gate E requires independent mathematical verification of all financial indicators, return metrics, moving averages, risk statistics, and valuation formulas computed by `company_quant_engine` (`backend/app/analytics/company_quant.py`). Every displayed metric must possess a traceable formula, defined calculation window, and robust handling of division-by-zero or non-finite inputs.

---

## 2. Quantitative Metric Formulas & Audit Verification

### 1. Periodic Return Definitions
- **1-Month Return (21 trading bars):**
  $$R_{1M} = \left(\frac{P_t}{P_{t-21}} - 1.0\right) \times 100\%$$
- **6-Month Return (126 trading bars):**
  $$R_{6M} = \left(\frac{P_t}{P_{t-126}} - 1.0\right) \times 100\%$$
- **1-Year Return (Calendar-Aware Indian Market Window):**
  - If $N \ge 252$: $R_{1Y} = \left(\frac{P_t}{P_{t-252}} - 1.0\right) \times 100\%$
  - Else if $N \ge 245$: $R_{1Y} = \left(\frac{P_t}{P_{t-N}} - 1.0\right) \times 100\%$ (accommodates 245–250 Indian exchange sessions).
  - Else: `None` (`"Insufficient observations"`).
- **Independent Verification:** Tested on flat series ($R = 0.0\%$), ramp series, and boundary series ($N < 21 \implies R_{1M} = \text{None}$).

### 2. Annualized Volatility
- **Formula:**
  $$\sigma_{\text{ann}} = \sqrt{\frac{1}{K-1}\sum_{i=1}^K (r_i - \bar{r})^2} \times \sqrt{252} \times 100\%$$
  where $r_i = \frac{P_i}{P_{i-1}} - 1.0$, for $i \in [1, K]$, $K = \min(N, 252)$.
- **Requirement:** Requires at least $10$ daily return bars; returns `None` for shorter sequences.
- **Boundary Test:** For constant price array ($P_i = 100$), $\sigma_{\text{ann}} = 0.0\%$.

### 3. Maximum Drawdown (1-Year Peak-to-Trough)
- **Algorithm:**
  $$\text{Peak}_i = \max_{j \le i} P_j$$
  $$\text{Drawdown}_i = \frac{P_i - \text{Peak}_i}{\text{Peak}_i}$$
  $$\text{Max Drawdown} = \max_{i} |\text{Drawdown}_i| \times 100\%$$
- **Known-Answer Reproduction:**
  - Price sequence: `[100.0, 150.0, 105.0, 140.0, 80.0, 200.0, 170.0]`
  - Maximum peak prior to deepest trough: $150.0$, deepest subsequent trough: $80.0$.
  - Calculated $\text{MDD} = \frac{|80.0 - 150.0|}{150.0} \times 100\% = 46.67\%$.
  - QuantX Engine Output: **46.67%** (exact match).

### 4. Simple Moving Averages (SMA 20, SMA 50, SMA 200)
- **Warm-Up Bounds:**
  - $N < 20 \implies \text{SMA 20} = \text{None}$
  - $N < 50 \implies \text{SMA 50} = \text{None}$
  - $N < 200 \implies \text{SMA 200} = \text{None}$
- **Formula:** $\text{SMA}_W = \frac{1}{W} \sum_{k=0}^{W-1} P_{t-k}$.
- **Verification:** Evaluated on known arithmetic progressions $\sum_{i=1}^{20} i = 210 / 20 = 10.5$.

### 5. Benchmark Relative Strength (vs. Nifty 50)
- Excess Return: $\Delta R = R_{1M,\text{Stock}} - R_{1M,\text{NIFTY50}}$.
- Classification Rules:
  - $\Delta R > +3.0\% \implies \text{OUTPERFORMING}$
  - $\Delta R < -3.0\% \implies \text{UNDERPERFORMING}$
  - $-3.0\% \le \Delta R \le +3.0\% \implies \text{MARKET\_PERFORM}$

---

## 3. Fundamental Metrics & Denominator Safety

Division by zero or negative denominators (e.g., negative net worth or zero revenue) is handled without exceptions:
- **EBITDA Margin:** If $\text{Revenue} \le 0 \implies \text{None}$.
- **Debt-to-Equity:** If $\text{Net Worth} \le 0 \implies \text{None}$ (prevents meaningless negative ratios).
- **Return on Equity (ROE):** If $\text{Net Worth} \le 0 \implies \text{None}$.
- **Return on Capital Employed (ROCE):** If $\text{Capital Employed} \le 0 \implies \text{None}$.

No synthetic ratios are fabricated when inputs are absent.

---

## 4. Gate E Acceptance Decision

**GATE E STATUS: PASS**  
All mathematical formulas are independently verified against known-answer fixtures, boundary conditions, and real market histories with zero look-ahead bias and strict numerical safeguards.
