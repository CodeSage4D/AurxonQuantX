# AURXONQuant — Phase 2.2 Baseline Verification Report

**Date:** October 13, 2026  
**Auditor / Team:** AURXON Principal Engineering Team (Financial Architect, QA Auditor, Security Engineer)  
**Baseline Commit:** `15da0edeba05fe66945d47bb602d86d9ed8c32d4`  
**Git Branch:** `main`  
**Git Working Tree Status:** Clean (0 untracked files, 0 uncommitted changes)  

---

## 1. Verified Starting Environment

- **Host OS:** Linux Mint 22.3 (kernel `6.8.0-49-generic` x86_64)
- **Host Resources:** 4 vCPUs, 7.5 GiB Physical RAM (~2.4 GiB free)
- **Python Environment:** Python 3.12.3 in `/home/karann/Documents/AURXONQuant/.venv`
- **Node.js Environment:** v20.20.2, npm 10.8.2
- **Database Engine:** SQLite 3.45.1 in WAL mode (`audit_ledger.db`)
- **System Toolchain:** Tesseract OCR v5 (`/usr/bin/tesseract`)

---

## 2. Test & Build Baseline Results

### 2.1 Backend Automated Test Suite
- **Command:** `PYTHONPATH=backend .venv/bin/pytest backend/tests -v`
- **Exit Code:** `0`
- **Execution Time:** `1.92s`
- **Total Test Count:** **66 passed, 0 failed, 1 warning**
- **Test Modules Passing:**
  - `test_api_endpoints.py`: 11 passed
  - `test_audit_ledger.py`: 2 passed
  - `test_document_ingestion.py`: 2 passed
  - `test_evidence_loop.py`: 4 passed
  - `test_fund_analyzer.py`: 6 passed
  - `test_ipo_analyzer.py`: 4 passed
  - `test_model_registry.py`: 6 passed
  - `test_nse_connector.py`: 4 passed
  - `test_phase_2_1_extraction_security.py`: 4 passed
  - `test_phase_2_1_fund_math.py`: 5 passed
  - `test_phase_2_1_ipo_math.py`: 5 passed
  - `test_screen_ocr.py`: 3 passed
  - `test_source_registry.py`: 2 passed
  - `test_valuation.py`: 8 passed

### 2.2 Frontend Production Build
- **Command:** `npm run build` in `frontend/`
- **Exit Code:** `0`
- **Execution Time:** `2.80s`
- **Artifacts:**
  - `dist/index.html`: `1.12 kB` (gzip: `0.64 kB`)
  - `dist/assets/index-dFPiwz-p.css`: `9.42 kB` (gzip: `2.53 kB`)
  - `dist/assets/index-BYqvJRFS.js`: `218.79 kB` (gzip: `62.30 kB`)
- **TypeScript strict checks (`tsc`):** Clean (0 errors).

---

## 3. Scope & Objectives for Phase 2.2

With the Phase 2.1 gate established and verified:
1. **Workstream A:** Repair financial semantics: Replace numeric `0.0` sentinels for loss-making P/E with typed `MetricValue` (`value: null`, `status: NOT_APPLICABLE`, `reason: "Negative earnings"`), and audit all metrics for invalid zero defaults.
2. **Workstream B:** Primary-source registry and data connectors: Implement provider-independent integration layer supporting official primary sources (SEBI, NSE/BSE, AMFI statutory daily NAV data, AMC Factsheets), with formal provenance states (`LIVE_VERIFIED`, `DELAYED_VERIFIED`, `HISTORICAL_VERIFIED`, `CACHED`, `SYNTHETIC`, `UNVERIFIED`, `UNAVAILABLE`).
3. **Workstream C:** Live data and freshness policies by data type (intraday prices, end-of-day, NAV dates, portfolio dates, filing versions).
4. **Workstream D:** Real IPO prospectus extraction verification with field-level lineage records (`BAJAJHFL`, `TATATECH`).
5. **Workstream E:** Mutual Fund & ETF data verification, official AMFI statutory NAV data integration (`https://www.amfiindia.com/spages/NAVAll.txt`), category-aware benchmark alignment.
6. **Workstream F:** Evidence graph and claim verification: Distinguish source facts, corroborated facts, deterministic calculations, interpretations, scenarios, and unverified claims.
7. **Workstream G:** Recommendation readiness: Multi-dimensional qualification gates without black-box scores, refusing return/listing gain guarantees.
8. **Workstream H:** Frontend transparency: Status indicators, provenance badges, and lineage inspection.
9. **Workstream I:** Security, 50MB payload limits, loopback binding, and audit tamper-evidence.
10. **Workstream J:** Comprehensive regression testing and release gate verification.
