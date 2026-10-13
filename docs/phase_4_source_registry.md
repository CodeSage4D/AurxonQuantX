# AURXONQuant — Phase 4 Source Registry Specification

**Phase:** 4 — Live Data & Company Research Intelligence Engine  
**Module:** `backend/app/sources/enhanced_registry.py`  
**API Endpoint:** `GET /api/v1/company/sources`  
**Status:** VALIDATED & DEPLOYED

---

## 1. Registry Architecture & Legal Data Governance

AURXONQuant operates under strict legal and evidentiary guidelines:
1. **Primary Regulatory & Exchange Feeds**: Preferred over unverified third-party scrapers.
2. **Search Engines as Discovery Only**: Web search and search APIs are utilized strictly for discovery and citation grounding; they are never treated as authoritative financial data providers.
3. **Restricted Services Policy**: No automated scraping of paywalled or terms-restricted websites (such as Moneycontrol, Bloomberg, or Economic Times premium) is permitted without authorized commercial APIs.
4. **Untrusted Input Boundary**: All external web data, news articles, and filing texts are treated as untrusted passive payloads and scrubbed against prompt injection before semantic extraction.

---

## 2. Permitted Source Inventory

| Source ID | Name & Category | Supported Scope | Data Fields | Rate Limits | Authentication | License & Permitted Usage | Health Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SRC_NSE_BSE` | National Stock Exchange & BSE Official Feeds (`EXCHANGE_OFFICIAL`) | All actively listed Indian equities, ETFs, Indices | LTP, OHLCV, 52W High/Low, Corporate LODR circulars | Max 30 req/min with jitter | None | Regulated statutory exchange disclosures. Private research use. | `HEALTHY` |
| `SRC_AMFI` | Association of Mutual Funds in India (`AMFI_AMC_OFFICIAL`) | >15,000 registered mutual fund schemes | Scheme Code, Scheme Name, NAV, Date | Max 60 req/min | None | Open public data feed for Indian mutual funds. | `HEALTHY` |
| `SRC_COMPANY_IR` | Official Issuer Investor Relations (`ISSUER_OFFICIAL`) | NSE/BSE listed corporate issuers | Balance sheets, P&L, Cash flows, Auditor notes, Presentations | On-demand (10s backoff) | None | Statutory corporate disclosures under SEBI LODR regulations. | `HEALTHY` |
| `SRC_RBI` | Reserve Bank of India DBIE (`CENTRAL_BANK_REGULATORY`) | Macro indicators, policy rates, G-Sec yields | Policy Repo Rate, SDF, MSF, 10Y G-Sec yield, CPI inflation | Max 20 req/min | None | Official public statistics (Creative Commons / Public Domain). | `HEALTHY` |
| `SRC_ALPHA_VANTAGE` | Alpha Vantage Market API (`AGGREGATOR`) | Indian equities with `.BSE`/`.NSE` | Daily OHLCV, volume, technical indicators | 25 req/day, 5 req/min | API Key (`ALPHA_VANTAGE_API_KEY`) | Commercial API with free tier for personal research. | `UNCONFIGURED` (Optional) |
| `SRC_BENCHMARK_ARCHIVE` | AURXON Curated Audited Archive (`SYNTHETIC_BENCHMARK`) | Curated Nifty 50 benchmarks (RELIANCE, TCS, INFY, etc.) | Daily OHLCV, audited fundamentals, Piotroski raw, ratios | Unlimited (Local disk) | None | Ground-truth calibration dataset for regression and offline tests. | `HEALTHY` |
| `SRC_WEB_DISCOVERY` | Permitted Regulatory & Web Portals (`DISCOVERY_TOOL`) | SEBI press, exchange circulars, business daily portals | Headlines, article text, publication dates, source links | Max 10 req/min | None | Public web news. Passive untrusted payload. | `HEALTHY` |

---

## 3. Health Tracking & Dynamic Probing

The enhanced registry maintains operational telemetry:
- `last_successful_fetch`: ISO 8601 timestamp of most recent successful data retrieval.
- `last_observation_time`: Timestamp of market or regulatory event observation.
- `health_status`: Dynamic state machine (`HEALTHY`, `DEGRADED`, `DOWN`, `OFFLINE_ONLY`, `UNCONFIGURED`).
- `fallback_policy`: Explicit cascade rules defining what happens when a primary source fails (e.g. fallback to disk cache, then benchmark archive, or return explicit `UNAVAILABLE` rather than fabricating numbers).
