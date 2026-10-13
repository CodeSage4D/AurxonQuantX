# AURXON IPO Prospectus Intelligence Specification

**Milestone:** Phase 2  
**Status:** Hardened Specification  
**Version:** 1.0.0  

---

## 1. Principles of IPO Research

1. **No Speculative Euphoria:** An attractive company does not automatically imply an attractive IPO price. The analysis strictly decouples business quality from valuation multiples.
2. **Deterministic Arithmetic:** Total issue size, Fresh Issue vs Offer For Sale (OFS) split, post-issue equity dilution, promoter stake dilution, and P/E multiples are computed deterministically in code—never guessed by an LLM.
3. **Disclosed Risks $\neq$ Misconduct:** Indian regulations (SEBI ICDR) mandate exhaustive risk disclosures. A disclosed litigation or concentration risk is evaluated by material financial impact rather than assumed guilt.
4. **No Allotment or Capital Promises:** The engine strictly forbids promising listing gains, grey market premiums (GMP), allotment guarantees, or downside protection.
5. **The 7 Mandated Research Verdicts:**
   - Business Quality
   - Financial Quality
   - Governance & Disclosed Risks
   - Valuation Multiples vs Listed Peers
   - Issue Structure & Capital Deployment
   - Listing-Day Speculation vs Long-Term Suitability
   - Key Facts Still Requiring Verification

---

## 2. Mathematical Formulas & Arithmetic Integrity

### 2.1 Post-Issue Equity Base & Dilution
$$\text{New Fresh Shares} = \frac{\text{Fresh Issue Capital (INR Cr)}}{\text{Price Band Cap (INR)}}$$
$$\text{Post-Issue Shares} = \text{Pre-Issue Shares} + \text{New Fresh Shares}$$
$$\text{Dilution Percentage} = \frac{\text{New Fresh Shares}}{\text{Post-Issue Shares}} \times 100\%$$

### 2.2 IPO Valuation Multiples
$$\text{Market Capitalization at Cap} = \text{Price Band Cap} \times \text{Post-Issue Shares}$$
$$\text{P/E at Upper Band} = \frac{\text{Price Band Cap}}{\text{Trailing Diluted EPS}}$$
$$\text{Peer Premium/Discount} = \frac{\text{IPO P/E} - \text{Peer Average P/E}}{\text{Peer Average P/E}} \times 100\%$$

---

## 3. Disclosed Risk Classification Matrix

| Risk Category | Key Risk Triggers Audited in DRHP/RHP | Materiality Impact Metric |
| :--- | :--- | :--- |
| `CUSTOMER_CONCENTRATION` | Top 5 customers $> 40\%$ of revenue. | Revenue loss sensitivity if key anchor departs. |
| `INDEBTEDNESS` | High debt-to-equity ($> 3.0$x) or rising finance cost. | Interest coverage ratio stress under higher rate cycles. |
| `PROMOTER_GOVERNANCE` | High promoter pledge or past regulatory reprimands. | Voting control stability and governance discount. |
| `LITIGATION_REGULATORY` | Tax claims or patent disputes exceeding $5\%$ of net worth. | Contingent liability as percentage of net worth. |
| `OPERATING_HISTORY` | $100\%$ OFS (Zero fresh capital infusion into company). | Capital expenditure reliance purely on internal accruals. |
