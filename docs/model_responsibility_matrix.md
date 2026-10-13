# AURXONQuant — Model Responsibility & Task Routing Matrix

**Phase:** 3.5 — Premium Experience & Intelligence Transformation  
**Registry Module:** `backend/app/model_adapters/inventory.py`  
**API Endpoint:** `GET /api/v1/models/responsibilities`  
**Frontend View:** `frontend/src/components/ModelInventoryView.tsx`  
**Audited Baseline:** 2026-10-13  
**Status:** VALIDATED & STRICTLY ENFORCED

---

## 1. Architectural Principle: Deterministic Risk Superiority

In financial intelligence systems, probabilistic language models are prone to hallucination, sycophancy, and numerical drift. 

**AURXON Core Invariant:**  
No AI model consensus, agentic workflow, or prompt instruction is permitted to override, bypass, or relax a deterministic mathematical calculation or risk management veto.

| Responsibility Boundary | Enforcement Level | Override Allowed? |
| :--- | :--- | :--- |
| **Portfolio Risk & Drawdown Limits** | Deterministic Python Engine | **STRICTLY FORBIDDEN (`can_override_risk_veto=False`)** |
| **Transaction Costs & Taxes** | Deterministic Formula | **STRICTLY FORBIDDEN (`can_override_risk_veto=False`)** |
| **Order Book Price & Stale Checks** | Deterministic Staleness Guard | **STRICTLY FORBIDDEN (`can_override_risk_veto=False`)** |
| **Qualitative Narrative Synthesis** | Generative LLM | Allowed with Evidence Citations |
| **Document OCR & Layout Parse** | Computer Vision / Heuristic | Allowed with Source Lineage |

---

## 2. Task Responsibility Matrix

| Task Domain | Primary Component | Execution Mode | Fallback Component | Fallback Latency | Risk Override Permitted? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Screen Reading & OCR** | `local:tesseract-v5` | Local Binary | Heuristic Layout Parser | < 2 ms | **NO** |
| **Financial Valuation & Multiples** | `deterministic:valuation_engine` | Deterministic Code | Cached Historical Financials | < 1 ms | **NO** |
| **Regulatory & Statutory Taxes** | `deterministic:statutory_cost_model` | Deterministic Code | Hardcoded SEBI/CBIC Schedule | < 1 ms | **NO** |
| **Risk Enforcement & Portfolio Ledger** | `deterministic:paper_portfolio_manager` | Deterministic Code | Hard Stop / Kill Switch Trigger | < 1 ms | **NO** |
| **Offline Claim & Evidence Scoring** | `aurxon_offline:heuristic_evidence_v1` | Heuristic Code | Strict Unverified Marker | < 1 ms | **NO** |
| **Prospectus & Red Herring Synthesis** | `openai:gpt-4o` | Cloud API | `aurxon_offline:heuristic_evidence_v1` | ~1.5 ms | **NO** |
| **High-Speed SEC/SEBI Extraction** | `groq:llama-3.3-70b-versatile` | Cloud API | `aurxon_offline:heuristic_evidence_v1` | ~1.5 ms | **NO** |

---

## 3. Fallback & Graceful Degradation Rules

1. **Cloud Model Unavailability**:
   - If OpenAI or Groq endpoints return timeouts (> 5.0s), 429 rate limits, or 401 unauthenticated errors, the pipeline immediately falls back to `aurxon_offline:heuristic_evidence_v1`.
   - The user interface transparently badges the output as:
     `HEURISTIC_OFFLINE_FALLBACK (Cloud Provider Unreachable)`.
   - Factual accuracy and evidence citation tags remain required.

2. **OCR Failure / Unreadable Input**:
   - If an uploaded screen or image fails OCR decoding, the pipeline returns `UNREADABLE_IMAGE_ERROR` and requests a higher-resolution crop or manual bounding box.
   - It will never invent tickers, prices, or orders.

3. **Stale Market Data Guard**:
   - If a quote has `freshness == FreshnessStatus.STALE_WARNING` or `STALE_CRITICAL`, simulated orders are rejected with `REJECTED: STALE_MARKET_DATA`.
   - No model sentiment or speculative confidence score can execute an order against stale prices.

---

## 4. Verification Evidence

- Verified in unit tests: `test_risk_limits_prevent_unrealized_daily_loss`, `test_risk_limits_prevent_max_drawdown`, `test_reject_stale_prices_in_paper_trading`.
- Verified in model registry: `backend/app/model_adapters/inventory.py` line items confirm `can_override_risk_veto: False` on all 7 components.
