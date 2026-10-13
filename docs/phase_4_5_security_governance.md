# Aurxon QuantX — Phase 4.5 Security & Provider Governance

## 1. Executive Summary & Verification Context
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.5 — Integrated Portfolio Validation & Release Readiness
- **Module:** `backend/app/config.py`, `backend/app/trading/risk_gate.py`, `backend/app/companion/screen_ocr.py`

This document details the verification of real-trading isolation, operator kill switches, credential redaction, provider rights boundaries, and deployment gaps.

---

## 2. Hard Execution Isolation
```python
ENABLE_REAL_TRADING: bool = False
```
- **Architectural Guard:** The codebase contains zero integrations with live Indian broker APIs (Zerodha Kite, Upstox, Angel One, Groww, ICICI Direct).
- **Hard-Locked Configuration:** Real trading cannot be enabled via runtime parameters or user headers. Any attempt to route real orders triggers an immediate system panic.

---

## 3. Emergency Kill Switch Integrity
The `PaperRiskGate` incorporates an immediate kill switch:
```python
risk_gate.trigger_kill_switch("Emergency Operator Intervention")
```
- **Veto Behavior:** When engaged, all simulated buy/sell orders, rebalance execution requests, and portfolio allocations are blocked with status `REJECTED`.
- **Verified in Tests:** Deterministically verified in `test_real_trading_invariant_and_kill_switch_blocks_rebalancing` and `test_failure_modes_unpriced_holdings_and_kill_switch`.

---

## 4. Privacy & Sensitive Credential Redaction
Automated regular expression sanitizers in `screen_ocr.py` and input document processors protect user privacy:
- **Permanent Account Numbers (PAN):** `[A-Z]{5}[0-9]{4}[A-Z]` $\to$ `[REDACTED_PAN]`.
- **Aadhaar Numbers:** 12-digit UID numbers $\to$ `[REDACTED_AADHAAR]`.
- **One-Time Passwords (OTPs):** 6-digit verification codes $\to$ `[REDACTED_OTP]`.
- **API Secrets & Keys:** Automated zero-secret scrubbing from logs and audit chains.

---

## 5. Provider Rights & Licensing Boundaries
- **Research vs Commercial Redistribution:**
  - Connectors (e.g. Yahoo Finance NSE, AMFI statutory feeds) are permitted strictly for local research and simulated paper trading.
  - Commercial distribution of real-time exchange tick streams requires an official vendor license from the National Stock Exchange of India (NSE) or Bombay Stock Exchange (BSE).
  - Aurxon QuantX does not scrape exchange web portals in violation of Akamai WAF policies.

---

## 6. Identified Deployment & Infrastructure Gaps

Prior to deploying Aurxon QuantX in a multi-tenant enterprise or cloud production environment, the following infrastructure gaps must be addressed:
1. **Authentication & Multi-User Authorization:**
   - Current portfolios use local identifiers (`portfolio_id`). Production deployment requires JWT / OAuth2 authentication with Role-Based Access Control (RBAC).
2. **Automated WAL Backups & Point-in-Time Recovery (PITR):**
   - SQLite WAL databases (`data/aurxon_paper_portfolio.sqlite` and `data/aurxon_market_data.sqlite`) currently rely on filesystem replication. An automated S3/GCS snapshot replication service is recommended.
3. **Encrypted at Rest:**
   - Database volumes should be mounted on encrypted block storage (e.g. LUKS or AWS EBS encryption).
