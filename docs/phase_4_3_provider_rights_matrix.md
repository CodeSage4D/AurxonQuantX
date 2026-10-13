# Phase 4.3 Provider Rights & Source Governance Matrix

**Document Reference:** `docs/phase_4_3_provider_rights_matrix.md`  
**Milestone:** Phase 4.3 — Gate B Acceptance  
**Date:** 2026-10-13  
**Auditor:** Role F (Provider Rights and Governance Auditor)  
**Status:** AUDITED & CLASSIFIED (CONDITIONAL PASS FOR PRODUCTION SCOPE)  

---

## 1. Provider Governance Framework

A successful HTTP response code does not constitute authorization for redistribution, commercial display, or official exchange tick representation. Each external data source integrated or evaluated in **QuantX for Aurxon** has been audited under four distinct criteria:
1. **Technical Connectivity & Data Integrity**
2. **Freshness & Provenance Transparency**
3. **Documented Terms & Licensing Boundaries**
4. **Production Suitability Status**

---

## 2. Comprehensive Provider Audit Matrix

| Provider Identity | Data Scope | Connectivity Tested | Data Retrieved | Instruments & Range | Freshness Behavior | Documented Terms Permitted | Caching Permitted | Internal Display Permitted | Commercial Redistribution Permitted | Production Readiness Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **AMFI India** (`portal.amfiindia.com`) | Mutual Fund NAVs | **YES** (HTTP 200) | **YES** (Daily NAV text) | All Indian MFs (~15,000 schemes) | Daily (21:00 IST NAV updates) | **YES** (Public statutory dissemination) | **YES** (Fair use cache) | **YES** | **YES** (Public disclosure) | **APPROVED (PRODUCTION)** |
| **Yahoo Finance** (`yfinance`) | Indian Equities & Indices (NSE/BSE) | **YES** (HTTP 200) | **YES** (247 daily bars, quotes) | Nifty 50, broad Indian equities | 15-minute delayed quotes; daily EOD | **CONDITIONAL** (Personal/research use only) | **YES** (Local client caching) | **YES** (Research workstation) | **NO / STRICTLY PROHIBITED** | **CONDITIONAL (DEV / RESEARCH ONLY)** |
| **NSE India Direct Web** (`nseindia.com`) | Official Live Feeds & Bhavcopy | **BLOCKED** (Akamai WAF 403) | **NO** | Blocked | N/A | **PROHIBITED** (Automated scraping banned by ToS) | **NO** | **NO** | **NO** | **REJECTED (REQUIRES LICENSED FEED)** |
| **BSE India Direct Web** (`bseindia.com`) | BSE Bhavcopy & Filings | **BLOCKED** (WAF / Cloudflare) | **NO** | Blocked | N/A | **PROHIBITED** (Automated scraping banned by ToS) | **NO** | **NO** | **NO** | **REJECTED (REQUIRES LICENSED FEED)** |
| **Alpha Vantage** | US/Global/Indian Equities | **UNCONFIGURED** | **NO** | API Key not set | N/A | Requires Commercial API Plan | `REQUIRES_REVIEW` | `REQUIRES_REVIEW` | `REQUIRES_REVIEW` | **CONDITIONAL (PENDING API KEY)** |
| **RBI (Reserve Bank of India)** | Policy Rates (Repo, Reverse Repo, SDF) | **YES** (Static Reference / Public Site) | **YES** | Macroeconomic benchmarks | Monthly / Bi-monthly MPC updates | **YES** (Public official dissemination) | **YES** | **YES** | **YES** | **APPROVED (PRODUCTION)** |
| **Company Investor Relations (BSE/NSE statutory uploads)** | Annual Reports, Earnings Presentations | **YES** (Direct PDF ingestion) | **YES** | Reliance, TCS, Infosys, HDFC Bank | Quarterly / Annual | **YES** (Public regulatory disclosures) | **YES** (Research archive) | **YES** | **YES** (Fair dealing research) | **APPROVED (PRODUCTION)** |
| **AURXON Benchmark Fixtures** | Deterministic Offline Fixtures | **YES** (Local storage) | **YES** | Top 4 Nifty 50 benchmark stocks | Offline frozen snapshot | **YES** (Proprietary test calibration) | **YES** | **YES** | **YES** | **APPROVED (OFFLINE / DEV ONLY)** |

---

## 3. Governance Findings & Boundaries

1. **Yahoo Finance Prohibition on Commercial Redistribution:**
   - *Governance Finding:* Yahoo Finance explicitly restricts automated commercial redistribution and real-time trade execution in its Terms of Service.
   - *Enforced Boundary:* In QuantX, Yahoo Finance data is strictly tagged with:
     - `classification = DataClassification.THIRD_PARTY_DELAYED`
     - `freshness = FreshnessStatus.FRESH` (or `STALE_ACCEPTABLE`)
     - `provenance_notes = "Third-party aggregator quote. Disclaimers: 15-minute delayed; not an official exchange direct tick feed."`
   - *Release Constraint:* Yahoo Finance is approved **strictly for non-commercial research, backtesting validation, and paper-trading simulation**. It must never be connected to real-money broker routing.

2. **Official Exchange Direct Access:**
   - Both NSE and BSE operate active Web Application Firewalls (Akamai / Cloudflare) that rightfully reject non-browser automated scrapers. QuantX adheres to governance directives: **no scraper evasion, header spoofing, or WAF bypass tools are permitted or implemented**.
   - Production deployment requiring sub-second, real-time exchange ticks must integrate an authorized, commercial Market Data Feed Provider (such as NSE Data & Analytics or BSE Market Data Feed vendor agreements).

3. **AMFI Statutory Dissemination:**
   - AMFI NAV text feeds are established public statutory records with open access. QuantX ingests these with full provenance citations and error-handling resilience.

---

## 4. Gate B Acceptance Decision

**GATE B STATUS: CONDITIONAL PASS**  
- **Approved for Research & Paper Trading:** AMFI, RBI, Company Filings, and Local Curated Benchmark Fixtures.
- **Conditional (Non-Commercial Research Only):** Yahoo Finance aggregator.
- **Production Boundary:** Live commercial distribution requires contracted exchange tick licenses.
