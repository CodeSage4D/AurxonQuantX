# Aurxon QuantX — Phase 4.2 Quantitative Audit & Risk Review

**Product Identity:** Aurxon QuantX  
**Brand:** AURXON  
**Audit Date:** 2026-10-13  
**Auditor:** Principal Model Risk Auditor & Quantitative Financial Engineer  
**Baseline Commit:** `7ad29f8` | **Target Milestone:** Phase 4.2  

---

## 1. Quantitative Analytics Mathematical Audit

### 1.1 Trading Calendar & Annual Return Periods
- **1-Month Return ($R_{1M}$):** Evaluated over 21 trading bars.
  $$R_{1M} = \left(\frac{P_t}{P_{t-21}} - 1\right) \times 100\%$$
- **6-Month Return ($R_{6M}$):** Evaluated over 126 trading bars.
  $$R_{6M} = \left(\frac{P_t}{P_{t-126}} - 1\right) \times 100\%$$
- **1-Year Return ($R_{1Y}$):** In India, an annual trading calendar contains 245–250 sessions. The engine evaluates:
  $$R_{1Y} = \begin{cases}
  \left(\frac{P_t}{P_{t-252}} - 1\right) \times 100\% & \text{if } N \ge 252 \\
  \left(\frac{P_t}{P_0} - 1\right) \times 100\% & \text{if } 245 \le N < 252 \\
  \text{None} & \text{if } N < 245
  \end{cases}$$

### 1.2 Annualized Volatility
Sample variance is computed with Bessel's correction ($N-1$ degrees of freedom) over trailing window $W = \min(N, 252)$:
$$s^2 = \frac{1}{k - 1} \sum_{i=1}^k (r_i - \bar{r})^2$$
$$\sigma_{ann} = \sqrt{s^2} \times \sqrt{252} \times 100\%$$
*Sample Count Invariant:* Requires $\ge 10$ valid daily returns. If $k < 10$, $\sigma_{ann} = \text{None}$.

### 1.3 Maximum Drawdown Peak-to-Trough
$$\text{Peak}_t = \max_{0 \le \tau \le t} (P_\tau)$$
$$\text{Drawdown}_t = \frac{P_t - \text{Peak}_t}{\text{Peak}_t}$$
$$\text{MDD} = \max_{t} |\text{Drawdown}_t| \times 100\%$$

### 1.4 Moving Averages & Trend Regime
- **SMA 20:** Sum of trailing 20 closes / 20. Requires $N \ge 20$.
- **SMA 50:** Sum of trailing 50 closes / 50. Requires $N \ge 50$.
- **SMA 200:** Sum of trailing 200 closes / 200. Requires $N \ge 200$.
- **Regime Logic:**
  - `STRONG_BULLISH`: Close > SMA 20 > SMA 50
  - `STRONG_BEARISH`: Close < SMA 20 < SMA 50
  - `MILD_BULLISH`: Close > SMA 50
  - `CONSOLIDATION_NEUTRAL`: Other configurations

---

## 2. Defensive Accounting & Boundary Guards

| Risk Hazard | Mathematical Condition | System Guard | Audit Result |
| :--- | :--- | :--- | :---: |
| **Zero / Negative Revenue** | $\text{Revenue} \le 0$ | Returns `None` for margins | **PASSED** (No ZeroDivisionError) |
| **Negative Net Worth** | $\text{Net Worth} \le 0$ | Returns `None` for D/E and ROE | **PASSED** (No misleading positive ROE) |
| **Depleted Capital Employed** | $\text{Debt} + \text{Net Worth} \le 0$ | Returns `None` for RoCE | **PASSED** |
| **Missing Price Bars** | $N < 2$ | Returns all `None`, regime `INSUFFICIENT_DATA` | **PASSED** |
| **Look-Ahead Bias** | Reverse-ordered inputs | Sorts strictly by `trading_date` ascending | **PASSED** (Chronological invariant) |

---

## 3. Paper-Trading Risk Controls & Fail-Closed Safety

All paper-trading risk gates operate independently of the research engine and enforce **fail-closed** security:

1. **Hard Real-Trading Invariant:** `ENABLE_REAL_TRADING = false` strictly enforced across all routes.
2. **Maximum 1-Year Drawdown Ceiling:** Capped at **30.0%**. When historical MDD exceeds 30.0%, the paper trading ticket is vetoed with `"1-Year maximum drawdown (X.X%) exceeds safety ceiling (30.0%)"`.
3. **Missing Data Fail-Closed Guard:** If price history is absent or bars are insufficient to compute 1-year drawdown, the ticket is vetoed with `"Insufficient historical price bars to compute 1-Year maximum drawdown risk limit"`.
4. **Stale Market Price Guard:** Stale quotes (`STALE_WARNING`) trigger immediate order vetoes.
5. **Position Allocation Ceiling:** Single-equity virtual position sizing is capped at **15.0%** of portfolio equity.
6. **Cash Conservation:** Double-entry ledger accounting strictly accounts for virtual cash, brokerage, exchange fees, SEBI charges, Stamp Duty, and STT.
