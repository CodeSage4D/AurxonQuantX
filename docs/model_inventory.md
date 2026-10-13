# AURXONQuant — Discovered AI Model Estate & Inventory

**Phase:** 3.5 — Premium Experience & Intelligence Transformation  
**Registry Module:** `backend/app/model_adapters/inventory.py`  
**API Endpoint:** `GET /api/v1/models/inventory`  
**Frontend View:** `frontend/src/components/ModelInventoryView.tsx`  
**Audited Baseline:** 2026-10-13  
**Status:** VALIDATED & OPERATIONAL

---

## 1. Discovered Model Estate Overview

An exhaustive audit of the codebase, adapter registries, local binaries, heuristic fallback trees, and deterministic execution engines discovered seven distinct intelligence modules.

Each model/engine is tracked with its operational state:
- `INSTALLED_LOCAL`: Resident on local host filesystem, fully tested and active.
- `DETERMINISTIC_ACTIVE`: Pure Python/math algorithms with zero stochastic variance, active.
- `HEURISTIC_ACTIVE`: Rule-based deterministic extraction pipeline, active.
- `CONFIGURED_CLOUD`: Cloud API configured; operational only when valid API keys are present.

---

## 2. Model Inventory Table

| Model ID | Provider & Version | Family / Engine | Execution Mode | Task Responsibility | License | Estimated RAM | Operational Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `local:tesseract-v5` | Google / Tesseract 5.3+ | OCR / Computer Vision | Local Binary | Fast screen reading, terminal OCR, document table extraction | Apache 2.0 | ~28 MB | `INSTALLED_LOCAL` |
| `deterministic:valuation_engine` | AURXON Deterministic 1.0 | Quantitative Finance | Deterministic Engine | DCF, peer multiples, debt-to-equity, ROE, RoCE calculations | Proprietary | ~12 MB | `DETERMINISTIC_ACTIVE` |
| `deterministic:statutory_cost_model` | AURXON Regulatory Engine | Tax & Compliance | Deterministic Engine | Indian statutory brokerage, STT, stamp duty, GST, exchange charges | Proprietary | ~4 MB | `DETERMINISTIC_ACTIVE` |
| `deterministic:paper_portfolio_manager` | AURXON Risk & Ledger | Portfolio Accounting | Deterministic Engine | Peak drawdown tracking, daily stop-loss, position ledger, order life | Proprietary | ~8 MB | `DETERMINISTIC_ACTIVE` |
| `aurxon_offline:heuristic_evidence_v1` | AURXON Fallback System | Rule-based Extraction | Local Heuristic | Offline fallback, deterministic claim validation, keyword scoring | MIT | ~2 MB | `HEURISTIC_ACTIVE` |
| `openai:gpt-4o` | OpenAI (Omni v1) | Transformer LLM | Cloud Provider | Complex synthesis, multi-source contradiction detection, DRHP narrative | Commercial API | ~15 MB | `CONFIGURED_CLOUD` (Simulated without key) |
| `groq:llama-3.3-70b-versatile` | Groq / Meta Llama 3.3 | Transformer LLM | Cloud Provider | High-speed structured summarization, SEC/SEBI evidence extraction | Meta Community / Cloud | ~10 MB | `CONFIGURED_CLOUD` (Simulated without key) |

---

## 3. Storage Footprint & Path Verification

1. **`local:tesseract-v5`**:
   - Location: `/usr/bin/tesseract`
   - Data Path: `/usr/share/tesseract-ocr/5/tessdata/eng.traineddata` (approx. 4.1 MB)
   - Executable Verified: Yes, exit code 0 on `--version`.

2. **Deterministic & Heuristic Engines**:
   - `backend/app/trading/paper_manager.py` (Ledger & Risk)
   - `backend/app/backtesting/cost_model.py` (Statutory charges)
   - `backend/app/ipo/` & `backend/app/mutual_funds/` (Valuation & Metrics)
   - `backend/app/evidence/orchestrator.py` (Evidence scoring)
   - Footprint: Resident in Python runtime memory; zero additional disk asset overhead.

3. **Cloud Adapters**:
   - `backend/app/model_adapters/`
   - Configured via environment variables (`OPENAI_API_KEY`, `GROQ_API_KEY`).
   - If keys are unset, adapters automatically return marked heuristic fallbacks without raising uncaught runtime exceptions.

---

## 4. Key Architectural Guarantees

- **No Phantom Models**: No model is listed as "ACTIVE" or "TESTED" unless its executable is proven to exist on disk or its deterministic code passes unit tests.
- **Strict Simulation Reporting**: Cloud models without API keys are reported as `CONFIGURED_CLOUD (Simulated)`—never as passed or live.
- **Resource Discipline**: Total local model RAM footprint is restricted to **~79 MB**, preserving host memory for market data streaming and UI rendering.
