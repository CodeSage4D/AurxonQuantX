# AURXON Data Provenance & Market Data Specification

**Status:** Hardened Specification  
**Version:** 1.0.0 (Phase 1.5 Gate)  
**Target:** Indian Equities & Derivatives (NSE / BSE)  

---

## 1. Principles of Data Provenance

1. **Explicit Classification Invariance:** Every price quote, corporate filing, and fundamental ratio must carry an explicit [DataClassification](file:///home/karann/Documents/AURXONQuant/backend/app/schemas/market.py#L9) tag.
2. **Never Call Mock Data "Live":** Test fixtures and regression benchmarks are strictly tagged as `SYNTHETIC_BENCHMARK`. They are never presented as real-time market data.
3. **No Unwarranted Official Attribution:** Scraping third-party aggregators such as Yahoo Finance or yfinance is classified as `THIRD_PARTY_DELAYED`. They are never represented as official exchange feeds.
4. **Graceful Unavailable State:** When a symbol cannot be resolved or external networks are unreachable, the connector emits `UNAVAILABLE` (`current_price: None`) rather than fabricating synthetic prices.
5. **Separation of Quotes and Audited Disclosures:** Real-time prices decay rapidly (15-minute freshness window), whereas audited balance sheets decay over quarterly cycles (90-day window).

---

## 2. Classification Hierarchy

| Classification | Definition | Typical Latency / Freshness | Usage in AURXON |
| :--- | :--- | :--- | :--- |
| `LIVE_EXCHANGE` | Direct tick stream from NSE/BSE authorized broker API / feed. | < 500 ms | Paper trading and live execution research (when authorized). |
| `DELAYED_EXCHANGE` | Exchange website snapshot with mandatory 15-minute delay. | 15 minutes | General valuation research. |
| `THIRD_PARTY_DELAYED` | Aggregated feed (Yahoo Finance, Google Finance). | 15–30 minutes | Secondary reference. Clear disclaimer attached. |
| `CACHED_LOCAL` | Locally stored snapshot from prior session in `data/cache/`. | Variable | Offline resiliency, rate-limit defense. |
| `HISTORICAL_FILING` | Regulated disclosure from MCA/BSE/NSE (Q1-Q4 audited results). | Audited quarterly | Fundamental ratio computation (Piotroski, DCF). |
| `SYNTHETIC_BENCHMARK`| Curated offline Nifty 50 reference fixture. | Frozen | Deterministic unit and integration tests. |
| `UNAVAILABLE` | Resolution failed across all providers and local cache. | N/A | Terminal state. Triggers `ABSTAIN_DATA_DEFICIENT`. |

---

## 3. Freshness Assessment Matrix

```
Current Time - Retrieved Time (Δt)
├── Δt < 15 minutes  ──► FRESH
├── Δt < 24 hours    ──► STALE_ACCEPTABLE (Post-market / weekend)
└── Δt >= 24 hours   ──► STALE_WARNING (Requires user acknowledgement)
```

Static test fixtures carry `FreshnessStatus.OFFLINE_FROZEN` to indicate that time decay does not invalidate their benchmark purpose.

---

## 4. Financial Sector Handling (Banks & NBFCs)

Commercial banks (`HDFCBANK`, `ICICIBANK`, `SBIN`) and NBFCs (`BAJFINANCE`) differ fundamentally from industrial firms:
- Customer deposits are liabilities, not working capital.
- Traditional Free Cash Flow (FCF) and debt-to-equity metrics are mathematically invalid.
- Tickers classified with `is_financial_institution: True` suppress corporate debt and industrial DCF metrics, and instead mandate banking metrics (NIM, CRAR, Net NPA, ROA).
