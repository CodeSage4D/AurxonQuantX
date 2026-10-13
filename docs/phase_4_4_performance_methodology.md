# Aurxon QuantX — Phase 4.4 Portfolio Performance Methodology

## 1. Overview & System Identity
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.4 — Workstream B: Portfolio Performance
- **Module:** `backend/app/trading/portfolio_analytics.py`, `backend/app/schemas/portfolio_intelligence.py`

This document details the quantitative methods, geometric compounding, numerical solvers, and benchmark-relative tracking error formulations used in **Aurxon QuantX**.

---

## 2. Return Measurement Methodologies

### 2.1 Absolute and Percentage Returns
- **Absolute Return (INR):**
  $$\text{Absolute Return} = \text{Current Equity} - \text{Initial Capital}$$
- **Total Percentage Return:**
  $$R_{total} = \frac{\text{Current Equity} - \text{Initial Capital}}{\text{Initial Capital}} \times 100$$

### 2.2 Time-Weighted Return (TWR)
Time-Weighted Return eliminates the distortion caused by external cash deposits or withdrawals, reflecting purely the investment manager's asset allocation performance:
$$R_{TWR} = \left[ \prod_{t=1}^T \left( 1 + R_t \right) \right] - 1$$
Where for sub-period $t$:
$$R_t = \frac{V_{end, t} - CF_t}{V_{start, t}} - 1$$
- $V_{start, t}$: Portfolio equity at start of sub-period $t$.
- $V_{end, t}$: Portfolio equity at end of sub-period $t$.
- $CF_t$: Net external cash flow occurring during sub-period $t$.
If no external cash flows exist, $R_{TWR} \equiv R_{total}$.

### 2.3 Money-Weighted Return (MWR / Internal Rate of Return)
When external cash flows occur with specific calendar timestamps $(t_0, t_1, \dots, t_K)$, the annualized Money-Weighted Return $r_{MWR}$ is defined as the discount rate that sets the Net Present Value (NPV) of all cash flows plus terminal equity to zero:
$$\text{NPV}(r) = -CF_0 + \sum_{k=1}^K \frac{-CF_k}{(1 + r)^{t_k - t_0}} + \frac{V_{terminal}}{(1 + r)^{t_T - t_0}} = 0$$

#### Numerical Solver Implementation:
Aurxon QuantX uses a robust **Bisection Root-Finding Algorithm**:
1. Search interval bounded between $r_{low} = -99\%$ and $r_{high} = +500\%$.
2. Iterates up to 100 iterations until $|\text{NPV}(r)| < 10^{-5}$ or $|r_{high} - r_{low}| < 10^{-6}$.
3. If cash flows do not span $>3$ days or have insufficient directional variance, the metric is explicitly qualified as requiring further observation history.

---

## 3. Volatility, Drawdown & Risk Ratios

### 3.1 Annualized Volatility
Given daily returns $R_1, R_2, \dots, R_N$:
$$\bar{R} = \frac{1}{N}\sum_{i=1}^N R_i$$
$$\sigma_{daily} = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (R_i - \bar{R})^2}$$
Annualized using the official Indian equity market calendar constant (252 sessions):
$$\sigma_{annual} = \sigma_{daily} \times \sqrt{252} \times 100\%$$

### 3.2 Peak-to-Trough Maximum Drawdown
For daily equity curve $E_1, E_2, \dots, E_T$:
$$\text{Peak}_t = \max_{1 \le \tau \le t} E_\tau$$
$$\text{Drawdown}_t = \frac{E_t - \text{Peak}_t}{\text{Peak}_t}$$
$$\text{Max Drawdown} = \left| \min_{1 \le t \le T} \text{Drawdown}_t \right| \times 100\%$$

### 3.3 Risk-Adjusted Ratios
- **Sharpe Ratio:**
  $$\text{Sharpe} = \frac{R_{p, annual} - R_f}{\sigma_{p, annual}}$$
  Where $R_f = 6.5\%$ (calibrated to the Reserve Bank of India 10-year G-Sec yield baseline).
- **Sortino Ratio:**
  $$\text{Sortino} = \frac{R_{p, annual} - R_f}{\sigma_{downside} \times \sqrt{252}}$$
  Where downside deviation considers only returns below $0$.

---

## 4. Benchmark Alignment & Tracking Error

### 4.1 Benchmark Selection
- Primary Benchmark: **NIFTY 50** (`^NSEI` / `NIFTY50.NS`).
- Secondary Benchmarks: NIFTY Next 50, NIFTY Bank, NIFTY IT.

### 4.2 Tracking Error
Tracking error measures the annualized standard deviation of active excess returns:
$$D_t = R_{p, t} - R_{b, t}$$
$$\text{TE}_{annual} = \sigma(D) \times \sqrt{252} \times 100\%$$

### 4.3 Information Ratio
$$\text{IR} = \frac{\bar{R}_p - \bar{R}_b}{\text{TE}_{annual}}$$

### 4.4 Portfolio Beta & Jensen's Alpha
$$\beta_p = \frac{\text{Cov}(R_p, R_b)}{\text{Var}(R_b)}$$
$$\alpha_p = R_{p, annual} - \left[ R_f + \beta_p \times (R_{b, annual} - R_f) \right]$$

---

## 5. Disclosures, Constraints & Caveats
1. **Date-Alignment Guard:** Portfolio returns and benchmark returns must share identical trading session calendars. Non-trading exchange holidays (Diwali, Independence Day) are synchronized to eliminate spurious tracking error.
2. **Zero-Volatility Guard:** If price history exhibits zero variance (e.g., all bars equal), volatility is clamped to $0.0\%$ with diagnostic caveats.
3. **Currency Alignment:** All Indian portfolios, benchmark series, and cash flows are strictly evaluated in INR.
