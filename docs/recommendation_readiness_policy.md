# AURXON Recommendation Readiness Policy — Phase 2.2
**Project:** AURXONQuant  
**Milestone:** Phase 2.2 — Primary-Source Data Integration & Evidence Verification  
**Status:** ENFORCED  
**Date:** 2026-10-13  

---

## 1. Principle: No Black-Box Universal Scores

AURXONQuant rejects single, opaque numerical "investment scores" that obscure underlying risks and data deficiencies. A high financial score must not mask poor governance, stale earnings, or an unverified prospectus.

Instead, recommendations are governed by **explicit multi-dimensional evidence gates**:
1. **Business Quality** (Moat, competitive position, sector dynamics)
2. **Financial Quality** (ROE, ROCE, debt-to-equity, cash flow generation)
3. **Governance & Documented Risks** (Promoter track record, related party transactions, legal proceedings)
4. **Valuation** (P/E relative to peer median, DCF margin of safety, dilution mechanics)
5. **Market & Liquidity Conditions** (Free float, trading volumes, lock-in expiries)
6. **Portfolio Suitability** (Investor time horizon, risk profile, existing asset allocation)
7. **Evidence & Provenance Integrity** (Filing verification, freshness, extraction confidence)

---

## 2. Gate Decision Hierarchy

| Gate Status | Description | User Interface Presentation | Permitted Actions |
| :--- | :--- | :--- | :--- |
| `ACTIVE_UNQUALIFIED` | All 7 dimensions satisfy threshold criteria; verified primary sources; no stale metrics. | Green badge (`ACTIVE_UNQUALIFIED`); full confidence metrics displayed. | Actionable research thesis permitted. |
| `QUALIFIED_ADVISORY` | Core facts verified, but material qualifications exist (e.g., historical earnings lag, high anchor concentration, pure OFS). | Amber badge (`QUALIFIED_ADVISORY`) with explicit advisory bullet points. | Recommendation permitted *strictly subject to stated qualifications*. |
| `BLOCKED_DEFICIENT` | Essential inputs missing, stale data (>permitted window), ambiguous identity, or unresolved material contradiction. | Red badge (`BLOCKED_DEFICIENT`) with blocking diagnostics; recommendation masked. | Recommendation BLOCKED. Research thesis withheld until data refreshed. |

---

## 3. Strict Prohibitions

1. **No Speculative Pop Guarantees:** Recommendations must never promise "listing day pops", "guaranteed allotment", or "risk-free stag profits".
2. **No Capital Protection Promises:** Equities and mutual funds carry market risk; no capital guarantees are permitted.
3. **Past Performance Disclaimers:** Historical CAGR is explicitly labeled as not predictive of future returns.
4. **Founder Portfolio Inventions:** Allocation models use strictly founder-entered or confirmed cash balances and goals; the system never invents hypothetical portfolio holdings.
