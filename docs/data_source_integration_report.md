# AURXON Data Source Integration Report — Phase 2.2
**Project:** AURXONQuant  
**Milestone:** Phase 2.2 — Primary-Source Data Integration & Evidence Verification  
**Status:** VERIFIED & AUDITED  
**Date:** 2026-10-13  

---

## 1. Executive Summary

AURXONQuant prioritizes primary, regulatory, and official statutory data sources over third-party scrapers or uncorroborated financial blogs. Under Phase 2.2, a provider-independent data integration architecture has been established with explicit data classifications, legal retrieval methods, and deterministic fallback behaviors.

---

## 2. Source Priority Hierarchy

| Priority | Source Tier | Provider / Entity | Permitted Access Method | Primary Instruments / Disclosures |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Regulatory Publications | SEBI (Securities & Exchange Board of India) | Public filing archive HTTP retrieval / Statutory filings | DRHP, RHP, Listing approvals, Takeover regulations |
| **Tier 2** | Official Exchanges | NSE & BSE India | Public equity quote archives & official corporate announcements | Equity prices, Bhavcopy, announcements, tick bounds |
| **Tier 3** | Official Issuer Disclosures | Issuer IR & Registrar (KFin, Link Intime) | Official investor relations portals | Audited annual reports, Investor presentations, basis of allotment |
| **Tier 4** | Statutory Fund Publications | AMFI (Association of Mutual Funds in India) | Statutory open NAV feed (`https://www.amfiindia.com/spages/NAVAll.txt`) | Daily NAV, ISIN mapping, Scheme codes, Plan types |
| **Tier 5** | Official AMC Factsheets | AMC Disclosures (PPFAS, Mirae, Nippon) | Monthly portfolio disclosure sheets (SEBI mandated) | Monthly portfolio holdings, AUM, TER, benchmark disclosures |
| **Tier 6** | Licensed Data Providers | Dedicated Market APIs (when licensed) | Authenticated REST/WebSocket | Intraday streaming, order book depth |
| **Tier 7** | Secondary Verification | Aggregators / Independent cross-checks | Supplemental reference only | Uncorroborated reference only |

---

## 3. Data Classification States

Every material metric and dataset in AURXONQuant is explicitly typed with one of seven canonical classifications:

1. `LIVE_VERIFIED`: Real-time data retrieved directly via an authenticated, permitted session within its active freshness window.
2. `DELAYED_VERIFIED`: Exchange-delayed or end-of-day data with verified exchange timestamp and official settlement date.
3. `HISTORICAL_VERIFIED`: Audited statutory or prospectus filing records linked to verified regulatory documents (e.g. SEBI RHP).
4. `CACHED`: Locally stored verified snapshot used when running offline or in network-isolated sandboxes.
5. `SYNTHETIC`: Deterministically generated stress test or simulated trajectory; explicitly flagged with visible warning tags.
6. `UNVERIFIED`: Data retrieved from unauthenticated or secondary sources awaiting multi-model or document corroboration.
7. `UNAVAILABLE`: Data not disclosed in public filings or unavailable from permitted channels. Never defaulted to zero.

---

## 4. AMFI Mutual Fund Statutory Connector

### 4.1 Specification
- **Endpoint:** `https://www.amfiindia.com/spages/NAVAll.txt`
- **Regulatory Basis:** SEBI circular mandates daily NAV publication by 11:00 PM for all registered mutual fund schemes.
- **Access Protocol:** Open HTTP GET; plain pipe-delimited text (`Scheme Code;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date`).
- **Offline / Sandbox Resilience:** Packaged verified statutory baseline snapshot (`LOCAL_AMFI_SNAPSHOT`) ensures 100% offline functionality without network dependencies.

### 4.2 Verified Scheme Mapping
- `122639` (`INF879O01027`): Parag Parikh Flexi Cap Fund - Direct Plan - Growth (NAV: ₹78.4321)
- `122640` (`INF879O01019`): Parag Parikh Flexi Cap Fund - Regular Plan - Growth (NAV: ₹71.8942)
- `100122` (`INF732E01015`): Nippon India ETF Nifty 50 BeES (NAV: ₹272.5400)
- `107578` (`INF769K01010`): Mirae Asset Large Cap Fund - Direct Plan - Growth (NAV: ₹114.2810)

---

## 5. Security and Operational Compliance

1. **Zero Credential Storage:** No broker login credentials, passwords, TOTP tokens, or financial transaction credentials are saved.
2. **Loopback Service Binding:** Backend strictly binds to `127.0.0.1` preventing remote exposure.
3. **50 MB File Size Ceiling:** Enforced on DRHP/RHP upload endpoints to prevent memory denial-of-service.
4. **Anti-Scraping / Terms Compliance:** No CAPTCHA bypassing or unauthorized scraping routines.
