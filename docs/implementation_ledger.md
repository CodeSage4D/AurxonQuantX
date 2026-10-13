# AURXON Master Implementation Ledger

**Project:** AURXON Investment Intelligence Hub  
**Founder Operations Mode:** Private, Single-Operator, Indian Markets  
**Current Milestone:** Phase 1.5 — Trust, Reliability and Integration Gate (COMPLETE)  
**Last Updated:** October 13, 2026  

---

## 1. Architectural Decision Records (ADRs)

| ADR ID | Decision Title | Status | Rationale / Tradeoff |
| :--- | :--- | :--- | :--- |
| **ADR-01** | **Local Hardware LLM Exclusion** | Accepted | Host has 7.5 GB RAM total (~2.5 GB available). Local 7B+ models cause extreme swap thrashing on CPU. Decision: Use cloud provider adapters (OpenAI, Groq) with an offline deterministic heuristic engine for zero-cost testing. |
| **ADR-02** | **Deterministic Financial Calculations** | Accepted | LLMs are strictly prohibited from calculating financial ratios or valuations. All Graham, DCF, Piotroski, Altman Z, Sharpe, and Sortino calculations are computed in pure Python (NumPy/Pandas). |
| **ADR-03** | **Tamper-Evident Hash-Chained Audit Ledger** | Accepted | Standard SQLite is mutable on disk. Calling it immutable is inaccurate. Implemented sequential SHA-256 hash chaining ($\text{prev\_hash} \to \text{chained\_hash}$) with automatic integrity verification across the entire chain. |
| **ADR-04** | **Data Provenance & Classification** | Accepted | All quotes and filings must carry explicit classification (`LIVE_EXCHANGE`, `DELAYED_EXCHANGE`, `THIRD_PARTY_DELAYED`, `CACHED_LOCAL`, `HISTORICAL_FILING`, `SYNTHETIC_BENCHMARK`, `UNAVAILABLE`). Scraping aggregators (Yahoo Finance) is never represented as official exchange tick feeds. |
| **ADR-05** | **Banking Sector Valuation Guard** | Accepted | Commercial Banks (`HDFCBANK`, `ICICIBANK`, `SBIN`) hold deposits as liabilities and lack traditional working capital and enterprise FCF. Suppressed Altman Z and industrial DCF for banks to prevent false distress alerts. |
| **ADR-06** | **Zero Credential Harvesting & Trading Hard Lock** | Accepted | Real-money trading is hard-locked (`ENABLE_REAL_TRADING = false`). Screen companion uses regex redaction to strip OTPs, passwords, and card numbers before processing. |
| **ADR-07** | **Untrusted Document Ingestion & Injection Neutralization** | Accepted | Ingested PDFs and HTML filings are strictly treated as untrusted text. Active prompt injection directives (`Ignore instructions...`, `SYSTEM OVERRIDE`) are scrubbed and quarantined before reaching model synthesis. |
| **ADR-08** | **Deterministic Mutual Fund Overlap & Direct Drag Math** | Accepted | Scheme overlap is computed as $\sum \min(w_{A,i}, w_{B,i})$. Direct vs Regular compounding expense savings are evaluated deterministically over 10-year horizons with zero LLM guesswork. |
| **ADR-09** | **7-Point Multi-Dimensional IPO Decision Framework** | Accepted | IPO evaluation strictly decouples business quality from IPO valuation and separates listing-day speculation from long-term ownership, forbidding any speculative listing gain promises. |

---

## 2. Milestone Ledger & Verification History

### Phase 0: Mandatory Environment Audit
- **Status:** Complete & Signed Off
- **Artifact:** `docs/phase_0_environment_audit_report.md`
- **Verified Environment:** Linux Mint 22.3, 4 vCPUs, 7.5 GB RAM, Python 3.12.3 in `.venv`, Node.js v20.20.2, Tesseract OCR v5, SQLite 3.45.1.

### Phase 1: Smallest Working Vertical Slice
- **Status:** Complete & Signed Off
- **Deliverables:**
  - FastAPI backend with SSE streaming (`/api/v1/research/stream`).
  - NSE data connector with disk cache & benchmark fixtures.
  - Deterministic Graham, DCF, and Piotroski calculation engine.
  - Dark-mode glassmorphic desktop interface (Vite + React + TS).
  - Chrome Manifest V3 companion side panel.
  - 18 passing tests.

