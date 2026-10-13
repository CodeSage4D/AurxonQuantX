# AURXON Financial Semantics Audit — Phase 2.2
**Project:** AURXONQuant  
**Milestone:** Phase 2.2 — Primary-Source Data Integration & Evidence Verification  
**Status:** REMEDIATED & VERIFIED  
**Date:** 2026-10-13  

---

## 1. Problem Statement: Zero Sentinels & Financial Misrepresentation

In financial software, a numeric value of `0.0` has specific economic meaning:
- A P/E of `0.0` implies infinite earnings or zero share price.
- A dilution percentage of `0.0%` implies zero new shares issued (e.g., pure OFS).
- An expense ratio of `0.0%` implies zero management fees.

In Phase 2.1, an audit finding identified that loss-making issuers or missing financial indicators could inadvertently receive `0.0` as a default or sentinel value if not explicitly protected.

**Phase 2.2 Core Mandate:**  
1. Loss-making issuers must never receive a numeric P/E of `0.0`.
2. Missing data is never zero.
3. Unavailable data is never zero.
4. Not applicable is never zero.
5. Calculation errors must never silently transform into valid-looking metrics.

---

## 2. Typed Financial Semantics Architecture

To solve this systematically across all backend and frontend layers, `TypedFinancialMetric` and `MetricStatus` were instituted in `backend/app/schemas/semantics.py`:

```python
class MetricStatus(str, Enum):
    VALID = "VALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    CALCULATION_ERROR = "CALCULATION_ERROR"

class TypedFinancialMetric(BaseModel):
    value: Optional[float] = None
    status: MetricStatus = MetricStatus.VALID
    reason: Optional[str] = None
    unit: Optional[str] = None
```

---

## 3. Financial Metrics Audited and Remediated

### 3.1 IPO P/E Valuation Multiples
- **Condition:** Issuer has negative EPS (`eps < 0`)
  - **Previous State (Phase 2):** In some calculation paths, returned `0.0` or raw division resulting in negative P/E.
  - **Phase 2.2 State:** `pe_at_floor: None`, `pe_at_cap: None`, `pe_status: MetricStatus.NOT_APPLICABLE`, `pe_reason: "Loss-making issuer (Negative EPS: ₹-X.XX). P/E ratio is not economically meaningful."`
- **Condition:** Issuer has zero EPS (`eps == 0.0`)
  - **Phase 2.2 State:** `pe_floor: None`, `pe_cap: None`, `pe_status: MetricStatus.NOT_APPLICABLE`, `pe_reason: "Zero EPS: P/E ratio is mathematically undefined."`
- **Condition:** Missing EPS (`eps is None`)
  - **Phase 2.2 State:** `pe_floor: None`, `pe_cap: None`, `pe_status: MetricStatus.DATA_UNAVAILABLE`, `pe_reason: "EPS data unavailable in prospectus filing"`

### 3.2 Compound Annual Growth Rate (CAGR)
- **Condition:** Non-positive initial value (`initial_val <= 0`)
  - **Semantics:** Turnaround from loss or zero base cannot be represented by real-valued fractional powers.
  - **Phase 2.2 State:** `status: MetricStatus.NOT_APPLICABLE`, `value: None`, `reason: "Non-positive base value (-X): CAGR mathematically undefined for turnaround from loss"`
- **Condition:** Invalid period count (`periods <= 0`)
  - **Phase 2.2 State:** `status: MetricStatus.CALCULATION_ERROR`, `value: None`, `reason: "Periods must be greater than zero for CAGR calculation"`
- **Condition:** NaN or Infinite inputs
  - **Phase 2.2 State:** `status: MetricStatus.CALCULATION_ERROR`, `value: None`, `reason: "Input values contain NaN or Infinite values"`

### 3.3 Dilution Arithmetic
- **Condition:** 100% Offer For Sale (e.g. Tata Technologies)
  - **Semantics:** Exactly `0.0%` dilution is economically correct because company receives zero fresh capital and share count remains unchanged (`pre_issue_shares == post_issue_shares`).
  - **Status:** `VALID`, `value: 0.0%`, with explicit note: `Offer For Sale (Nil Proceeds to Company)`.

### 3.4 Mutual Fund Tracking Error & Alpha
- **Condition:** Insufficient history (< 36 monthly observations or < 252 trading days)
  - **Semantics:** Calculation aborted; `tracking_error_status: DATA_UNAVAILABLE` rather than defaulting to `0.0%`.

---

## 4. Test Coverage & Verification

- `backend/tests/test_phase_2_2_semantics_and_connectors.py` executes 5 specific financial semantics regression tests:
  1. `test_negative_eps_produces_not_applicable` — PASS
  2. `test_zero_eps_produces_not_applicable` — PASS
  3. `test_missing_eps_produces_data_unavailable` — PASS
  4. `test_positive_eps_produces_valid_metric` — PASS
  5. `test_financial_cagr_semantics` — PASS
- Frontend `IPOResearchView.tsx` safely renders `MetricStatus` badge and diagnostic reason when P/E or dilution is `null`.
