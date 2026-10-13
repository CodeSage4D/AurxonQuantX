# AURXONQuant — Phase 4 Baseline Repository Audit & Architecture Plan

**Phase:** Phase 4 — Live Data & Company Research Intelligence Engine  
**Baseline Git Commit:** `ffe4ee73488f69c0bed232ae226498e0389491f3`  
**Checkpoint Tag:** `checkpoint-phase-4-start`  
**Date:** 2026-10-13  
**Status:** AUDITED & VALIDATED  
**Engineers:** Principal Quant Architect, Indian Market Data Engineer, Security Lead  

---

## 1. Executive Baseline State

Prior to initiating Phase 4 feature development, an exhaustive audit was performed on repository commit `ffe4ee7`:

- **Git Working Tree:** Completely clean, zero uncommitted modifications.
- **Backend Test Suite:** **131 tests passing out of 131 tests** in 2.67s (`PYTHONPATH=backend .venv/bin/pytest backend/tests/`).
- **Frontend Production Build:** **Clean build** with Vite v6.4.4 in 2.23s (dist bundle 262 kB JS, 9.01 kB CSS).
- **Security & Safety Invariants:** `ENABLE_REAL_TRADING = false` strictly enforced. Zero live broker order routing or real-money execution capabilities.

---

## 2. Component Inventory & Audit Findings

### 2.1 Existing Data Providers & Sources of Truth
- **AMFI NAV Connector (`backend/app/connectors/amfi_connector.py`):**
  - Connects to official AMFI text feed (`portal.amfiindia.com/DownloadNAVHistoryReport_PD.aspx`).
  - Supports live network fetching and falling back to cached local files (`data/cache/amfi_nav_history.txt`).
  - Strict observation date, net asset value, scheme code, and scheme name normalization.
- **NSE / Market Connector (`backend/app/market_data/nse_connector.py`):**
  - Handles symbols (`RELIANCE.NS`, `TCS.NS`, etc.).
  - Distinguishes data classifications: `LIVE_VERIFIED`, `DELAYED_VERIFIED`, `CACHED_LOCAL`, `SYNTHETIC_BENCHMARK`, and `UNAVAILABLE`.
  - Rejects unverified tickers with `classification = UNAVAILABLE` and `current_price = None` rather than fabricating numbers.
- **Source Registry (`backend/app/sources/registry.py`):**
  - Tracks 6 sources (`SRC_SEBI`, `SRC_NSE_BSE`, `SRC_ISSUER_PROSPECTUS`, `SRC_AMFI`, `SRC_AMC_SID`, `SRC_BENCHMARK_ARCHIVE`).
  - *Gap for Phase 4:* Missing structured metadata for RBI, corporate disclosures, authorized web search endpoints, company filing repositories, symbol coverage mapping, and operational health probes.

### 2.2 Entity Resolution & Company Identity
- *Current State:* The system relies on string normalization (strip `.NS`/`.BO`, uppercase).
- *Gap for Phase 4:* No centralized company registry resolving legal entities (e.g. "Reliance Industries Limited", "RIL", "RELIANCE", "INE002A01018") to an unambiguous canonical instrument record with exchange, ISIN, listing status, and alias resolution.
- *Ambiguity Risk:* Queries like "Tata", "Bajaj", or "HDFC" are multi-entity conglomerates; system must detect ambiguity and prompt for clarification rather than hallucinating an identity.

### 2.3 Market Data & Historical Store
- *Current State:* `HistoricalSeriesContract` (`backend/app/schemas/historical_data.py`) supports strongly typed daily/intraday bars, timestamps with timezones, and corporate actions.
- *Gap for Phase 4:* Needs a persistent store (`MarketDataStore` in SQLite) for normalized company fundamentals, quarterly balance sheets, P&L statements, cash flows, historical OHLCV, and corporate actions with explicit observation and retrieval timestamps, currency, units, and freshness markers.

