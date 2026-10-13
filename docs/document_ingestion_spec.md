# AURXON Document Ingestion & Verification Specification

**Milestone:** Phase 2  
**Status:** Hardened Specification  
**Version:** 1.0.0  

---

## 1. Principles of Document Ingestion

1. **Passive Data Payload Invariance:** All uploaded documents (DRHP, RHP, SIDs, financial statements) are treated strictly as passive, untrusted input. Under no circumstances may text inside a document trigger system instructions, alter system prompts, or bypass safety gates.
2. **Untrusted Directive Sanitization:** Any instruction resembling `ignore all previous instructions`, `<script>`, or system prompt overrides is neutralized and flagged in `detected_injection_attempts`.
3. **Traceability to Page Numbers:** Extracted sections and tables maintain 1-indexed page number references so the founder can cross-reference findings directly in the original PDF.
4. **Table Arithmetic Integrity:** Stated units (e.g. `₹ in Crores`, `₹ in Lakhs`, `₹ in Millions`) and periods (`FY24`, `FY25`, `FY26`, `Q1 FY27`) must be explicitly declared. Financial components (e.g. Fresh Issue + OFS) are validated against stated totals.
5. **No Hallucinated Fill-ins:** If an extraction fails or a page is scanned without readable text, the engine records an extraction error. It never prompts an LLM to guess missing numbers.

---

## 2. Ingestion Pipeline Lifecycle

```
Uploaded PDF / Filing
       │
       ▼
[SHA-256 Hash & Size Measurement]
       │
       ▼
[Page-by-Page Text Extraction (pypdf)]
       │
       ▼
[Untrusted Injection Filter (sanitize_untrusted_content)]
       │
       ├── Detection Alert logged if injection patterns match
       │
       ▼
[Section Chunking & Page Numbering]
       │
       ▼
[Tabular Block Detection & Unit Validation (Lakhs vs Crores)]
       │
       ▼
DocumentIngestionResult (Ready for IPO / MF Research Engine)
```
