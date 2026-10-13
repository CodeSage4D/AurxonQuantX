# AURXON Mutual Fund & ETF Quantitative Research Specification

**Milestone:** Phase 2  
**Status:** Hardened Specification  
**Version:** 1.0.0  

---

## 1. Principles of Fund Research

1. **Category-Appropriate Comparison:** Schemes are strictly benchmarked within identical SEBI categories (e.g. Large Cap vs Nifty 100 TRI; Flexi Cap vs Nifty 500 TRI). Small cap funds are never compared directly against large cap funds without category adjustment.
2. **Direct vs Regular Plan Transparency:** Direct plans bypass broker distribution commissions. The 10-year compounding fee drag of Regular plans is calculated and presented to the founder.
3. **Total Return vs IDCW Separation:** IDCW (Income Distribution cum Capital Withdrawal) is fundamentally a distribution of existing net asset value—never free bonus yield. Performance is measured strictly via NAV compounding (Growth option).
4. **Portfolio Overlap Discipline:** Investors holding multiple mutual funds often unknowingly duplicate identical mega-cap stocks. The engine computes mathematical portfolio overlap using common holding weights.
5. **Passive ETF Tracking Metrics:** ETFs are evaluated by Tracking Difference and Tracking Error, not just gross historical returns.

---

## 2. Mathematical Formulas

### 2.1 Portfolio Overlap Percentage
$$\text{Overlap}(A, B) = \sum_{i \in A \cap B} \min(\text{Weight}_{A, i}, \text{Weight}_{B, i})$$

### 2.2 Direct Plan Compounding Wealth Difference
$$\Delta \text{Wealth} = P \times \left[ (1 + r - \text{TER}_{\text{direct}})^N - (1 + r - \text{TER}_{\text{regular}})^N \right]$$
Where $P = \text{Principal}$, $r = \text{Gross CAGR}$, $N = \text{Horizon years}$.

### 2.3 Annualized Tracking Error
$$\text{TE} = \sqrt{\frac{1}{N-1} \sum_{t=1}^{N} \left( (R_{\text{ETF}, t} - R_{\text{Bench}, t}) - \overline{\Delta R} \right)^2} \times \sqrt{252}$$
