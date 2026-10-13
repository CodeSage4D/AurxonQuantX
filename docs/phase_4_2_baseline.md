# Aurxon QuantX — Phase 4.2 Baseline and Provider Audit

**Product Identity:** Aurxon QuantX  
**Brand:** AURXON  
**Audit Date:** 2026-10-13  
**Auditor:** Principal Financial Data Engineer & AI Research Architect  
**Baseline Commit:** `7ad29f8` | **Target Milestone:** Phase 4.2  
**Repository:** `/home/karann/Documents/AURXONQuant`  
**Remote:** `git@github.com:CodeSage4D/AurxonQuantX.git`

---

## 1. Baseline Verification & Repository State

At the inception of Phase 4.2, the repository state was formally verified:
- **Git HEAD:** `7ad29f8faa10c31a871b549188f8e61ca36cec58` (`feat(phase-4.1): Live Data Verification, Persona Removal, Risk Policy & Quantitative Audit`).
- **Working Tree:** Clean, synchronized with `origin/main`.
- **Baseline Automated Test Suite:** 153 passed, 1 skipped (offline mode) in 2.65s.
- **Frontend Production Build:** Succeeded cleanly in 2.25s via `tsc && vite build`.
- **Checkpoint Tag:** Created `checkpoint-phase-4-2-start`.

---

## 2. Component Provenance & Architectural Audit

Every system component was audited to determine whether it relies on real external data, cached observations, offline fixtures, or heuristic rules:

| Component | Module Location | Implementation Type | True Provenance | Operational Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **Mutual Fund Feed** | `connectors/amfi.py` | Official HTTP Parser | **LIVE_VERIFIED** (Real Data) | Fetches official daily NAV text feed (`NAVAll.txt`) |
| **Central Bank Macro** | `sources/provider_probe.py` | Official Portal Probe | **LIVE_VERIFIED** (Real Data) | Verified HTTP 200 on `https://rbi.org.in/` |
| **Equity Price History** | `market_data/store.py` | yfinance Market Connector | **LIVE_VERIFIED** (Real Data) | Fetches live daily OHLCV bars for Indian equities (`.NS`) |
| **Official Exchange Feed**| `market_data/nse_connector.py`| Exchange HTTP Connector | **BLOCKED (WAF)** | Blocked by Akamai WAF without browser session cookies |
| **Commercial Aggregator** | `sources/enhanced_registry.py`| Alpha Vantage API Client | **BLOCKED (UNCONFIGURED)** | Free tier key not set in environment |
| **Benchmark Archive** | `trading/fixtures.py` | Deterministic Generators | **SYNTHETIC_BENCHMARK** | Provides reproducible calibration bars offline |
| **Company Resolver** | `research/company_resolver.py`| Canonical Master Trie | **DETERMINISTIC_RULES** | Matches ISIN, symbol, historical aliases, and umbrellas |
| **Quantitative Analytics** | `analytics/company_quant.py` | Pure-Python Math Engine | **DETERMINISTIC_CALC** | Exact returns, volatility, MDD, moving averages |
| **Specialist Perspectives**| `research/company_researcher.py`| Software Rules / Engines | **RULE_BASED** | 6 software engines (Fundamentals, Technicals, etc.) |
| **Adversarial Review** | `research/company_researcher.py`| Invalidation Engine | **RULE_BASED** | Generates mandatory bear-case invalidation conditions |
| **Paper-Trading Risks** | `trading/risk_engine.py` | Hard Gatekeeper | **FAIL_CLOSED_GUARD** | Enforces 30% drawdown ceiling, daily loss stop, kill-switch |
| **Screen OCR Engine** | `companion/screen_ocr.py` | Tesseract v5 + Redactor | **LOCAL_OCR / PRIVACY** | Extracts Indian stock tickers, redacts OTPs/passwords |
| **Document Ingestion** | `ingestion/parser.py` | PyPDF + AST Table Validator| **SECURITY_PARSER** | Disarms prompt injection, validates accounting sums |

---

## 3. Reproduction of Phase 4.1 Live-Integration Tests

The live provider integration test was executed with external network permissions:
```bash
RUN_LIVE_PROVIDER_TESTS=1 PYTHONPATH=backend .venv/bin/pytest backend/tests/test_phase_4_1_live_providers.py -v -k test_opt_in_live_amfi_and_equity_fetching
```
**Outcome:** **PASSED [100%] in 1.95s**.
- Statutory AMFI feed returned HTTP 200 with ~15,000 live mutual fund schemes.
- `yfinance` retrieved active daily bars for `RELIANCE.NS`.

---

## 4. Discrepancy Investigation: 5-Day Exploratory Tests vs. 252-Bar Coverage Claim

### 4.1 Identified Discrepancy
In Phase 4.1 exploratory verification:
1. `provider_probe.py` executed a lightweight health check via `t.history(period="5d")`, which returned **4 bars** for equities and 5 bars for indices.
2. Meanwhile, test documentation cited "252-bar coverage", which is the nominal academic convention for a US trading year.

### 4.2 Empirical Investigation & Ground Truth
An empirical network query was executed across representative Indian securities (`RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `HDFCBANK.NS`, `^NSEI`) over a 1-year window (`period="1y"`):
- **Actual Trading Sessions Returned:** Exactly **247 trading bars** from `2025-10-13` to `2026-10-13`.
- **Reason:** In India, the National Stock Exchange observes weekends plus statutory holidays (Diwali, Republic Day, Independence Day, Holi, Good Friday, Eid, Gandhi Jayanti, Dussehra, etc.), reducing the trading sessions in a 365-calendar-day year to 245–249 days.
- **Architectural Defect Discovered:** `company_quant.py` previously mandated `n >= 252` to calculate `returns_1y_pct`. Consequently, an authentic 1-year historical dataset with 247 bars yielded `None` for 1-Year returns!

### 4.3 Remediation Implemented
1. Updated `company_quant.py` to evaluate 1-Year returns over $n \ge 252$ when available, or $n \ge 245$ (representing a complete Indian exchange calendar year).
2. Prohibited the silent invention or forward-filling of fictitious bars to reach 252.
3. Added metadata fields to research dossiers: `historical_bars_count` (e.g. 247) and `historical_date_range` (`2025-10-13 to 2026-10-13`).
