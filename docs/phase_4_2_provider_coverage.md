# Aurxon QuantX — Phase 4.2 Provider and Licensing Decisions

**Product Identity:** Aurxon QuantX  
**Brand:** AURXON  
**Audit Date:** 2026-10-13  
**Auditor:** Principal Data Licensing Auditor & Financial Systems Architect  
**Baseline Commit:** `7ad29f8` | **Target Milestone:** Phase 4.2  

---

## 1. Provider Evaluation Framework

A successful HTTP response code does not establish commercial redistribution rights or production suitability. In Aurxon QuantX, every data provider is evaluated along a six-dimensional operational and regulatory framework:
1. **Technically Accessible:** Endpoints reachable over TCP/TLS without socket errors or network drops.
2. **Authenticated / Configured:** Required API keys, secrets, or headers present and valid.
3. **Data Retrieved:** Actual market prices, NAVs, or disclosures successfully parsed.
4. **Coverage Validated:** Correct ticker resolution, date range, and zero duplicate bars.
5. **Permitted Usage:** Permitted under provider terms for quantitative research and backtesting.
6. **Production Suitability:** Sufficient SLA, rate limits, latency, and institutional support.

---

## 2. Provider Evaluation Matrix

| Provider / Channel | Accessible | Configured | Data Retrieved | Coverage Validated | Permitted Usage | Production Suitability | Operational Status / Policy Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **AMFI Statutory NAV** | **YES** | Public | **YES** (~15k schemes) | **YES** (Daily) | **YES** (Statutory Public) | **PRODUCTION READY** | Primary feed for Indian Mutual Fund portfolios. Zero licensing fees. |
| **RBI DBIE Macro** | **YES** | Public | **YES** (Policy rates) | **YES** (G-Sec/Repo) | **YES** (Govt Public Domain)| **PRODUCTION READY** | Primary feed for risk-free rate ($R_f = 6.5\%$) and yield curves. |
| **Yahoo Finance (NSE)**| **YES** | Public | **YES** (Daily OHLCV) | **YES** (247 bars/yr) | **RESEARCH ONLY** | **PROTOTYPE / BACKTEST** | Permitted for personal quantitative research; commercial redistribution restricted. |
| **NSE India Official** | **NO** (WAF) | N/A | **NO** (Blocked 403) | **NO** | Regulated Exchange Data | **REQUIRES SUBSCRIPTION** | Anti-bot WAF blocks automated scraping. Commercial data product required. |
| **BSE India Official** | **PARTIAL** | N/A | **NO** | **NO** | Regulated Exchange Data | **REQUIRES SUBSCRIPTION** | Official Bhavcopy archives require licensed institutional access. |
| **Issuer IR Portals** | **YES** | Public | **YES** (Filings/Pdfs) | **YES** (Quarterly) | **YES** (SEBI Public LODR) | **PRODUCTION READY** | Primary evidence source for audited balance sheets and disclosures. |
| **Alpha Vantage API** | Optional | Missing Key | **NO** | Unverified | Commercial / Free 25/day | **BLOCKED (UNCONFIGURED)** | Requires commercial API key; 25 req/day free tier exhausts rapidly. |
| **Audited Benchmark** | **YES** | In-Memory | **YES** (Top Nifty 50) | **YES** (Deterministic)| **YES** (Internal Proprietary) | **PRODUCTION READY (OFFLINE)** | Deterministic offline calibration archive for zero-network testing. |

---

## 3. Detailed Licensing & Compliance Decisions

### 3.1 AMFI Daily Statutory NAV Feed
- **Licensing Terms:** Open public financial data mandated under SEBI (Mutual Funds) Regulations, 1996.
- **Permitted Scope:** Unrestricted non-commercial and analytical use for Indian mutual fund portfolios.
- **Redistribution Policy:** Raw data caching permitted for quantitative scoring and portfolio analysis.

### 3.2 Reserve Bank of India DBIE Portal
- **Licensing Terms:** Open Government Data (OGD) Platform India (Public Domain).
- **Permitted Scope:** Macroeconomic policy rates (Repo rate, Reverse Repo, SDF), G-Sec sovereign yields, and inflation benchmarks.

### 3.3 Yahoo Finance (`yfinance`) Indian Equity Connector
- **Licensing Terms:** Personal quantitative research, educational analysis, and prototyping.
- **Production Boundary:** Does not confer commercial redistribution rights or real-time trading SLAs. Quotes reflect 15-minute exchange delays.
- **Aurxon QuantX Decision:** Used as an exploratory and research market-data connector. All outputs are explicitly tagged with `data_provider: "YFINANCE_LIVE"` and `classification: "LIVE_VERIFIED"` or `"DELAYED_VERIFIED"`.

### 3.4 Official Exchange Channels (NSE / BSE) & WAF Policy
- **WAF Guard:** National Stock Exchange web endpoints are protected by Akamai Bot Manager and Cloudflare WAF. Headless automated requests receive HTTP 403 Forbidden.
- **Anti-Circumvention Mandate:** Aurxon QuantX **strictly prohibits** unauthorized WAF bypass, automated session cookie tampering, or deceptive scraping headers.
- **Official Path:** Production deployments requiring real-time level-1 or level-2 tick feeds must integrate official licensed products (NSE Real-Time Data Feed / Authorized Vendor APIs such as Zerodha Kite Connect, Upstox, or Bloomberg/Refinitiv).

### 3.5 Alpha Vantage API
- **Policy:** Marked as **BLOCKED (UNCONFIGURED)** until a valid `ALPHA_VANTAGE_API_KEY` is supplied in the `.env` configuration file.
- **Quota Safeguard:** Free tier is strictly limited to 25 requests per day. The engine prevents automatic batch scans that would prematurely exhaust operator quota.
