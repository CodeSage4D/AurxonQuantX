# AURXON Phase 2.2 Issue Register
**Project:** AURXONQuant  
**Milestone:** Phase 2.2 — Primary-Source Data Integration & Evidence Verification  
**Date:** 2026-10-13  

---

## 1. Resolved Issues in Phase 2.2

| Issue ID | Category | Severity | Description | Resolution | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ISSUE-2.2-01** | Financial Semantics | HIGH | Loss-making or missing earnings could receive misleading `0.0` P/E sentinel. | Implemented `TypedFinancialMetric` & `MetricStatus.NOT_APPLICABLE` with explicit reason. | **RESOLVED** |
| **ISSUE-2.2-02** | Primary Source | MEDIUM | Mutual fund daily NAV lacked official statutory AMFI integration. | Built `AMFIConnector` parsing statutory AMFI daily NAV file (`NAVAll.txt`) with local verified fallback. | **RESOLVED** |
| **ISSUE-2.2-03** | Data Provenance | MEDIUM | Prospectus metrics lacked document-level page/section lineage records. | Added `FieldLineageRecord` with PDF page, exact quoted text, and SEBI filing URLs for `BAJAJHFL` and `TATATECH`. | **RESOLVED** |
| **ISSUE-2.2-04** | Decision Integrity | HIGH | Lack of multi-dimensional gating allowed unverified or stale data to produce recommendations. | Instituted `RecommendationReadinessGate` separating 5+ dimensions and refusing black-box universal scores. | **RESOLVED** |
| **ISSUE-2.2-05** | Frontend Transparency | MEDIUM | Frontend lacked visual indicators for typed `null` metrics, lineage inspection, and readiness gates. | Added lineage inspection table, readiness gate card, and safe null/status badges to React interface. | **RESOLVED** |

---

## 2. Active Technical Constraints & Limitations

| Constraint ID | Component | Operational Limit | Mitigation / Future Path |
| :--- | :--- | :--- | :--- |
| **CONSTR-01** | NSE Connector | Intraday tick streaming requires authenticated exchange API or broker session. | Offline / synthetic benchmark fixtures clearly labeled as `SYNTHETIC_BENCHMARK` or `CACHED`. |
| **CONSTR-02** | Scanned PDFs | Image-only prospectuses cannot be extracted without OCR engine (Tesseract/paddleocr). | Scanned PDF detector flags document and alerts user to upload text-searchable filing. |
| **CONSTR-03** | Local Sandbox | Default sandbox execution operates without network connectivity. | Packaged local AMFI snapshot and SEBI fixtures ensure complete offline testability. |
