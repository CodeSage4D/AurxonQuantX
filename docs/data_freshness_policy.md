# AURXON Data Freshness Policy — Phase 2.2
**Project:** AURXONQuant  
**Milestone:** Phase 2.2 — Primary-Source Data Integration & Evidence Verification  
**Status:** ENFORCED  
**Date:** 2026-10-13  

---

## 1. Principles of Freshness Gates

Financial information changes across widely disparate timescales. Applying a single global freshness window (e.g., 24 hours) causes false alarms for annual statutory filings and dangerous complacency for intraday market quotes.

AURXONQuant enforces **category-specific freshness policies** with deterministic gate checks. When data exceeds its permitted freshness window, the platform:
1. Flags the data with a prominent `is_stale: True` warning tag.
2. Preserves the historical observation date and retrieval timestamp.
3. Blocks or qualifies any automated recommendation dependent on that metric.
4. Explains what specific information is missing or out of date.
5. Never synthesizes current market prices from stale historical snapshots.

---

## 2. Permitted Freshness Windows by Category

| Category | Typical Update Cadence | Permitted Max Age | Freshness Action on Expiry | Recommendation Impact |
| :--- | :--- | :--- | :--- | :--- |
| **INTRADAY_PRICE** | Real-time / 1-15 min | 15 minutes (during market hours: 09:15 - 15:30 IST) | Mark `STALE_WARNING`; display timestamp | Blocks real-time valuation; limits to EOD scenario |
| **END_OF_DAY_PRICE** | Daily after 16:00 IST | 24 hours (business days) / 72 hours (weekends) | Mark `HISTORICAL_VERIFIED` with date | Issues advisory qualification if trading session open |
| **MUTUAL_FUND_NAV** | Daily by 23:00 IST | 36 hours | Mark `STALE_ACCEPTABLE`; display NAV date | Flags tracking error and rolling return as historical |
| **PORTFOLIO_HOLDINGS** | Monthly (by 10th of succeeding month) | 45 days | Mark `STALE_WARNING` | Blocks high-conviction overlap conclusions |
| **FINANCIAL_STATEMENTS** | Quarterly / Annual | 120 days (quarterly) / 365 days (annual) | Mark `HISTORICAL_VERIFIED` with FY/Qtr | Discloses reporting lag; qualifies DCF projection |
| **IPO_PROSPECTUS** | Once per issue (DRHP / RHP) | 90 days (validity of RHP through listing) | Preserved as immutable benchmark fixture | Historical fixture; valid for issue analysis |
| **CORPORATE_ANNOUNCEMENT** | Ad-hoc / Event-driven | 48 hours | Archived into evidence timeline | Re-evaluates ongoing governance score |

---

## 3. Enforcement Implementation

Freshness evaluations are computed deterministically via `DataFreshnessRecord`:

```python
class DataFreshnessRecord(BaseModel):
    data_type: FreshnessCategory
    observation_date: str          # e.g., "2024-09-03" or "11-Oct-2024"
    as_of_timestamp: str           # ISO-8601 UTC timestamp
    max_permitted_age_hours: float # Configured threshold
    age_hours: float               # Elapsed time since observation
    is_stale: bool                 # age_hours > max_permitted_age_hours
    stale_warning: Optional[str]   # Explicit explanation of missing fresh data
```

When `is_stale == True`, downstream recommendation modules downgrade readiness gates from `ACTIVE_UNQUALIFIED` to `QUALIFIED_ADVISORY` or `BLOCKED_DEFICIENT`.
