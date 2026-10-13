# AURXONQuant — Phase 4.1 Quantitative Audit Report

**Audit Date:** 2026-10-13  
**Auditor:** Principal Quantitative Financial Engineer & Model Risk Auditor  
**Baseline Commit:** `2d9b533` | **Target Milestone:** Phase 4.1  
**Scope:** Mathematical formulas, trading calendar conventions, edge case robustness, zero-division guards, and look-ahead bias prevention.

---

## 1. Mathematical Framework & Implementation Verification

### 1.1 Trading Calendar & Period Returns

Returns are calculated over canonical Indian trading session bar counts:
- **1-Month Return ($R_{1M}$):** 21 trading bars.
  $$R_{1M} = \left(\frac{P_t}{P_{t-21}} - 1\right) \times 100\%$$
- **6-Month Return ($R_{6M}$):** 126 trading bars.
  $$R_{6M} = \left(\frac{P_t}{P_{t-126}} - 1\right) \times 100\%$$
- **1-Year Return ($R_{1Y}$):** 252 trading bars.
  $$R_{1Y} = \left(\frac{P_t}{P_{t-252}} - 1\right) \times 100\%$$

**Boundary Behavior:** If the series contains fewer than the required bars (e.g. $N < 21$ for 1M), the metric returns `None` rather than extrapolating or guessing.

### 1.2 Volatility Annualization
Daily simple returns are computed across the trailing evaluation window $W = \min(N, 252)$:
$$r_i = \frac{P_i}{P_{i-1}} - 1$$
Sample variance is computed with Bessel's correction ($N-1$ degrees of freedom):
$$s^2 = \frac{1}{k - 1} \sum_{i=1}^k (r_i - \bar{r})^2$$
Annualized volatility assumes 252 trading sessions per Indian market year:
$$\sigma_{ann} = \sqrt{s^2} \times \sqrt{252} \times 100\%$$

**Sample Count Requirement:** Volatility requires at least 10 valid daily returns. If $k < 10$, $\sigma_{ann} = \text{None}$.

### 1.3 Maximum Drawdown (MDD)
The peak-to-trough decline is computed chronologically over the price series:
$$\text{Peak}_t = \max_{0 \le \tau \le t} (P_\tau)$$
$$\text{Drawdown}_t = \frac{P_t - \text{Peak}_t}{\text{Peak}_t}$$
$$\text{MDD} = \max_{t} |\text{Drawdown}_t| \times 100\%$$

**Audit Finding:** Peak updates strictly sequentially. When prices achieve a new high, the peak adjusts upward, correctly resetting drawdown measurements.

### 1.4 Moving Average Warm-Up Periods
- **SMA 20:** Requires $\ge 20$ bars. If $N < 20$, returns `None`.
- **SMA 50:** Requires $\ge 50$ bars. If $N < 50$, returns `None`.
- **SMA 200:** Requires $\ge 200$ bars. If $N < 200$, returns `None`.

### 1.5 Benchmark Relative Strength vs. NIFTY50
Excess return spread over 1 month ($R_{1M, asset} - R_{1M, NIFTY50}$):
- Spread $> +3.0\% \implies$ `OUTPERFORMING (+X.X% vs Nifty)`
- Spread $< -3.0\% \implies$ `UNDERPERFORMING (-X.X% vs Nifty)`
- $-3.0\% \le \text{Spread} \le +3.0\% \implies$ `MARKET_PERFORM (+/-X.X% vs Nifty)`

---

## 2. Defensive Accounting & Zero-Division Guards

Financial statement ratios are audited against dangerous mathematical edge cases:

| Metric | Formula | Edge Case / Hazard | Implemented Safeguard |
| :--- | :--- | :--- | :--- |
| **EBITDA Margin** | $\frac{\text{EBITDA}}{\text{Revenue}} \times 100$ | Revenue $\le 0$ | Returns `None` (avoids ZeroDivisionError) |
| **PAT Margin** | $\frac{\text{PAT}}{\text{Revenue}} \times 100$ | Revenue $\le 0$ | Returns `None` |
| **Debt to Equity** | $\frac{\text{Total Debt}}{\text{Net Worth}}$ | Net Worth $\le 0$ (Insolvent) | Returns `None` (prevents meaningless negative D/E) |
| **ROE** | $\frac{\text{PAT}}{\text{Net Worth}} \times 100$ | Net Worth $\le 0$ | Returns `None` (prevents false positive ROE if both negative) |
| **RoCE** | $\frac{\text{EBITDA}}{\text{Debt} + \text{Net Worth}} \times 100$ | Capital Employed $\le 0$ | Returns `None` |
| **YoY Rev Growth** | $\left(\frac{\text{Rev}_t}{\text{Rev}_{t-1}} - 1\right) \times 100$ | Prior Revenue $\le 0$ | Returns `None` |

---

## 3. Look-Ahead Bias Audit

1. **Chronological Invariant:** All calculations in `CompanyQuantEngine` sort incoming bars strictly by `trading_date` ascending before evaluating rolling windows.
2. **Lagged Execution Contract:** As verified in Phase 3 Stage 1, order fills in backtesting and paper simulation occur strictly at $t+1$ bar open/close after signal generation at $t$. No future bar prices are referenced.
3. **Point-in-Time Disclosures:** Filing data is aligned with historical announcement dates rather than retroactive restatements.
