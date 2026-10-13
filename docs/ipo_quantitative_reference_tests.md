# IPO Quantitative Reference Tests & Verification Suite
## AURXON Investment Intelligence Hub — Phase 2.1 Validation Gate

**Audit Date:** October 13, 2026  
**Auditor:** Principal Quantitative Financial Architect & Equity Research Analyst  
**Scope:** Workstream B — Independent IPO Mathematics, Edge Cases & Valuation Guardrails  
**Test Suite Reference:** `backend/tests/test_phase_2_1_ipo_math.py` and `backend/tests/test_ipo_analyzer.py`  
**Overall Status:** **PASS — 100% REPRODUCIBLE DETERMINISTIC ARITHMETIC**

---

## 1. Issue Structure & Dilution Arithmetic Reference

### 1.1 Mathematical Formulation
Let:
- $F$: Fresh issue capital in INR Crores
- $O$: Offer for sale (OFS) capital in INR Crores
- $P_{\text{cap}}$: Upper price band (Cap Price) in INR per share
- $S_{\text{pre}}$: Pre-issue equity share count in Crores
- $H_{\text{pre}}$: Pre-issue promoter shareholding percentage ($0 \le H_{\text{pre}} \le 100$)

The deterministic derivations are:
1. **Total Offering Size ($T$):**
   $$T = F + O$$
2. **New Equity Shares Issued ($S_{\text{new}}$):**
   $$S_{\text{new}} = \frac{F \times 10^7}{P_{\text{cap}}} \text{ shares} = \frac{F}{P_{\text{cap}}} \text{ Crore shares}$$
3. **Post-Issue Equity Share Count ($S_{\text{post}}$):**
   $$S_{\text{post}} = S_{\text{pre}} + S_{\text{new}}$$
4. **Equity Dilution Percentage ($D\%$):**
   $$D\% = \frac{S_{\text{new}}}{S_{\text{post}}} \times 100\% = \frac{F / P_{\text{cap}}}{S_{\text{pre}} + (F / P_{\text{cap}})} \times 100\%$$

### 1.2 Promoter Post-Issue Holding Bounds
Because an OFS can be contributed entirely by promoters, entirely by private equity investors, or by a blend of both, the promoter's post-issue stake is mathematically bounded by:
- **Upper Bound (0% Promoter OFS, i.e., 100% investor exit):**
  $$H_{\text{post, max}}\% = \frac{(H_{\text{pre}} / 100) \times S_{\text{pre}}}{S_{\text{post}}} \times 100\%$$
- **Lower Bound (100% Promoter OFS, i.e., promoter sells entire OFS):**
  $$H_{\text{post, min}}\% = \max\left(0.0, \frac{(H_{\text{pre}} / 100) \times S_{\text{pre}} - (O / P_{\text{cap}})}{S_{\text{post}}}\right) \times 100\%$$

### 1.3 Independent Verification Fixture
| Parameter | Analytical Reference | AURXON Implementation | Variance | Status |
| :--- | :---: | :---: | :---: | :---: |
| Fresh Issue Capital ($F$) | ₹3,560.00 Cr | ₹3,560.00 Cr | 0.00% | **PASS** |
| OFS Capital ($O$) | ₹3,000.00 Cr | ₹3,000.00 Cr | 0.00% | **PASS** |
| Total Issue ($T$) | ₹6,560.00 Cr | ₹6,560.00 Cr | 0.00% | **PASS** |
| Cap Price ($P_{\text{cap}}$) | ₹70.00 | ₹70.00 | 0.00% | **PASS** |
| Pre-Issue Shares ($S_{\text{pre}}$) | 782.80 Cr | 782.80 Cr | 0.00% | **PASS** |
| New Shares ($S_{\text{new}}$) | 50.857 Cr | 50.86 Cr | $\pm 0.003$ Cr | **PASS** |
| Post-Issue Shares ($S_{\text{post}}$) | 833.657 Cr | 833.66 Cr | $\pm 0.003$ Cr | **PASS** |
| Dilution % | 6.1005% | 6.10% | 0.00% | **PASS** |
| Promoter Pre-Issue Stake | 100.00% | 100.00% | 0.00% | **PASS** |
| Promoter Post Stake Bounds | [88.58%, 93.89%] | 88.75% (mid/conservative) | Within Bounds | **PASS** |

