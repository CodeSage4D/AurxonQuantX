# AURXON Source Registry & Access Governance

**Milestone:** Phase 2  
**Status:** Hardened Specification  
**Version:** 1.0.0  

---

## 1. Principles of Source Governance

1. **Hierarchy of Truth:** Primary regulatory documents (SEBI, RBI) and official issuer disclosures (DRHP/RHP, ROC, Exchange filings) always take precedence over secondary news reporting or aggregators.
2. **Aggregator Demotion:** Aggregated data (Yahoo Finance, Screener, Moneycontrol) is classified as `AGGREGATOR` with a 15-minute delay notice. It is never misrepresented as a primary exchange tick stream.
3. **No Scraping Against Anti-Bot / Terms:** The platform respects `robots.txt`, rate limits, and requires explicit user-provided sessions for authenticated portals. It never bypasses CAPTCHAs, bot defenses, or paywalls.
4. **Fallback Honesty:** When a source access fails, the failure is logged and the data is marked `UNAVAILABLE`. Missing prospectus figures or fund NAVs are never fabricated.

---

## 2. Source Hierarchy & Reliability Weights

| Source ID | Name | Category | Access Method | Weight | Update Frequency | Fallback Policy |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `SRC_SEBI` | Securities and Exchange Board of India | `PRIMARY_REGULATORY` | Direct HTTP | 1.00 | Daily / Ad-hoc | Check Exchange circulars; do not guess regulatory stance. |
| `SRC_NSE_BSE` | NSE & BSE Corporate Filings (LODR) | `EXCHANGE_OFFICIAL` | Direct HTTP / API | 0.98 | Real-time / Daily | Disk cache $\to$ Offline benchmark archive. |
| `SRC_ISSUER_PROSPECTUS`| DRHP / RHP / Prospectus Filing | `ISSUER_OFFICIAL` | Manual Upload / PDF | 0.95 | Filing milestones | Prompt founder for manual PDF upload; do not interpolate. |
| `SRC_AMFI` | Association of Mutual Funds in India | `AMFI_AMC_OFFICIAL` | Direct HTTP | 0.98 | Daily NAVs (9 PM) | Local cached NAV; label date staleness clearly. |
| `SRC_AMC_SID` | AMC Scheme Information Docs & Factsheets| `AMFI_AMC_OFFICIAL` | Local Parser | 0.96 | Monthly | Mark unverified fields as `AWAITING_FACTSHEET`. |
| `SRC_REPUTABLE_SEC` | CRISIL, ICRA Rating Rationales | `REPUTABLE_SECONDARY` | Direct HTTP / PDF | 0.88 | Quarterly / Annual | Note absence of rating corroboration. |
| `SRC_BENCHMARK_ARCHIVE`| Ground-Truth Calibration Fixtures | `SYNTHETIC_BENCHMARK`| Local Storage | 0.90 | Static / Versioned | Frozen offline safety net; strictly tagged. |
