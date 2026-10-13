# Phase 2.1 Issue Register & Remediation Log
## AURXON Investment Intelligence Hub — Phase 2.1 Independent Validation Gate

**Date:** October 13, 2026  
**Auditor:** Principal Financial Architect, Security Engineer & QA Lead  
**Scope:** All findings from Workstreams A, B, C, D, E, and F.

---

## 1. Issue Register

| Issue ID | Category | Severity | Title / Description | Impact | Remediation / Status |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **ISSUE-01** | **Security / DoS** | **HIGH** | **Unbounded File Upload Payload**<br>`/api/v1/ingestion/upload` read entire file bytes into memory via `await file.read()` without size cap. | Uploading 1GB+ files could exhaust host RAM (7.5GB total) and crash FastAPI backend. | **RESOLVED**<br>Implemented `MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024` (50MB) and HTTP 413 rejection. Verified by `test_upload_size_limit_rejection`. |
| **ISSUE-02** | **Document Extraction** | **MEDIUM** | **Unclear Scanned PDF Boundary**<br>System previously did not differentiate searchable digital text PDFs from pure scanned image PDFs. | Feeding scanned PDFs resulted in empty sections without explaining why no text was parsed. | **RESOLVED**<br>Identifies scanned PDFs with zero text streams and returns `FAILED` with diagnostic message: `"Scanned PDF detected: no digital text layer found. System OCR pipeline required."` Documented limitation in spec. |
| **ISSUE-03** | **Financial Arithmetic** | **MEDIUM** | **Accounting Parentheses Parsing**<br>Financial tables in Indian prospectuses format cash outflows and net losses as `(5,200.0)`. | Naive regex or `float()` could parse as NaN or positive numbers, inverting sign of cash flows. | **RESOLVED**<br>Implemented `parse_indian_number` to strip parentheses and assign negative signs. Verified by `test_parse_indian_number_accounting_and_commas`. |
| **ISSUE-04** | **Financial Mathematics** | **MEDIUM** | **CAGR Boundary with Negative/Zero Base**<br>Standard CAGR formula breaks or produces complex numbers for negative base values (turnaround cases). | Misinterpreting turnaround from loss to profit or calculating fractional powers of negative numbers. | **RESOLVED**<br>Documented mathematical limitation in `docs/ipo_quantitative_reference_tests.md`. Guarded return in `calculate_3y_cagr`. Added `test_cagr_mathematical_limits_and_turnaround_cases`. |
| **ISSUE-05** | **IPO Mathematics** | **LOW** | **Promoter OFS Post-Stake Bounds**<br>Previous promoter post-stake estimation used a fixed 70% heuristic factor. | Could produce slight variance if promoter sold 100% or 0% of OFS. | **RESOLVED**<br>Derived exact analytical upper and lower bounds for promoter post-issue holding based on OFS allocation. Verified in `test_promoter_holding_bounds_and_ofs_allocation`. |
| **ISSUE-06** | **Fund Mathematics** | **LOW** | **Universal ETF Benchmark Risk**<br>Applying Nifty 50 as a generic benchmark across all ETFs. | Inappropriate benchmark comparisons for sector funds (Bank BeES) or commodity ETFs (Gold). | **RESOLVED**<br>Decoupled ETF benchmarks in `CURATED_FUND_BENCHMARKS` to match category (Nifty 50 TRI for large-cap, Nifty 500 TRI for flexi-cap, Spot Gold for gold ETFs). Verified by `test_etf_benchmark_alignment_non_universal`. |
| **ISSUE-07** | **Data Governance** | **MEDIUM** | **Source Registry Reliability Weights**<br>Source registry reliability weights (1.0 for SEBI, 0.98 for NSE, 0.40 for aggregators) were configured defaults, not empirical probabilities. | Presenting heuristic weights as calibrated frequentist probabilities. | **RESOLVED**<br>Documented explicitly that reliability weights are Bayesian prior policy heuristics, not statistically calibrated frequencies. |
| **ISSUE-08** | **Security / Adversarial** | **MEDIUM** | **Prompt Injection Regex Coverage**<br>Original regex missed `SYSTEM OVERRIDE:` or `disregard instructions` variations. | Adversarial prompt injections in filings could evade sanitization. | **RESOLVED**<br>Hardened `UNTRUSTED_INJECTION_PATTERNS` to catch `system (prompt)? override`, `disregard`, `developer mode`, and expanded instruction phrases. Verified by `test_prompt_injection_sanitization_in_document`. |
| **ISSUE-09** | **Audit / Integrity** | **LOW** | **Hash-Chain Local Threat Model**<br>Local SQLite hash-chain is tamper-evident against runtime app modifications, but cannot prevent root filesystem manipulation. | Describing hash-chain as "immutable" on a mutable local disk. | **RESOLVED**<br>Clarified threat model in documentation: provides local runtime tamper-evidence; external cryptographic timestamping or remote ledger required for full adversary non-repudiation. |

---

## 2. Issue Resolution Summary

- **Total Issues Identified:** 9
- **Issues Resolved & Verified:** 9 (100%)
- **Critical Blockers Remaining:** 0
- **Regression Suite Status:** 66/66 automated tests passing synchronously.
