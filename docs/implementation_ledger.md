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

---

## 3. Test Matrix Summary

```
======================== 33 passed, 1 warning in 1.92s =========================
- test_api_endpoints.py: 6 passed (Health, Quote, Sync, Audit Records, Integrity, Companion)
- test_audit_ledger.py: 2 passed (Sequential Hash-Chaining, Tampering Detection)
- test_evidence_loop.py: 4 passed (Streaming Execution, Prompt Injection Defense, Dedup, Contradictions)
- test_model_registry.py: 6 passed (Missing Keys, 401 Auth, Timeout, 429 Rate Limit, Bad Output, Fallback)
- test_nse_connector.py: 4 passed (Normalization, Provenance, Bank Sector Detection, Unavailable State)
- test_screen_ocr.py: 3 passed (Symbol Detection, Privacy Redaction, Pause Control)
- test_valuation.py: 8 passed (Graham, DCF, Sensitivity Matrix, Bank Exclusion, Piotroski, Altman Z, Risk Metrics, Dossier)
```

---

## 4. Unresolved Risks & Next Phase Roadmap

1. **Unresolved Risks:**
   - **External API Keys:** No production OpenAI, Anthropic, or Groq API keys are currently set in `.env`. System operates cleanly using deterministic fallback demonstration mode.
   - **Rust/WebKit2GTK Toolchain:** Building the native Linux Tauri binary requires `sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev` and the Rust toolchain. The web UI and desktop shell run immediately via Vite.
2. **Next Milestone (Phase 2):**
   - IPO prospectus analysis engine (DRHP/RHP extraction, anchor investor lock-in, listing-gain vs long-term scenarios).
   - Mutual funds and portfolio factor allocation module.