### Phase 1.5: Trust, Reliability and Integration Gate
- **Status:** Complete & Signed Off (All 8 Acceptance Gates Passed)
- **Delivered Improvements:**
  - **Workstream A:** Baseline audit reproduced; 18 initial tests verified; frontend build verified.
  - **Workstream B:** Formal data provenance spec, explicit classification enum, freshness tracking, and unavailable-state handling.
  - **Workstream C:** OpenAI and Groq adapters implemented; failure modes tested (missing keys, 401 auth, timeouts, 429 rate limits, malformed JSON); transparent fallback labelling.
  - **Workstream D:** Parallel sub-agent execution demonstrated with concurrency telemetry; prompt injection neutralization; claim deduplication.
  - **Workstream E:** Financial validation report; 3x3 DCF sensitivity matrix; banking sector exclusion for Altman Z and industrial DCF.
  - **Workstream F:** Cryptographic hash-chain ledger in SQLite WAL mode; `/api/v1/audit/integrity` endpoint; tampering detection verified.
  - **Workstream G:** Desktop and screen companion permission clarity verified; 33 passing automated tests.

### Phase 2: IPO Prospectus Intelligence + Mutual Fund & ETF Research
- **Status:** Complete & Signed Off (All Gates Passed)
- **Deliverables:**
  - `backend/app/sources/registry.py` & `docs/source_registry.md`: Source governance registry (SEBI, NSE, AMFI, AMC Factsheets, DRHP/RHP, Aggregators).
  - `backend/app/ingestion/parser.py` & `docs/document_ingestion_spec.md`: Untrusted PDF/HTML parser with prompt-injection defense and table extraction.
  - `backend/app/ipo/analyzer.py` & `docs/ipo_research_spec.md`: Deterministic IPO structure, dilution %, promoter holding shift, financial CAGR, valuation peer comparisons, and 7-point decision matrix with curated ground truth benchmarks (`BAJAJHFL`, `TATATECH`).
  - `backend/app/funds/analyzer.py` & `docs/mutual_fund_etf_research_spec.md`: Mutual fund CAGR, rolling returns, portfolio overlap math, 10Y Direct vs Regular compounding savings, ETF tracking error, and goal-based asset allocation proposals.
  - FastAPI REST Endpoints: `/api/v1/sources`, `/api/v1/ingestion/upload`, `/api/v1/ipo/list`, `/api/v1/ipo/analyze/{symbol}`, `/api/v1/funds/list`, `/api/v1/funds/compare`, `/api/v1/funds/allocate`, `/api/v1/export/report`.
  - Frontend React/TS components: `IPOResearchView.tsx`, `FundResearchView.tsx`, `SourcesInspectionModal.tsx`, and Markdown dossier export.
  - 52 passing automated tests in 1.47s; clean production bundle build in 2.15s.

### Phase 2.1: Independent Validation Gate
- **Status:** Complete & Signed Off (All 6 Workstreams Verified)
- **Deliverables:**
  - `docs/phase_2_1_validation_report.md`: Executive gate assessment and workstream summaries.
  - `docs/fixture_provenance_audit.md`: Sourced ledger for all IPO, mutual fund, ETF, and stock fixtures.
  - `docs/ipo_quantitative_reference_tests.md`: Mathematical references for issue split, dilution, CAGR limits, and promoter bounds.
  - `docs/fund_quantitative_reference_tests.md`: Mathematical references for CAGR, tracking error, direct savings, overlap, and IDCW discipline.
  - `docs/document_extraction_accuracy.md`: Searchable vs scanned PDF boundaries, Indian numbers, accounting parentheses, and prompt injection defense.
  - `docs/phase_2_1_issue_register.md`: 9 audit findings logged and 100% resolved.
  - `docs/phase_2_1_issue_register.md`: 9 audit findings logged and 100% resolved.
  - 66 passing automated tests in 1.62s; clean production bundle build in 2.08s.

---

