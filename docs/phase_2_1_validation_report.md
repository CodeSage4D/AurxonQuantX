# AURXONQuant — Phase 2.1 Independent Validation Gate Report
## Verification of IPO Prospectus Intelligence + Mutual Fund & ETF Research

**Audit Date:** October 13, 2026  
**Auditor / Lead:** Principal Financial-Software Architect, Indian Equity Research Analyst, Security Engineer & QA Lead  
**Commit Inspected:** `1a45efc` (`feat(ipo-funds): Phase 2 IPO Prospectus Intelligence and Mutual Fund Research`)  
**Gate Status:** **ALL AUDIT GATES PASSED (66/66 Backend Tests Verified, 0 Build Errors)**

---

## 1. Executive Gate Assessment

This independent validation gate was conducted to rigorously verify whether the IPO and mutual fund/ETF research modules are:
1. **Financially Correct:** Deterministic mathematical arithmetic verified with analytical references and numerical tolerances ($\pm 0.001\%$). Zero LLM hallucinations of numbers or valuation ratios.
2. **Traceable to Reliable Data:** All fixtures traced to official regulatory filings (SEBI RHP) or statutory AMC disclosures. Explicitly classified as `HISTORICAL_FILING` or `SYNTHETIC_BENCHMARK`.
3. **Safe for Investment Research:** Real-money execution hard-locked, prompt injection vectors actively sanitized, file upload DoS limits enforced, loopback binding preserved, and honest documentation of scanned PDF limitations.

---

## 2. Workstream Audit Results

| Workstream | Focus Area | Status | Key Findings & Evidence |
| :--- | :--- | :---: | :--- |
| **Workstream A** | **Source-of-Truth Audit** | **PASS** | Sourced and cross-checked `BAJAJHFL` (SEBI RHP Sept 2024), `TATATECH` (SEBI RHP Nov 2023), `PPFAS_FLEXI`, `NIFTYBEES`, and `MIRAE_LARGE` (AMC Factsheets June 2024). All fixtures classified strictly as `HISTORICAL_FILING`. Zero unverified claims of live data. Documented in `docs/fixture_provenance_audit.md`. |
| **Workstream B** | **Independent IPO Mathematics** | **PASS** | Verified issue split, pre/post share counts, dilution % ($6.10\%$), promoter post-holding bounds [$88.58\%, 93.89\%$], CAGR mathematical limits on negative/zero base values, loss-making P/E guards, and peer comparison alignment. Verified by `test_phase_2_1_ipo_math.py`. Documented in `docs/ipo_quantitative_reference_tests.md`. |
| **Workstream C** | **Independent Fund & ETF Mathematics** | **PASS** | Verified CAGR ($20.11\%$), 10Y direct vs regular compounding drag ($₹2.04\text{ Lakhs}$ savings), tracking error ($\pm 0.01\%$), portfolio overlap arithmetic across disjoint/identical/asymmetric cases, non-universal ETF benchmarks, and IDCW total return discipline. Verified by `test_phase_2_1_fund_math.py`. Documented in `docs/fund_quantitative_reference_tests.md`. |
| **Workstream D** | **Document Extraction Accuracy** | **PASS** | Searchable PDF parsing verified. Scanned image PDF boundary honestly declared as **BLOCKED / NOT SUPPORTED** in `pypdf` without pretending OCR succeeds. Accounting parentheses `(5,200.0)` $\to -5200.0$ and Indian number commas verified. Documented in `docs/document_extraction_accuracy.md`. |
| **Workstream E** | **Research & Recommendation Integrity** | **PASS** | Every conclusion separates business quality from valuation sanity, distinguishes facts vs estimates, and explicitly refuses to promise listing pops or allotment. Source registry reliability weights documented as Bayesian heuristic priors, not empirical probabilities. |
| **Workstream F** | **Security & Audit** | **PASS** | Enforced 50 MB upload limit (`MAX_UPLOAD_SIZE_BYTES`) with HTTP 413 to prevent memory exhaustion DoS. Hardened prompt injection regex patterns. Loopback binding (`127.0.0.1`) and SQLite hash-chain threat model documented. |

---

## 3. Reproducible Test Suite & Production Build

### 3.1 Backend Test Execution
- **Command:** `PYTHONPATH=backend .venv/bin/pytest backend/tests -v`
- **Exit Code:** `0`
- **Execution Time:** `1.62s`
- **Total Test Count:** **66 passed, 0 failed**

```text
backend/tests/test_api_endpoints.py (11 passed)
backend/tests/test_audit_ledger.py (2 passed)
backend/tests/test_document_ingestion.py (2 passed)
backend/tests/test_evidence_loop.py (4 passed)
backend/tests/test_fund_analyzer.py (6 passed)
backend/tests/test_ipo_analyzer.py (4 passed)
backend/tests/test_model_registry.py (6 passed)
backend/tests/test_nse_connector.py (4 passed)
backend/tests/test_phase_2_1_extraction_security.py (4 passed)
backend/tests/test_phase_2_1_fund_math.py (5 passed)
backend/tests/test_phase_2_1_ipo_math.py (5 passed)
backend/tests/test_screen_ocr.py (3 passed)
backend/tests/test_source_registry.py (2 passed)
backend/tests/test_valuation.py (8 passed)

======================== 66 passed, 1 warning in 1.62s =========================
```

### 3.2 Frontend Production Build Execution
- **Command:** `npm run build` (in `/home/karann/Documents/AURXONQuant/frontend`)
- **Exit Code:** `0`
- **Execution Time:** `2.08s`
- **Artifacts:**
  - `dist/index.html`: `1.12 kB`
  - `dist/assets/index-dFPiwz-p.css`: `9.42 kB`
  - `dist/assets/index-BYqvJRFS.js`: `218.79 kB`
- **TypeScript strict checks (`tsc`):** 0 errors.

---

## 4. Operational Boundaries & Offline Verification

1. **What Works Completely Offline:**
   - Full IPO Prospectus Dossiers (`BAJAJHFL`, `TATATECH`).
   - Mutual fund comparison, overlap calculations, direct vs regular fee compounding simulations, and goal-based asset allocation.
   - Searchable PDF, HTML, and text ingestion with prompt-injection neutralization and accounting parentheses parsing.
   - Deterministic valuations (Graham, DCF 3x3 sensitivity grid, Piotroski, Altman Z, risk metrics).
   - Sequential SHA-256 hash-chained audit ledger.
   - Research report Markdown exports.
2. **What Requires External Credentials / Network:**
   - Live cloud LLM models (OpenAI, Groq): Requires `OPENAI_API_KEY` or `GROQ_API_KEY`. When absent, transparently uses deterministic heuristic fallback.
   - Live exchange web feeds: When offline, cleanly falls back to cached local data or synthetic benchmark fixtures.
3. **Safety Locks Maintained:**
   - Real-money trading hard-locked (`ENABLE_REAL_TRADING = false`).
   - Zero credential or OTP collection.
   - Loopback host binding (`127.0.0.1:8000`).

---

## 5. Gate Sign-Off & Recommendation

All 6 workstreams have been audited, all issues documented and resolved, and the entire test suite passes cleanly. The repository is verified as safe, mathematically sound, and traceable for private founder investment research.
