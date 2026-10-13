# Aurxon QuantX — Phase 4.4 Data Governance & Provider Rights

## 1. Overview & System Identity
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.4 — Workstream G: Security and Execution Boundaries
- **Module:** `backend/app/config.py`, `backend/app/sources/registry.py`, `backend/app/trading/risk_gate.py`

This document outlines the data governance policies, provider intellectual property boundaries, execution safeguards, and credential privacy protocols enforced across **Aurxon QuantX**.

---

## 2. Technical Accessibility vs Legal Rights

A foundational engineering principle of **Aurxon QuantX** is the strict demarcation between technical accessibility and legal provider rights:
> *"A registered provider is not necessarily an operational provider. Technical ability to fetch an HTTP payload does not convey the legal right to redistribute or commercialize it."*

### Provider Matrix Governance

| Data Channel | Technical Accessibility | Commercial Redistribution Status | Authorized Scope |
| :--- | :--- | :--- | :--- |
| **AMFI Statutory Feed** | Unrestricted HTTPS | Public non-commercial use permitted | Mutual Fund NAV tracking and scheme master |
| **RBI Reference Rates** | Unrestricted HTTPS | Public non-commercial statutory reference | INR Risk-free rate calibration ($R_f$) |
| **Yahoo Finance NSE** | Unrestricted HTTPS | Research / Non-commercial use only | Offline research, testing, portfolio analytics |
| **NSE / BSE Live WAF** | Akamai WAF blocked | Requires formal exchange vendor license | Live trading feeds (Blocked in free tier) |
| **Alpha Vantage** | API Key authenticated | Tier-limited free tier | Supplementary research |

---

## 3. Anti-Silent-Substitution Invariant

In quantitative accounting and portfolio analytics, silent fallback to synthetic or fabricated data is strictly prohibited:
1. **No Phantom Quotes:** If a price cannot be verified from the local market data store or permitted feeds, it is classified as `UNPRICED` / `UNAVAILABLE`.
2. **No Zero Substitution:** A missing price is NEVER coerced to ₹0.00, as doing so creates artificial 100% paper drawdowns and falsifies portfolio metrics.
3. **Transparent Badges:** Every displayed holding, valuation multiple, or factor exposure discloses its data provider (`AMFI`, `YAHOO_FINANCE_NSE`, `NSE_BHAVCOPY`, `SYNTHETIC_BENCHMARK`) and timestamp.

---

## 4. Execution Boundary & Risk Controls

### 4.1 Strict Simulation Invariant
```python
ENABLE_REAL_TRADING: bool = False
```
- Real-money trading is disabled by default and hard-locked.
- No live broker API SDKs (Kite Connect, SmartAPI, Breeze) are integrated or routed to.
- Any attempt to route orders externally raises an immediate system panic.

### 4.2 Emergency Kill Switch
The `PaperRiskGate` incorporates a persistent emergency kill switch:
```python
risk_gate.trigger_kill_switch("Operator Emergency Handoff")
```
When active, all order submissions, rebalancing transactions, and portfolio adjustments fail-closed with HTTP 403 / Risk Veto.

### 4.3 Redaction of Personal & Secret Data
The system includes automated regex guards preventing storage or transmission of:
- Indian Permanent Account Numbers (PAN: `[A-Z]{5}[0-9]{4}[A-Z]`).
- Aadhaar Numbers (12-digit UID).
- Two-factor OTP codes and broker session tokens.
- API keys, secrets, and private credentials.
