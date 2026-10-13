# Aurxon QuantX — Phase 4.4 Factor Attribution Methodology

## 1. Overview & System Identity
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.4 — Workstream C: Factor Attribution
- **Module:** `backend/app/analytics/factor_attribution.py`, `backend/app/schemas/portfolio_intelligence.py`

This document defines the mathematical formulation, input variables, benchmark reference frames, and epistemic boundaries governing portfolio factor attribution in **Aurxon QuantX**.

---

## 2. Factor Definitions & Input Variables

Aurxon QuantX decomposes portfolio equity exposures across six standardized quantitative equity factors:

### 2.1 Market Beta (Systematic Exposure)
- **Definition:** Sensitivity of portfolio security returns relative to NIFTY 50 benchmark returns.
- **Formula:** $\beta_i = \frac{\text{Cov}(R_i, R_m)}{\text{Var}(R_m)}$
- **Inputs:** 252 daily log returns of security and NIFTY 50.
- **Benchmark Median:** 1.00.
- **Tilt Status:**
  - $\beta_p > 1.05$: High Beta (Aggressive cyclical exposure)
  - $\beta_p < 0.95$: Low Beta (Defensive positioning)
  - Otherwise: Neutral

### 2.2 Momentum (12M - 1M Price Performance)
- **Definition:** Standard intermediate-term momentum (Jegadeesh & Titman), computing 12-month return skipping the most recent 1-month reversal window:
  $$\text{Mom}_i = \frac{P_{t-21}}{P_{t-252}} - 1$$
- **Inputs:** Daily close prices from $t-252$ to $t-21$.
- **Benchmark Median:** 12.5% (approximate median 1Y NIFTY 50 return).
- **Tilt Status:**
  - $\text{Mom}_p > \text{BM} + 5.0\%$: Momentum Positive Tilt
  - $\text{Mom}_p < \text{BM} - 5.0\%$: Value / Reversal Tilt
  - Otherwise: Neutral

### 2.3 Value (Earnings Yield / P/E Reciprocal)
- **Definition:** Inverse Price-to-Earnings ratio ($E/P$), reflecting earnings yield discount:
  $$\text{Earnings Yield}_i = \frac{\text{Trailing 12M EPS}_i}{P_i}$$
- **Inputs:** Trailing audited diluted EPS from annual/quarterly filings and latest closing price.
- **Benchmark Median:** 4.35% (corresponding to NIFTY 50 P/E of ~23.0x).
- **Tilt Status:**
  - $E/P_p > 5.25\%$: Deep Value Tilt
  - $E/P_p < 3.50\%$: Premium Growth Tilt
  - Otherwise: Balanced Valuation

### 2.4 Quality (Return on Equity)
- **Definition:** Efficiency of net capital allocation:
  $$\text{ROE}_i = \frac{\text{Trailing 12M PAT}_i}{\text{Total Shareholders Equity}_i}$$
- **Inputs:** Audited Consolidated Profit After Tax and Book Value of Equity.
- **Benchmark Median:** 15.0% (NIFTY 50 constituent median).
- **Tilt Status:**
  - $\text{ROE}_p > 18.0\%$: High Quality Tilt
  - $\text{ROE}_p < 12.0\%$: Low Quality / Capital-Intensive Tilt
  - Otherwise: Neutral

### 2.5 Low Volatility (Annualized Standard Deviation)
- **Definition:** Dispersion of daily returns over the preceding 252 sessions:
  $$\sigma_i = \text{StDev}(R_{i, 1\dots 252}) \times \sqrt{252}$$
- **Inputs:** 252 daily trading bar closes.
- **Benchmark Median:** 16.5% (NIFTY 50 realized volatility baseline).
- **Tilt Status:**
  - $\sigma_p < 14.5\%$: Low Volatility Advantage
  - $\sigma_p > 19.0\%$: High Volatility Speculative Tilt
  - Otherwise: Neutral

### 2.6 Size (Market Capitalization)
- **Definition:** Natural logarithm of market capitalization in INR Crores:
  $$\text{Size Score}_i = \ln(\text{Market Cap in ₹ Cr})$$
- **Inputs:** Free-float market capitalization.
- **Benchmark Median:** 11.5 (~₹1,00,000 Cr median NIFTY 50 constituent).
- **Tilt Status:**
  - $\text{Size}_p > 12.0$: Mega-Cap Weighted
  - $\text{Size}_p < 10.5$: Mid/Small-Cap Weighted
  - Otherwise: Large-Cap Neutral

---

## 3. Aggregation & Weighting Math

Portfolio factor scores are derived through holdings-weighted aggregation over verified priced constituents:
$$S_{p, f} = \sum_{i=1}^M w_i \times S_{i, f}$$
Where:
$$w_i = \frac{\text{Market Value}_i}{\sum_{j=1}^M \text{Market Value}_j}$$
Unpriced or unverified holdings are excluded from the denominator weight to prevent artificial dilution.

---

## 4. Epistemic Principles & Disclaimers

1. **Correlation vs Causation Distinction:** Factor tilts describe descriptive historical regression associations, NOT guarantees of future alpha generation or causal economic certainty.
2. **Look-Ahead & Survivorship Bias Prevention:** All factor metrics are computed strictly using historical trailing disclosures available at or prior to observation date $T$.
3. **No Phantom Factors:** If historical financial statements or price bars are unavailable for a constituent, its factor score is marked `None` / `UNAVAILABLE` rather than estimated or imputed.
4. **Empty Portfolio Safety:** An empty portfolio reports `is_available = False` across all factors with clear diagnostic notices.
