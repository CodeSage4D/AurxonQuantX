# AURXON Investment Intelligence Hub

Founder-operated, evidence-first quantitative financial research system for Indian markets (Equities, ETFs, Dividends, IPOs, Mutual Funds, Trading Research, and Screen/Companion Context).

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │    Desktop Shell / UI (Tauri 2 / React) │
                      │  Dark-Mode Glassmorphism • SSE Stream  │
                      └──────────────────┬─────────────────────┘
                                         │  HTTP / SSE
                                         ▼
                      ┌────────────────────────────────────────┐
                      │    FastAPI Backend Server (:8000)      │
                      ├──────────────────┬─────────────────────┤
                      │  Evidence-Loop   │ Deterministic Math  │
                      │  Orchestration   │ (DCF, Graham, Piot) │
                      └────────┬─────────┴──────────┬──────────┘
                               │                    │
              ┌────────────────┴────────┐  ┌────────┴─────────────────┐
              │ Multi-Provider Registry │  │ NSE Market Connector     │
              │ Groq • OpenAI • Mock    │  │ Disclosures • yfinance   │
              └─────────────────────────┘  └──────────────────────────┘
                               │                    │
                               ▼                    ▼
                      ┌────────────────────────────────────────┐
                      │ Immutable Audit Ledger (SQLite + SHA)  │
                      │ 100% Reproducible Research Dossiers    │
                      └────────────────────────────────────────┘
```

---

## Phase 0 Environment Audit Summary

- **OS:** Linux Mint 22.3 (Ubuntu 24.04 noble base), Linux 7.0.0 kernel x86_64
- **Host Memory:** 7.5 GiB RAM (~2.5 GiB available) $\to$ *Strict budget: Large local LLMs (7B+) are avoided in-memory to prevent system thrashing; lightweight compact models and remote cloud providers used instead.*
- **Accelerators:** CPU compute only (no discrete NVIDIA GPU).
- **Toolchains Verified:**
  - Python 3.12.3 in dedicated `.venv`
  - Node.js v20.20.2 & npm 10.8.2
  - Git 2.43.0
  - Tesseract OCR v5 (/usr/bin/tesseract)
  - SQLite 3.45.1
- **Trading Safety:** Real-money execution hard-locked (`ENABLE_REAL_TRADING=false`). Paper trading & research mode only.

---

---

## Verification & Automated Test Suite

All 52 unit, integration, and quantitative tests execute synchronously and pass cleanly:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run full backend test suite
PYTHONPATH=backend pytest backend/tests -v
```

### Coverage (52 Tests):
1. `backend/tests/test_ipo_analyzer.py`: Deterministic IPO structure arithmetic (fresh issue vs OFS split, post-issue dilution, promoter holding shift, financial CAGR, valuation peer comparisons, 7-point decision matrix for `BAJAJHFL` and `TATATECH`).
2. `backend/tests/test_fund_analyzer.py`: Mutual fund CAGR, rolling returns, portfolio overlap math, 10Y Direct vs Regular compounding savings, ETF tracking error, category comparisons, and goal-based asset allocation proposals.
3. `backend/tests/test_document_ingestion.py`: Untrusted PDF, HTML, and text ingestion with prompt-injection neutralization and empty/corrupt document resilience.
4. `backend/tests/test_source_registry.py`: SEBI, NSE/BSE, AMFI, AMC, Issuer, and Aggregator source registration with reliability weights and fallback policies.
5. `backend/tests/test_valuation.py`: Graham Number, 2-Stage DCF 3x3 sensitivity matrix, Piotroski 9-point score, Altman Z-Score, banking sector exclusions, Sharpe/Sortino/Drawdown risk metrics.
6. `backend/tests/test_evidence_loop.py`: Evidence-Loop streaming workflow, prompt-injection defense, claim deduplication, and contradiction detection.
7. `backend/tests/test_audit_ledger.py`: Sequential SHA-256 hash-chain integrity and cryptographic tampering detection.
8. `backend/tests/test_nse_connector.py`: Symbol normalization, offline benchmark fixtures, and unavailable-state handling.
9. `backend/tests/test_screen_ocr.py`: Symbol extraction and regex privacy redactor for OTPs/credentials.
10. `backend/tests/test_model_registry.py`: Multi-model registry with transparent fallback and error handling (missing keys, 401 auth, timeouts, 429 rate limits, malformed JSON).
11. `backend/tests/test_api_endpoints.py`: All 11 FastAPI endpoints (`/health`, `/market/quote`, `/research/sync`, `/audit/records`, `/audit/integrity`, `/companion/context`, `/sources`, `/ipo/list`, `/ipo/analyze/{symbol}`, `/funds/list`, `/funds/compare`, `/funds/allocate`, `/export/report`, `/ingestion/upload`).

