# Aurxon QuantX — Phase 4.5 Frontend & API Acceptance

## 1. Executive Summary & Verification Context
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.5 — Integrated Portfolio Validation & Release Readiness
- **Module:** `frontend/src/components/PortfolioIntelligenceView.tsx`, `backend/app/main.py`

This audit verifies that the user interface connects to live REST endpoints rather than displaying mock hard-coded fixtures, supporting full theme toggling, responsive layouts, and data provenance disclosures.

---

## 2. REST API Contract Verification

| Endpoint | Method | Response Contract | Status Code | Verified Payload |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/portfolio/list` | `GET` | `List[Dict[str, Any]]` | 200 OK | Returns all configured portfolios, active cash, equity, and peak equity |
| `/api/v1/portfolio/create` | `POST` | `PaperPortfolioState` | 200 OK | Creates isolated portfolio and initializes cash balance |
| `/api/v1/portfolio/intelligence` | `GET` | `PortfolioIntelligenceSnapshot` | 200 OK | Holdings, concentration, performance, factors, and stress scenarios |
| `/api/v1/portfolio/rebalance/simulate` | `POST` | `RebalancingSimulationResult` | 200 OK | Evaluates proposed trades, statutory drag, and integer lots |
| `/api/v1/portfolio/rebalance/execute-paper` | `POST` | `List[Dict[str, Any]]` | 200 OK | Sequentially executes paper orders in paper trading ledger |
| `/api/v1/portfolio/snapshots` | `GET` | `List[Dict[str, Any]]` | 200 OK | Returns timestamped historical snapshots |

---

## 3. UI States & UX Verification

### 3.1 Amber Simulation Banner
The UI renders a persistent amber simulation warning banner:
> ⚠️ **PAPER TRADING ONLY — SIMULATION ENVIRONMENT**  
> *Real-money execution disabled (ENABLE_REAL_TRADING=false)*

### 3.2 Dynamic Data Loading & Error Handling
- **Loading State:** Spinner displays during REST queries to `/api/v1/portfolio/intelligence`.
- **Empty State:** When a portfolio holds 100% virtual cash, factor attribution renders diagnostic tiles stating:
  > *"Portfolio has zero active equity holdings (100% cash or unallocated)."*
- **Error Banner:** If API communication fails, an alert banner renders with HTTP diagnostic details.

### 3.3 Provenance Badges
- Each holding and factor tile renders provenance badges:
  - `PRICED_CURRENT`, `BENCHMARK_FIXTURE`, `CACHED`, `UNPRICED`.
  - Data Origin: `COMPUTED_HISTORICAL` or `AUDITED_REFERENCE_PROFILE (FY25-26)`.

---

## 4. Theme & Layout Compliance

1. **Dual Themes Supported:**
   - **Glacier Light:** Clean corporate presentation with high-contrast text and border separation.
   - **Neon Obsidian Dark:** High-contrast quantitative workspace with tabular numbers (`tabular-nums`).
2. **Responsive Layout:**
   - Evaluated across desktop wide screens ($1440\text{px}$) and compact viewports ($768\text{px}$).
   - Tables scroll horizontally; metric cards wrap dynamically via CSS grid.
3. **Accessibility:**
   - Tabular typography enforces aligned decimals for INR currency amounts.
   - Contrast ratios on metric labels meet WCAG AA standards.
