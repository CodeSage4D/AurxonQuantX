# AURXON Security Review & Threat Model

**Status:** Hardened Specification  
**Version:** 1.0.0 (Phase 1.5 Gate)  

---

## 1. Local Network & Host Boundary Controls

1. **Loopback Service Binding:**
   - The FastAPI backend binds strictly to loopback interface `127.0.0.1` (configurable in [config.py](file:///home/karann/Documents/AURXONQuant/backend/app/config.py#L18)).
   - The server is never exposed to public interfaces (`0.0.0.0`) by default.
2. **CORS Isolation:**
   - Permitted origins are explicitly restricted to `http://localhost:5173`, `http://localhost:1420`, and `tauri://localhost`.
3. **Environment & Secret Protection:**
   - Secrets (`.env`, `.pem`, API keys) are strictly ignored by Git.
   - All runtime configurations mask and never log raw credential tokens.

---

## 2. Broker & Banking Privacy Boundary

1. **Zero Credential Collection Policy:**
   - The application does not collect, store, parse, or transmit:
     - Broker login passwords, PINs, or MPINs.
     - One-Time Passwords (OTPs) or 2FA codes.
     - Active session cookies or OAuth tokens.
2. **Active Regex Privacy Filter:**
   - Incoming context to the [ScreenOCRCompanion](file:///home/karann/Documents/AURXONQuant/backend/app/companion/screen_ocr.py#L29) passes through regex filters redacting credit card numbers, OTPs, and password strings before ingestion into memory or downstream models.
3. **Automated Order Placement Lock:**
   - Real-money order execution is hard-locked (`ENABLE_REAL_TRADING = false`).
   - The platform strictly supports financial research, paper trading, and deterministic scenario simulation.

---

## 3. Cryptographic Audit Ledger & Tamper Detection

1. **Realistic Threat Model for Local SQLite:**
   - A raw SQLite database file on disk is inherently mutable by any local process possessing write permissions. Calling a standard SQLite database "immutable" is a security misnomer.
2. **Implemented Solution: Sequential Cryptographic Hash Chain:**
   - Each audit record is cryptographically linked to its predecessor via SHA-256:
     $$\text{chained\_hash}_i = \text{SHA-256}(\text{sequence}_i : \text{chained\_hash}_{i-1} : \text{content\_hash}_i : \text{timestamp}_i)$$
   - The [verify_chain_integrity](file:///home/karann/Documents/AURXONQuant/backend/app/evidence/ledger.py#L107) function validates the entire chain from genesis (`"0"*64`) to head.
   - Any manual edit, record deletion, or row injection in SQLite alters the hash cascade and is detected upon verification.

---

## 4. Untrusted Retrieved Web Content & Prompt Injection

1. Web content from external sites, filings, or forums is treated as untrusted data.
2. Active neutralization filters strip `<script>` tags, control characters, and injection directives (e.g. `ignore all previous instructions`).
3. Retrieved text is passed as a data payload, never as executable system instructions.