---

## Phase 2 Modules & Capabilities

### 1. Module A: IPO Prospectus Intelligence
- **Issue Structure:** Fresh issue vs OFS breakdown, post-issue shares, dilution percentage, promoter stake shift (pre $\to$ post), lot size, and proceed utilization.
- **Financial & Valuation Analysis:** Historical revenue & PAT CAGR, RoE, margins, and valuation multiples (P/E at floor and cap) compared against genuine listed peers.
- **7-Point Decision Framework:** Separate objective assessments for Business Quality, Financial Quality, Governance & Disclosed Risks, Valuation Sanity, Issue Structure, Listing Speculation vs Long-Term Ownership, and Key Unverified Facts.
- **Zero Return Promises:** Hard architectural refusal to promise listing day pops, allotment guarantees, or capital protection.

### 2. Module B: Mutual Fund & ETF Intelligence
- **Deterministic Metrics:** CAGR, rolling returns, Sharpe, Sortino, max drawdown, and ETF tracking error vs benchmark index.
- **Portfolio Overlap:** Exact holdings overlap percentage calculated across mutual funds and ETFs using $\sum \min(w_{A,i}, w_{B,i})$.
- **Direct Plan Compounding Drag:** 10-year compounding calculation showing explicit rupee savings of Direct Plans vs Regular Plans due to distributor commissions.
- **Goal-Based Allocation:** Transparent portfolio allocation based on investment horizon, risk profile, and liquidity requirements with explicit downside stress scenarios.

### 3. Untrusted Document Ingestion & Source Governance
- **Injection Defense:** Uploaded DRHP/RHP PDFs and HTML disclosures are treated as untrusted input. Active prompt injection vectors (`SYSTEM OVERRIDE`, `Ignore previous instructions...`) are quarantined.
- **Source Registry:** Explicit tracking of primary regulatory sources (SEBI, NSE/BSE, AMFI) vs issuer filings vs aggregators with reliability weights.

---

## How to Run the Platform

### 1. Start Backend Server
```bash
source .venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation is available interactively at: `http://127.0.0.1:8000/docs`

### 2. Start Desktop Frontend UI
```bash
cd frontend
npm run dev
```
Open `http://127.0.0.1:5173` in your browser or desktop webview.

### 3. Production Frontend Bundle
```bash
cd frontend
npm run build
```

---

## Safety & Ethics Principles
1. **Never Hallucinate Ratios:** Financial multiples (P/E, P/B, DCF, Graham, Piotroski, CAGR, tracking error) are calculated deterministically in Python using pure math—never generated by an LLM.
2. **Auditable Evidence:** All material claims link to verified exchange filings or disclosure sources with timestamped audit IDs.
3. **Zero Credential Harvesting:** The screen companion and browser extension automatically redact OTPs, passwords, and banking identifiers. Real-money orders cannot be triggered (`ENABLE_REAL_TRADING=false`).
4. **Loopback Binding:** Backend binds strictly to `127.0.0.1` for private local operation.
