# Phase 2 Baseline Audit Report

**Date:** October 13, 2026  
**Auditor:** Principal Financial-Software Architect & QA Lead  
**Commit Inspected:** `afdd6f8` (`feat(gate): Phase 1.5 Trust, Reliability and Integration Gate`)  
**Git Working Tree State:** Clean (0 uncommitted files)  

---

## 1. Verified Baseline Status

1. **Backend Test Suite:**
   - Command: `PYTHONPATH=backend .venv/bin/pytest backend/tests -v`
   - Exit Code: `0`
   - Test Count: **33 passed, 0 failed** (1.52s)
   - Scope verified: API endpoints, hash-chained audit ledger, parallel Evidence-Loop, prompt injection sanitization, claim deduplication, contradiction detection, model registry failure modes (missing keys, 401 auth, timeouts, 429 rate limit, malformed JSON, fallback transparency), NSE market data provenance, screen companion privacy guards, Graham Number, DCF sensitivity matrix, banking sector model exclusions, Piotroski F-score, Altman Z-score, and risk metrics.

2. **Frontend Production Build:**
   - Command: `npm run build` (in `/home/karann/Documents/AURXONQuant/frontend`)
   - Exit Code: `0`
   - Time: 2.07s
   - Bundle output: `dist/index.html` (1.12 kB), `dist/assets/index-dFPiwz-p.css` (9.42 kB), `dist/assets/index-k4eRYpLr.js` (184.37 kB).

3. **Runtime Capabilities & External Dependencies:**
   - **Active & Offline-Verified:**
     - Deterministic mathematical valuation engines (Graham, DCF 3x3 sensitivity grid, Piotroski, Altman Z, risk metrics).
     - Cryptographic SHA-256 sequential hash-chain audit ledger in SQLite WAL mode.
     - Curated offline Nifty 50 benchmark fixtures (`RELIANCE`, `TCS`, `INFY`, `HDFCBANK`).
     - Local OCR engine using system Tesseract 5 (`/usr/bin/tesseract`).
     - Heuristic demonstration model adapter (`aurxon_offline:heuristic_evidence_v1`).
   - **Credentials / Network Required (Graceful Fallback Mode):**
     - Cloud LLM adapters (`OpenAIAdapter`, `GroqAdapter`): require `OPENAI_API_KEY` or `GROQ_API_KEY`. When absent, gracefully fall back to transparently labelled offline demonstration heuristics.
     - Live market feed (`yfinance`): network access blocked in sandboxed environment, cleanly falls back to cached or synthetic benchmark data.
   - **Unimplemented Scope Entering Phase 2:**
     - Dedicated IPO prospectus research module (DRHP/RHP parsing, fresh issue/OFS split, promoter holding dilution, proceed utilization, risk classification, listing speculation vs long-term valuation).
     - Mutual fund & ETF quantitative intelligence module (CAGR, rolling returns, expense ratio, tracking error, portfolio overlap, category-aware benchmarks, IDCW vs total return separation).
     - Source registry interface and untrusted document ingestion pipeline.
     - Frontend views and exportable reports for IPOs and Mutual Funds/ETFs.
