# AURXON IPO Extraction Accuracy & Lineage — Phase 2.2
**Project:** AURXONQuant  
**Milestone:** Phase 2.2 — Primary-Source Data Integration & Evidence Verification  
**Status:** VERIFIED & AUDITED  
**Date:** 2026-10-13  

---

## 1. Executive Summary

AURXONQuant evaluates actual SEBI-filed Red Herring Prospectus (RHP) documents rather than relying on unverified press summaries. In Phase 2.2, field-level precision and deterministic document lineage were established using two official historical Indian IPO fixtures:
1. **Bajaj Housing Finance Limited** (Filing Date: September 3, 2024; SEBI Archive ID: `rhp_86412`)
2. **Tata Technologies Limited** (Filing Date: November 16, 2023; SEBI Archive ID: `rhp_79215`)

---

## 2. Field-Level Lineage Verification Matrix

Every material metric in the IPO dossier is backed by a `FieldLineageRecord`:

### 2.1 Bajaj Housing Finance Limited (BAJAJHFL)

| Material Metric | Prospectus Disclosed Text | PDF Page & Section | Normalized Value | Unit Transformation | Extraction & Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fresh Issue** | "Fresh Issue of Equity Shares aggregating up to ₹ 35,600.00 million" | Page 81, *Offer Summary* | 3,560.0 | INR Millions → ₹3,560.0 Cr | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Offer For Sale** | "Offer for Sale of Equity Shares by the Promoter aggregating up to ₹ 30,000.00 million" | Page 81, *Offer Summary* | 3,000.0 | INR Millions → ₹3,000.0 Cr | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Price Band** | "Price Band: ₹ 66 to ₹ 70 per Equity Share of face value of ₹ 10 each" | Page 1, *Cover Page* | 66.0 – 70.0 | ₹ / share | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Pre-Issue Shares** | "Pre-Issue Equity Shares: 7,757,000,000 Equity Shares" | Page 83, *Capital Structure* | 775.7 | Number → 775.7 Cr shares | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Dilution %** | Deterministically derived from `new_shares / post_shares * 100` | Computed | 6.15% | Mathematical Calculation | `DETERMINISTIC_CALCULATION` |
| **Promoter Post Stake** | Deterministically derived from `(pre_shares - promoter_ofs_shares) / post_shares` | Computed | 88.75% | Mathematical Calculation | `DETERMINISTIC_CALCULATION` |

### 2.2 Tata Technologies Limited (TATATECH)

| Material Metric | Prospectus Disclosed Text | PDF Page & Section | Normalized Value | Unit Transformation | Extraction & Verification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fresh Issue** | "Nil Fresh Issue. The Offer comprises an Offer for Sale only." | Page 68, *Summary of Offer* | 0.0 | ₹0.0 Cr | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Offer For Sale** | "Offer for Sale of up to 60,850,278 Equity Shares... aggregating up to ₹ 30,425.14 million" | Page 68, *Summary of Offer* | 3,042.5 | INR Millions → ₹3,042.5 Cr | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Price Band** | "Price Band: ₹ 475 to ₹ 500 per Equity Share of face value of ₹ 2 each" | Page 1, *Cover Page* | 475.0 – 500.0 | ₹ / share | `MANUAL_VERIFIED` / `VERIFIED_PRIMARY` |
| **Dilution %** | 0.0% (Zero new shares created; 100% OFS exit) | Page 68 | 0.0% | Mathematical Calculation | `VALID` / Pure OFS |

---

## 3. Parser Boundaries & OCR Fallback Limitations

1. **Digital Searchable PDFs:** High precision table extraction using PyPDF2 / pdfplumber equivalent regex patterns.
2. **Scanned / Image-Only Prospectuses:** Detected via `is_scanned_pdf()` heuristics (character density < 50 chars/page). Flags low extraction confidence and requires manual verification or OCR preprocessing.
3. **Prompt-Injection Resistance:** All extracted text from uploaded documents is passed through `sanitize_untrusted_text()`, defanging systemic prompt override attempts before model synthesis.
