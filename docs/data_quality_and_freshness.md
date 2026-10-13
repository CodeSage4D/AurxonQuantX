# AURXONQuant — Data Quality, Provenance & Freshness Policy

**Phase:** 4 — Live Data & Company Research Intelligence Engine  
**Schemas:** `backend/app/schemas/market.py`  
**Status:** STRICTLY ENFORCED

---

## 1. Data Classification Taxonomy

Every market quote, historical bar, and financial statement observation in AURXON must carry an explicit `DataClassification` tag:

| Classification | Definition | Usage & Restrictions |
| :--- | :--- | :--- |
| `LIVE_VERIFIED` | Quote fetched directly from exchange or authorized broker with < 15 min delay | Fully eligible for live paper simulation |
| `DELAYED_VERIFIED` | Quote provided with standard 15-minute exchange-mandated statutory delay | Eligible for end-of-day research and daily bar simulation |
| `HISTORICAL_VERIFIED` | Closed historical candle or audited quarterly filing from official gazettes | Research and backtesting only; cannot execute intraday orders |
| `CACHED` / `CACHED_LOCAL` | Retrieved from local SQLite or disk snapshot within permissible TTL | Marked with cached retrieval timestamp |
| `SYNTHETIC_BENCHMARK` | Audited ground-truth calibration dataset (e.g. Nifty 50 benchmarks) | Deterministic test baseline; clearly badged in UI |
| `SYNTHETIC` | Algorithmically generated price paths for stress testing | Prohibited from paper portfolio balance calculations |
| `UNVERIFIED` | Data received from secondary aggregator without primary filing link | Prohibited from triggering paper trading tickets |
| `UNAVAILABLE` | No data feed reachable and symbol absent from local verified archive | Price set to `None`; clearly displayed as missing |

---

## 2. Time-Decay Freshness Policy

Freshness is computed dynamically based on the age of the observation:

```
Observation Age = Current_Timestamp - Observation_Timestamp
```

1. **`FRESH`**:
   - Trading Hours: $\le 15$ minutes old.
   - Non-Trading Hours: Closing price of the most recent active trading session.
2. **`STALE_ACCEPTABLE`**:
   - $15 \text{ mins} < \text{Age} \le 24 \text{ hours}$ (e.g. weekend or after-market review).
3. **`STALE_WARNING`**:
   - $\text{Age} > 24 \text{ hours}$ during active market sessions.
   - **Critical Safety Guard:** Automatically triggers `REJECTED: STALE_MARKET_DATA` veto on simulated paper orders.
4. **`OFFLINE_FROZEN`**:
   - Static benchmark fixture frozen at specific historical date for regression testing.

---

## 3. Data Integrity & Anti-Fabrication Invariants

1. **Zero Price Fabrication**: When an uncurated ticker is queried without a live network connection, the system returns `UNAVAILABLE` with `current_price = None`. It never copies prices from unrelated companies or generates plausible numbers.
2. **Missing Statement Fields**: If a company's balance sheet does not report Free Cash Flow or Debt, the field is stored as `None`. Downstream valuation models (such as DCF or Altman Z) gracefully exclude themselves rather than interpolating synthetic figures.
3. **Visual Transparency**: The UI displays distinct color-coded badges for `FRESH` (emerald), `STALE_ACCEPTABLE` (amber), `HISTORICAL` (cyan), and `UNAVAILABLE` (red).
