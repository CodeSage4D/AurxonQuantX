# Aurxon QuantX — Phase 4.5 Factor Data & Attribution Audit

## 1. Executive Summary & Verification Context
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.5 — Integrated Portfolio Validation & Release Readiness
- **Module:** `backend/app/analytics/factor_attribution.py`, `backend/app/schemas/portfolio_intelligence.py`

This audit examines whether factor outputs in **Aurxon QuantX** are computed dynamically from actual date-stamped bars and audited corporate filings or rely on illustrative calibration medians, enforcing strict provenance classification.

---

## 2. Factor Verification Matrix & Provenance Classification

| Factor Dimension | Empirical Formula | Primary Data Source | Fallback Reference Frame | Provenance Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Market Beta (β)** | $\frac{\text{Cov}(R_i, R_{bm})}{\text{Var}(R_{bm})}$ | Daily closing returns ($N \ge 20$) vs NIFTY 50 | Audited FY25-26 profile ($\beta = 1.08$ RELIANCE, $0.78$ TCS) | `COMPUTED_HISTORICAL` or `AUDITED_REFERENCE_PROFILE` |
| **Price Momentum** | $\frac{P_{t}}{P_{t-126}} - 1$ | 126-bar trailing daily closes | Trailing 6-month audited profile return | `COMPUTED_HISTORICAL` or `AUDITED_REFERENCE_PROFILE` |
| **Value (P/E Multiple)** | Harmonic mean of $E/P$ | EOD market quote PE ratio from store | Audited FY25 annual filing P/E | `COMPUTED_HISTORICAL` or `AUDITED_REFERENCE_PROFILE` |
| **Quality (ROE)** | $\frac{\text{PAT}}{\text{Net Worth}} \times 100$ | Audited quarterly filings from store | Audited FY25 balance sheet ROE | `AUDITED_REFERENCE_PROFILE (FY25-26)` |
| **Low Volatility** | $\text{StDev}(R_{1\dots N}) \times \sqrt{252}$ | 252 daily closing bars from store | Audited 1Y realized volatility | `COMPUTED_HISTORICAL` or `AUDITED_REFERENCE_PROFILE` |
| **Size** | $\log_{10}(\text{Market Cap in ₹ Cr})$ | `quote.current_price * quote.shares_outstanding` | Audited market capitalization tier | `COMPUTED_HISTORICAL` or `AUDITED_REFERENCE_PROFILE` |

---

## 3. Dynamic Resolution Architecture

In Phase 4.5, `FactorAttributionEngine` incorporates `resolve_security_factors(symbol)`:
1. **Dynamic Historical Inspection:** Inspects `MarketDataStore` for the presence of date-stamped bars ($N \ge 20$) and quotes.
2. **Empirical Calculation:**
   - 6-month momentum and 1-year annualized volatility are calculated directly from closing prices.
   - Systematic beta is computed via OLS regression against synchronized NIFTY 50 benchmark bars.
   - P/E and Size ($\log_{10}(\text{MCap})$) are calculated from stored quotes.
   - Tagged as: `COMPUTED_HISTORICAL`.
3. **Audited Profile Fallback:** When historical bars are offline or unconfigured, the engine draws upon `SECURITY_FACTOR_PROFILES` calibrated to audited FY25-26 filings.
   - Tagged as: `AUDITED_REFERENCE_PROFILE (FY25-26)`.
4. **Tile Metadata:** The dominant data origin is stamped onto each `FactorTile.data_origin` and displayed in the frontend user interface.

---

## 4. Benchmark Median Calibration Disclosures

To prevent misleading claims of real-time benchmark tick feeds:
- `BENCHMARK_FACTOR_BASELINES` values (Beta: 1.00, Momentum: 8.5%, PE: 22.5x, ROE: 16.5%, Volatility: 14.8%, Size: 12.2) are explicitly disclosed in `FactorTile.methodology_notes` as:
  > *"Illustrative benchmark medians calibrated to the NIFTY 50 empirical constituent distribution for FY25-26; not a live tick feed."*
- Unallocated cash buffers are insulated from factor exposure and dilute portfolio beta proportionally.
