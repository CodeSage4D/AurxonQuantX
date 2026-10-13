# AURXON Financial Validation & Mathematical Rigor Report

**Status:** Hardened Specification  
**Version:** 1.0.0 (Phase 1.5 Gate)  
**Standard:** 100% Deterministic Reproducibility (Zero LLM Fabrication)  

---

## 1. Mathematical Formula Inventory

### 1.1 Benjamin Graham Fair Value Threshold
- **Formula:**
  $$\text{Graham Number} = \sqrt{22.5 \times \text{EPS} \times \text{BVPS}}$$
- **Units:** INR per share.
- **Assumptions:** Based on Benjamin Graham's maximum conservative threshold (P/E $\le 15.0$ and P/B $\le 1.5$, where $15 \times 1.5 = 22.5$).
- **Boundary Handling:** If $\text{EPS} \le 0$ or $\text{BVPS} \le 0$, the function deterministically returns `0.0` (non-applicable).

---

### 1.2 Two-Stage Discounted Cash Flow (DCF) Model
- **Enterprise Cash Flow Specification:**
  $$PV = \sum_{t=1}^{5} \frac{FCF_0 \times (1 + g_1)^t}{(1 + r)^t} + \sum_{t=6}^{10} \frac{FCF_5 \times (1 + g_2)^{t-5}}{(1 + r)^t} + \frac{FCF_{10} \times (1 + g_{term})}{(r - g_{term}) \times (1 + r)^{10}}$$
- **Per-Share Value:**
  $$\text{Intrinsic Equity Value Per Share} = \frac{PV + \text{Cash} - \text{Total Debt}}{\text{Diluted Shares Outstanding}}$$
- **Baseline Indian Parameters:**
  - $r$ (Cost of Equity / WACC): $11.5\%$ (Risk-free 6.8% 10Y G-Sec + 4.7% Equity Risk Premium).
  - $g_1$ (Stage 1 Growth): $12.0\%$ (Initial 5-year compounding).
  - $g_2$ (Stage 2 Transition): $8.0\%$ (Years 6-10 fade).
  - $g_{term}$ (Perpetual Growth): $4.5\%$ (Long-term Indian real GDP + inflation anchor).
- **Boundary Handling:** If $r \le g_{term}$, a minimum spread of $2.5\%$ is enforced to prevent denominator singularity.

#### 3x3 Sensitivity Matrix Grid
The engine evaluates intrinsic value across a 2-dimensional grid:
- **Discount Rates ($r$):** $10.5\%$, $11.5\%$, $12.5\%$
- **Terminal Growth Rates ($g_{term}$):** $3.5\%$, $4.5\%$, $5.5\%$

---

### 1.3 Sector-Specific Exclusion: Commercial Banks & NBFCs
- **Problem Statement:** Applying industrial solvency (Altman Z-Score) or enterprise Free Cash Flow (FCF) to commercial banks (`HDFCBANK`, `ICICIBANK`, `SBIN`) produces false insolvencies because bank deposits are legally classified as liabilities, loans are assets, and traditional working capital is zero.
- **Implemented Guard:**
  - When `is_financial_institution == True`, the engine suppresses Altman Z-Score (`altman_z_score = None`) and enterprise DCF (`fair_value_dcf = None`).
  - An explicit `sector_exclusion_notes` disclaimer is appended to the audit record.
  - Valuation is anchored to Graham Number, Price-to-Book (P/B), and regulatory capital metrics (CRAR / NPA).

---

### 1.4 Piotroski F-Score (9-Signal Fundamental Accounting)
- **Signal 1:** Positive Net Income ($+1$)
- **Signal 2:** Positive Operating Cash Flow ($+1$)
- **Signal 3:** ROA Improvement ($+1$)
- **Signal 4:** Cash Flow from Operations > Net Income ($+1$)
- **Signal 5:** Lower Long-Term Debt / Decreased Leverage ($+1$)
- **Signal 6:** Higher Current Ratio ($+1$)
- **Signal 7:** No Dilution / Shares Unchanged or Reduced ($+1$)
- **Signal 8:** Higher Gross Margin ($+1$)
- **Signal 9:** Higher Asset Turnover ($+1$)
- **Range:** Integer $\in [0, 9]$. Companies scoring $\ge 7$ represent high accounting quality.

---

### 1.5 Altman Z-Score (Solvency)
- **Formula:**
  $$Z = 1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 0.999 X_5$$
  Where $X_1 = \frac{\text{Working Capital}}{\text{Total Assets}}$, $X_2 = \frac{\text{Retained Earnings}}{\text{Total Assets}}$, $X_3 = \frac{\text{EBIT}}{\text{Total Assets}}$, $X_4 = \frac{\text{Market Cap}}{\text{Total Liabilities}}$, $X_5 = \frac{\text{Sales}}{\text{Total Assets}}$.
- **Safe Zone:** $Z > 2.99$. **Grey Zone:** $1.81 \le Z \le 2.99$. **Distress Zone:** $Z < 1.81$.
