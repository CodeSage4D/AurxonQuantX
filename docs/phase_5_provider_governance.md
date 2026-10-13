# Aurxon QuantX — Phase 5 Provider & Financial-Data Governance

## 1. Governance Principles & Legal Boundaries

**Aurxon QuantX** operates under strict regulatory and data rights boundaries. Because real-time tick redistribution and un-licensed market data redistribution carry severe compliance liabilities under SEBI and exchange regulations (NSE/BSE), Phase 5 formalizes the following legal and operational guardrails:

1. **Research & Paper-Trading Scope Only**: All features are strictly scoped to internal analysis, valuation modeling, and paper-trading simulation.
2. **Zero Broker Routing**: No broker APIs, order routing bridges, or real-money execution credentials are permitted or implemented.
3. **Yahoo Finance Research Limitation**: `yfinance` data is utilized strictly for non-commercial research, retrospective backtesting, and development benchmarking. Commercial redistribution without a direct exchange license is strictly prohibited.
4. **Data Classification Integrity**: Every market price and quote displayed in the platform carries provenance metadata indicating its origin, freshness, and classification.

---

## 2. Standardized Financial Data Classifications

Every quote, holding valuation, and order fill record must carry one of the following canonical classifications:

| Classification | Meaning | Intended Usage | UI Indicator |
| :--- | :--- | :--- | :--- |
| **`LIVE_EXCHANGE`** | Direct licensed feed from NSE/BSE | Production with direct exchange license only | Green tag `LIVE` |
| **`THIRD_PARTY_DELAYED`** | Legitimate delayed feed (15 min delay) | Permitted research use with vendor license | Amber tag `DELAYED (15m)` |
| **`HISTORICAL_ARCHIVE`** | Historical daily OHLCV end-of-day bars | Backtesting, factor computation, risk models | Blue tag `HISTORICAL` |
| **`CACHED_FALLBACK`** | Previously retrieved quote used during outage | Temporary offline display; flagged as stale | Orange tag `CACHED` |
| **`SYNTHETIC_BENCHMARK`** | Deterministic mathematical benchmark prices | Algorithm testing & unit validation | Purple tag `BENCHMARK` |
| **`DEMONSTRATION_SIMULATION`** | Paper-trading virtual execution simulation | Simulated order fills and portfolio rebalancing | Amber banner `SIMULATION` |
| **`UNVERIFIED`** | Price cannot be verified from a trusted source | Vetoes order fills; flagged as non-actionable | Red tag `UNVERIFIED` |

---

## 3. Data Freshness & Provenance Policies

### Provenance Tracking
In `paper_manager.py`, each `PaperOrderRecord` persists:
- `data_provenance`: Identifies the connector (e.g. `NSE_DIRECT`, `YFINANCE_RESEARCH`, `HISTORICAL_CACHE`, `SYNTHETIC_BENCHMARK`).
- `data_classification`: Canonical classification from the table above.
- `freshness_status`: `FRESH`, `STALE`, or `UNKNOWN`.

### Stale Data Safeguards
- Quotes older than 24 hours during market trading hours are tagged as `STALE`.
- If an asset price cannot be resolved from any permitted source, the system refuses to fabricate a price and sets position state to `UNPRICED`, halting automatic rebalancing execution on that security.

---

## 4. Real-Trading Safety Invariants

The following invariants are hardcoded into the platform:
- `ENABLE_REAL_TRADING = false` (locked in settings with startup assertion).
- No API client libraries for Indian brokers (Zerodha Kite, Upstox, Angel One, Groww, ICICI Direct) exist in the codebase.
- Rebalancing execution sequentially creates entries in `paper_orders` inside SQLite; it never emits external network requests.