### 2.4 Research Orchestrator & Multi-Specialist Evidence Review
- *Current State:* `EvidenceLoopWorkflow` (`backend/app/orchestration/evidence_loop.py`) runs parallel tasks, sanitizes prompt injection (`sanitize_untrusted_content`), deduplicates claims with SHA-256 fingerprints, and logs to `audit_ledger`.
- *Gap for Phase 4:* Lacks dedicated modular specialist agents (Fundamentals Specialist, Price Trend/Technicals Specialist, Valuation & Quality Specialist, News & Corporate Action Specialist, Downside & Liquidity Risk Specialist, and Adversarial Invalidation Specialist).
- *Strict Invariant:* Specialist agents must share an immutable evidence ledger; deterministic financial math and risk limits veto any agent consensus.

### 2.5 Paper-Trading Integration & Safety Barrier
- *Current State:* `PaperPortfolioManager` (`backend/app/trading/paper_manager.py`) has cash conservation, FIFO cost accounting, peak drawdown circuit breaker, daily loss limit (including unrealized P&L), and stale quote veto.
- *Phase 4 Requirement:* Research conclusions must NOT automatically execute paper trades. A company research dossier can only emit a *Paper Trading Consideration Eligibility Ticket* after passing all data quality and risk gates.

---

## 3. Staged Implementation Plan for Phase 4

- **Stage 1 — Source Registry & Company Identity:**
  - Build `backend/app/sources/enhanced_registry.py` tracking update intervals, quotas, permitted licenses, rate limits, and health probes.
  - Build `backend/app/research/company_resolver.py` resolving legal name, NSE/BSE symbols, ISIN, and aliases, with explicit ambiguity detection.
- **Stage 2 — Market Data & Historical Store:**
  - Build `backend/app/market_data/store.py` (SQLite-backed store for normalized quotes, OHLCV, quarterly financials, and corporate actions).
  - Implement reusable adapters with normalized metadata contracts (`LIVE`, `DELAYED`, `HISTORICAL`, `STALE`, `FIXTURE`, `SIMULATED`, `UNAVAILABLE`).
- **Stage 3 — Web Research & Document Intelligence:**
  - Implement `backend/app/research/web_researcher.py` and document extractor supporting filings, results announcements, and credible news.
  - Enforce untrusted content sanitization, extraction uncertainty, and source attribution.
- **Stage 4 — Deterministic Quantitative & Financial Analysis:**
  - Implement `backend/app/analytics/company_quant.py` calculating returns, momentum, rolling volatility, benchmark relative strength (vs NIFTY50), trend, fundamental margins, debt/equity, and FCF trends.
- **Stage 5 — Modular Specialist Research Roles & Evidence Review:**
  - Implement 6 specialized research analysts:
    1. Fundamentals Specialist
    2. Technicals & Price Trend Specialist
    3. Valuation & Financial Quality Specialist
    4. Corporate Actions & News Specialist
    5. Downside & Liquidity Risk Specialist
    6. Adversarial Review & Counter-Thesis Specialist
  - Synthesizer generating bull, base, and bear scenarios with invalidation criteria.
- **Stage 6 — Research Report UX & UI Integration:**
  - Build `frontend/src/components/CompanyResearchView.tsx` integrated into the top navigation.
  - Implement company search, identity card, data freshness badge, fundamental trends, scenario breakdown, and paper-trading eligibility gate.
- **Stage 7 — Paper-Trading Safety Verification:**
  - Wire paper-trading consideration gates to verify data freshness, price support, and risk limits before simulated submission.
- **Stage 8 — Test Suite, Documentation & Release Gate:**
  - Author reproducible test suite covering entity resolution, ambiguous symbols, staleness veto, financial math, adversarial review, and UI regressions.
  - Deliver the complete Phase 4 documentation suite in `docs/`.

---

## 4. Safety & Operational Constraints

1. `ENABLE_REAL_TRADING = false` strictly preserved.
2. No fabricated prices for uncurated tickers.
3. Tabular typography (`tabular-nums`) maintained across all components.
4. All claims backed by clickable source links or designated as inferred/simulated.