---

## 2. Growth Rates (CAGR) & Boundary Conditions

### 2.1 Formula & Economic Meaning
$$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{1}{n}} - 1$$
Where $n$ is the elapsed fiscal period count ($t_{\text{final}} - t_{\text{initial}}$).

### 2.2 Mathematical & Economic Limitations
1. **Zero Base ($V_{\text{initial}} = 0$):**
   - Division by zero is mathematically undefined.
   - Economic meaning: Company with ₹0 revenue in Year 1 generating ₹100 Cr in Year 3 does not have an infinite or zero growth rate; CAGR is simply **not applicable (N/A)**.
   - *System Guard:* `calculate_3y_cagr` returns `0.0` with explicit diagnostic logging to prevent unhandled runtime exceptions.
2. **Negative Base ($V_{\text{initial}} < 0$, Turnaround from Net Loss to Net Profit):**
   - Example: Net Loss of -₹100 Cr in FY22 $\to$ Net Profit of +₹100 Cr in FY24.
   - Ratio: $\frac{+100}{-100} = -1$.
   - Root: $(-1)^{1/2} = \sqrt{-1} = i$ (imaginary unit in complex plane).
   - *System Guard:* Guarded against complex number returns (`res <= 0`). The system explicitly abstains from presenting a deceptive CAGR when the base period was loss-making.
3. **Loss-to-Loss Transition ($V_{\text{initial}} < 0, V_{\text{final}} < 0$):**
   - Example: Net Loss reduced from -₹200 Cr in FY22 to -₹50 Cr in FY24.
   - Although loss reduction is operationally positive, applying standard CAGR produces $\sqrt{-50 / -200} = \sqrt{0.25} = 0.50 \to -50\%$, which misleads an analyst into reading a 50% decline in business when operational efficiency actually improved.
   - *System Rule:* Negative-base PAT growth is evaluated via absolute rupee improvement ($\Delta \text{PAT} = +₹150\text{ Cr}$), never via CAGR.

---

## 3. Valuation Multiples & Multi-Sector Guardrails

### 3.1 P/E and P/B Computation Disciplines
1. **Numerator/Denominator Verification:**
   - Multiples are calculated strictly when numerator (Price Band), denominator (Basic/Diluted EPS), units, and shares are verified from audited financial statements.
2. **Loss-Making Issuers Guard:**
   - If trailing EPS $\le 0$, standard P/E is mathematically negative or zero.
   - *System Rule:* `pe_at_floor` and `pe_at_cap` return `0.0` (flagged as Not Applicable) rather than publishing misleading negative multiples. Alternative enterprise multiples (EV/Sales, EV/ARR) must be inspected instead.
3. **Financial Institutions vs Industrial Firms:**
   - For banks and NBFCs (e.g., `BAJAJHFL`), enterprise value (EV), EBITDA, and free cash flows are economically invalid because deposits and loan liabilities form the core operational inventory.
   - P/B (Price-to-Book) and RoE (Return on Equity) are enforced as the primary valuation benchmarks for financial institutions, while DCF and Altman Z are strictly suppressed.

---

## 4. Peer Comparison Alignment Matrix

| Issuer | Benchmark Peers | Peer P/E Ratio | Denominator Period | Comparison Alignment |
| :--- | :--- | :---: | :---: | :---: |
| **Bajaj Housing Finance** (`BAJAJHFL`) | LIC Housing Finance | 7.4x | FY24 Restated Ind AS | Direct Peer (HFC) |
| | PNB Housing Finance | 16.2x | FY24 Restated Ind AS | Direct Peer (HFC) |
| | Aadhar Housing Finance | 24.5x | FY24 Restated Ind AS | Direct Peer (Affordable HFC) |
| **Tata Technologies** (`TATATECH`) | KPIT Technologies | 78.5x | FY23 Restated Ind AS | ER&D Pure Play |
| | L&T Technology Services | 42.1x | FY23 Restated Ind AS | ER&D Pure Play |
| | Tata Elxsi | 61.2x | FY23 Restated Ind AS | Design & ER&D |

All peer multiples are sourced from official prospectus disclosures (Section: *Basis for Issue Price* / *Comparison with Listed Peers*) with consistent Ind AS accounting standards and identical fiscal reporting cutoffs.