## 3. Milestone 4: Phase 2.2 — Primary-Source Data Integration, Evidence Verification & Recommendation Readiness
- **Commit:** `[Current Phase 2.2 Commit]`
- **Date:** 2026-10-13
- **Delivered Capabilities:**
  - **Financial Semantics Remediation (Workstream A):** Eliminated misleading `0.0` sentinels for loss-making issuers. Implemented `TypedFinancialMetric` and `MetricStatus` (VALID, NOT_APPLICABLE, DATA_UNAVAILABLE, CALCULATION_ERROR). Added explicit diagnostic reasons for negative/zero/missing EPS and undefined CAGR turnaround cases.
  - **Primary-Source Registry & AMFI Connector (Workstream B & E):** Integrated official AMFI India statutory daily NAV file parser (`https://www.amfiindia.com/spages/NAVAll.txt`) supporting scheme code and ISIN lookup with robust cached snapshot fallback.
  - **Category-Specific Freshness Policies (Workstream C):** Instituted `DataFreshnessRecord` defining independent freshness thresholds by data category (intraday price, daily NAV, monthly holdings, prospectus filing).
  - **Prospectus Field Lineage & Ground-Truth Provenance (Workstream D & F):** Created `FieldLineageRecord` capturing PDF page numbers, exact quoted text, normalized values, and official SEBI URLs for `BAJAJHFL` and `TATATECH`.
  - **Multi-Dimensional Recommendation Readiness Gates (Workstream G):** Replaced black-box scores with multi-dimensional gates (`ACTIVE_UNQUALIFIED`, `QUALIFIED_ADVISORY`, `BLOCKED_DEFICIENT`) covering business quality, financial quality, governance, valuation, and evidence integrity. Blocked listing-day pop promises.
  - **Frontend Transparency (Workstream H):** Added statutory filing lineage inspector, recommendation readiness gate cards, and typed null-safe valuation displays in React interface.
  - **Release Suite:** 80 passing automated backend tests in 1.63s; clean production frontend build in 2.37s.

---

## 4. Test Matrix Summary

```
======================== 80 passed, 1 warning in 1.63s =========================
- test_api_endpoints.py: 11 passed (Health, Quote, Sync, Audit Records, Integrity, Companion, Sources, IPO, Funds, Export, Ingestion Upload)
- test_audit_ledger.py: 2 passed (Sequential Hash-Chaining, Tampering Detection)
- test_document_ingestion.py: 2 passed (Text/HTML Ingestion with Prompt Injection, Empty/Corrupt PDF Handling)
- test_evidence_loop.py: 4 passed (Streaming Execution, Prompt Injection Defense, Dedup, Contradictions)
- test_fund_analyzer.py: 6 passed (CAGR Math, Portfolio Overlap, Direct Compounding Drag, Tracking Error, Fund Comparison Logic, Goal-Based Allocation)
- test_ipo_analyzer.py: 4 passed (Arithmetic Precision, CAGR Math, Bajaj Housing Finance Dossier, Tata Technologies Dossier)
- test_model_registry.py: 6 passed (Missing Keys, 401 Auth, Timeout, 429 Rate Limit, Bad Output, Fallback)
- test_nse_connector.py: 4 passed (Normalization, Provenance, Bank Sector Detection, Unavailable State)
- test_phase_2_1_extraction_security.py: 4 passed (Accounting Parentheses, Scanned PDF Diagnostic, Upload Size Cap, Injection Defense)
- test_phase_2_1_fund_math.py: 5 passed (CAGR Reference, Direct Savings, Tracking Error Tolerance, Overlap Math, Benchmark Alignment)
- test_phase_2_1_ipo_math.py: 5 passed (Issue Structure & Dilution, Promoter Bounds, CAGR Limits, Negative EPS, Bajaj Cross-Check)
- test_phase_2_2_semantics_and_connectors.py: 14 passed (Negative/Zero/Missing EPS, CAGR Semantics, AMFI Parser & Lookup, IPO Lineage, Readiness Gates, Endpoints)
- test_screen_ocr.py: 3 passed (Symbol Detection, Privacy Redaction, Pause Control)
- test_source_registry.py: 2 passed (Default Sources Registered, Custom Source Registration)
- test_valuation.py: 8 passed (Graham, DCF, Sensitivity Matrix, Bank Exclusion, Piotroski, Altman Z, Risk Metrics, Dossier)
```

---

## 5. Unresolved Risks & Next Phase Roadmap

1. **Unresolved Risks:**
   - **External LLM Credentials:** `OPENAI_API_KEY` and `GROQ_API_KEY` remain optional. System operates reliably in offline demonstration/heuristic mode.
   - **Multi-Page Scanned PDF OCR:** Ingestion pipeline supports searchable PDFs. Scanned image-only PDFs return explicit diagnostic failure messages; full optical OCR pipeline deferred to Phase 4 toolchain enhancements.
2. **Next Milestone (Phase 3):**
   - Trading research & historical backtesting module.
   - Portfolio factor attribution and multi-asset risk parity modeling.
   - Cross-asset correlation stress testing under historical Indian market dislocations (2008, 2020).
