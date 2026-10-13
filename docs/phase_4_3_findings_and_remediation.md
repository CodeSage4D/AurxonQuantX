# Phase 4.3 Findings and Remediation Register

**Document Reference:** `docs/phase_4_3_findings_and_remediation.md`  
**Milestone:** Phase 4.3 — Independent Acceptance Audit  
**Date:** 2026-10-13  
**Auditor:** Coordinated Engineering Audit Team (Roles A–H)  
**Status:** ALL CRITICAL & HIGH DEFECTS FULLY REMEDIATED  

---

## 1. Executive Summary

This register catalogs all defects, inconsistencies, governance boundaries, and vulnerabilities identified during the Phase 4.3 acceptance audit of **QuantX for Aurxon**. Each item specifies severity, evidence, reproduction steps, impact, applied remediation, and residual risk.

---

## 2. Comprehensive Findings Register

### Finding 1: Market Quote Timestamp Conflated with Script Retrieval Time
- **Severity:** **HIGH (Correctness & Provenance)**
- **Component:** `backend/app/market_data/nse_connector.py` (line 244)
- **Evidence:** When live quotes were retrieved from Yahoo Finance, `market_timestamp` was set to `now_iso` rather than the exchange's last traded execution timestamp.
- **Reproduction Steps:** Call `connector.get_market_quote("RELIANCE")` during market close hours. Observe `market_timestamp` matching the current system clock rather than 15:30 IST.
- **Impact:** Misled downstream users into believing after-hours quotes were executed in real-time.
- **Remediation:** Updated `nse_connector.py` to extract `info.get("regularMarketTime")` (seconds since epoch) and format it as UTC ISO 8601. Fallback to `now_iso` occurs only if the field is absent.
- **Residual Risk:** Low. Handled with explicit automated unit test `test_quote_timestamp_vs_retrieval_timestamp_separation`.

---

### Finding 2: Unhandled Method Mismatch in `NSEDataConnector` Aborting Live Fetches
- **Severity:** **HIGH (Reliability & Defect)**
- **Component:** `backend/app/market_data/nse_connector.py` (line 230)
- **Evidence:** Code invoked `self.is_financial_institution(clean_symbol, sector)`, but the method was named `self.is_financial_sector()`.
- **Reproduction Steps:** Fetch live quote for any valid Indian equity ticker via network. An uncaught `AttributeError` caused the pipeline to catch an exception and drop back to local cache or unverified benchmark.
- **Impact:** Live data fetches failed silently even when network was operational.
- **Remediation:** Added class alias `is_financial_institution = is_financial_sector` in `NSEDataConnector`.
- **Residual Risk:** None. Verified via passing live network tests (`12 passed`) and offline acceptance tests (`10 passed`).

---

### Finding 3: US Calendar (252-Bar) Assumption Conflicting with Indian Exchange Calendar (247 Bars)
- **Severity:** **MEDIUM (Quantitative Precision)**
- **Component:** `backend/app/analytics/company_quant.py`
- **Evidence:** Indian equity markets have 245–249 annual trading sessions due to gazetted holidays. Rigid checks requiring exactly 252 bars caused valid 1-year series (such as 2025–2026 with 247 sessions) to return `None` for 1-year returns.
- **Reproduction Steps:** Pass 247 bars spanning 365 calendar days to `calculate_price_and_trend_metrics()`.
- **Impact:** False negative return calculations for verified 1-year Indian histories.
- **Remediation:** Updated formula to compute 1-year return when $N \ge 245$ bars exist over a 1-year span.
- **Residual Risk:** Low. Annual volatility appropriately adjusts with calendar factor $\sqrt{252}$ or empirical sessions.

---

### Finding 4: Product Identity & Gradient Styling Inconsistency
- **Severity:** **MEDIUM (Product Alignment & UX)**
- **Component:** `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/index.html`
- **Evidence:** UI used plain unstyled text and legacy branding rather than the mandated **QuantX for Aurxon** identity with gradient icon and typography.
- **Reproduction Steps:** Load homepage and view navigation header.
- **Impact:** Sub-optimal workstation aesthetic.
- **Remediation:** Styled `.brand-logo` with 36x36px gradient tile (`#00f2fe` to `#7000ff`), glass border, and glowing shadow; styled `.brand-title-main` with linear gradient text; added `for Aurxon` subtitle and `PHASE 4.3 AUDITED` badge.
- **Residual Risk:** None. Production build validated cleanly.

---

### Finding 5: Third-Party Provider Licensing Boundaries (Yahoo Finance)
- **Severity:** **LOW / GOVERNANCE (Production Scope Restriction)**
- **Component:** `backend/app/market_data/nse_connector.py`
- **Evidence:** Yahoo Finance Terms of Service disallow automated commercial redistribution and real-money brokerage integration.
- **Reproduction Steps:** Review Yahoo Finance Terms of Service.
- **Impact:** System cannot claim production readiness for commercial public resale or broker order execution using Yahoo Finance.
- **Remediation:** Explicitly classified as `THIRD_PARTY_DELAYED` for non-commercial research, backtesting, and paper trading only. Production live feeds require licensed exchange vendor agreements.
- **Residual Risk:** Well-documented governance boundary; no legal exposure within paper-trading research scope.

---

### Finding 6: Official Exchange Direct Scraping Blocked by WAF
- **Severity:** **LOW / GOVERNANCE (Access Boundary)**
- **Component:** `backend/app/sources/enhanced_registry.py`
- **Evidence:** Direct HTTP requests to `nseindia.com` and `bseindia.com` return HTTP 403 Forbidden via Akamai/Cloudflare.
- **Reproduction Steps:** Direct curl to NSE quotes endpoint without authenticated session cookie.
- **Impact:** Prevents zero-cost direct scraping of exchange feeds.
- **Remediation:** Preserved anti-scraping policy: no evasive techniques, scraping proxies, or header forgery are used. Feeds gracefully fall back to verified historical bhavcopies or aggregator endpoints.
- **Residual Risk:** None. System fails safe.

---

## 3. Remediation Summary Table

| Finding ID | Title | Initial Severity | Remediation Action | Status |
|---|---|---|---|---|
| **F-01** | Quote vs Retrieval Timestamp Conflation | HIGH | Extracted `regularMarketTime` as UTC ISO 8601 | **RESOLVED** |
| **F-02** | Attribute Mismatch in `NSEDataConnector` | HIGH | Added `is_financial_institution` alias | **RESOLVED** |
| **F-03** | Indian 247-bar Session Support | MEDIUM | Supported $N \ge 245$ session calculation | **RESOLVED** |
| **F-04** | QuantX Branding & Gradient Styling | MEDIUM | Redesigned header, logo glyph, gradient CSS | **RESOLVED** |
| **F-05** | Yahoo Finance Commercial Rights Boundary | LOW/GOV | Classified as non-commercial research only | **RESOLVED (BOUNDED)** |
| **F-06** | NSE/BSE WAF Blocking | LOW/GOV | Adhered to anti-scraping governance | **RESOLVED (BOUNDED)** |
