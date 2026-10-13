# Aurxon QuantX — Phase 4.4 Stress Testing & Risk Scenario Methodology

## 1. Overview & System Identity
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.4 — Workstream E: Risk and Stress Testing
- **Module:** `backend/app/trading/stress_testing.py`, `backend/app/schemas/portfolio_intelligence.py`

This document details the stress testing scenarios, historical shocks, Parametric Value-at-Risk (VaR), and downside risk evaluations implemented in **Aurxon QuantX**.

---

## 2. Hypothetical Stress Scenarios

All scenario simulations are deterministic, reproducible stress tests designed to measure capital impairment under severe historical or synthetic market distress. They are explicitly disclosed as **hypothetical stress simulations, not forecasts**.

### 2.1 Broad Market Shocks (Beta-Scaled)
- **Market Crash -10% (Correction):**
  - Systematic index shock: $\Delta R_m = -10.0\%$.
  - Asset shock: $\Delta R_i = \beta_i \times (-10.0\%)$.
- **Severe Market Crash -20% (Bear Market Regime):**
  - Systematic index shock: $\Delta R_m = -20.0\%$.
  - Asset shock: $\Delta R_i = \beta_i \times (-20.0\%)$.
  - Captures non-linear systemic margin contractions and liquidity distress.

### 2.2 Sector-Specific Devaluation
- **Technology Sector Shock (-15%):**
  - Affects IT constituents (`TCS`, `INFY`, `WIPRO`, `HCLTECH`, `TECHM`) with $-15.0\%$ shock.
  - Non-IT equities remain unshocked, isolating sector concentration vulnerability.
- **Banking & Financial Services Shock (-15%):**
  - Affects BFSI constituents (`HDFCBANK`, `ICICIBANK`, `SBIN`, `KOTAKBANK`, `AXISBANK`) with $-15.0\%$ shock.
  - Assesses systemic credit contraction impact.

### 2.3 Individual Holding Distress
- **Single Holding Black Swan (-25%):**
  - The portfolio's single largest holding by market value suffers an idiosyncratic $-25.0\%$ shock (e.g., regulatory ban, governance scandal, massive earnings miss).
  - Isolates portfolio vulnerability to single-stock concentration.

### 2.4 Volatility Surge & Liquidity Haircut
- **Volatility Spike (+50%):**
  - Simulates a 50% expansion in underlying equity volatility ($\sigma_{new} = 1.5 \times \sigma_{old}$), expanding parametric VaR bounds and risk margins.
- **Liquidity Deterioration (Haircut):**
  - Simulates sudden market illiquidity during rapid unwind: applies a 3.0% immediate liquidation haircut to all active equity holdings while leaving virtual cash intact.

---

## 3. Mathematical Value-at-Risk (VaR) Formulation

Aurxon QuantX computes Parametric 1-Day Value-at-Risk using standard normal quantile multipliers:

$$\text{VaR}_{95\%} = z_{0.95} \times \sigma_{portfolio, daily} \approx 1.645 \times \sigma_{p, daily}$$
$$\text{VaR}_{99\%} = z_{0.99} \times \sigma_{portfolio, daily} \approx 2.326 \times \sigma_{p, daily}$$

Where daily portfolio volatility is estimated from holdings weights and annualized volatility:
$$\sigma_{p, daily} = \frac{\sigma_{p, annual}}{\sqrt{252}}$$

In stress scenario evaluations, $\text{VaR}$ bounds expand dynamically to reflect stressed volatilities or concentrated holding impairments.

---

## 4. Post-Stress Evaluation & Constraint Auditing

For each scenario $S$:
$$\text{Stressed Equity}_S = \text{Cash} + \sum_{i=1}^N \left( \text{Market Value}_i \times (1 + \Delta R_{i, S}) \right)$$
$$\text{Estimated Loss (INR)}_S = \text{Baseline Equity} - \text{Stressed Equity}_S$$
$$\text{Stressed Loss \%}_S = \frac{\text{Estimated Loss}_S}{\text{Baseline Equity}} \times 100\%$$

### Constraint Auditing
The engine checks whether the stressed equity breaches system risk parameters:
- **Drawdown Circuit Breakers:** Flags `DRAWDOWN_BREACH` if $\text{Stressed Loss \%} > 30\%$.
- **Cash Solvency:** Verifies that virtual cash remains non-negative.
- **Concentration Distortion:** Identifies if unshocked holdings artificially exceed concentration thresholds as a percentage of diminished equity.

---

## 5. Epistemic Principles & Disclaimers
1. **Diversification Disclaimer:** Diversification mitigates idiosyncratic risk but does NOT eliminate systemic market losses.
2. **Non-Forecast Labeling:** All stress metrics carry the explicit banner:
   *"Hypothetical stress scenario for risk visualization only; not a performance forecast."*
