# Aurxon QuantX — Phase 5 Authentication & Authorization Architecture

## 1. Authentication Specification

Aurxon QuantX uses a token-based authentication architecture designed to operate with standard Python libraries, eliminating external binary dependencies while providing production-grade cryptographic security.

### Roles & Access Taxonomy
The user model ([schemas.py](file:///home/karann/Documents/AURXONQuant/backend/app/auth/schemas.py)) categorizes participants into 4 explicit roles:
1. **TRADER**: Can create paper portfolios, place simulated orders, execute rebalancing, and view their own portfolios and holdings.
2. **ANALYST**: Can access quantitative research dossiers, valuation engines, factor attribution, and screening reports.
3. **ADMIN**: Unrestricted administrative access, including system readiness audits, backup triggers, and cross-portfolio oversight for compliance.
4. **AUDITOR**: Read-only oversight of audit ledger records, execution provenance, and statutory cost calculations.

### Password Storage Security
Passwords are never stored in plaintext. They are protected using:
- **Algorithm**: PBKDF2 with HMAC-SHA256 ([security.py](file:///home/karann/Documents/AURXONQuant/backend/app/auth/security.py)).
- **Work Factor**: 100,000 hash iterations.
- **Salting**: 16 bytes (32 hex characters) of cryptographically random salt generated via `secrets.token_hex(16)` per user.
- **Storage Format**: `salt$derived_key_hex`.

### Token Lifecycle & Structure
Access tokens follow the standard Bearer header format (`Authorization: Bearer <token>`).
- **Signing Scheme**: HMAC-SHA256 using `AUTH_SECRET_KEY` configured in [config.py](file:///home/karann/Documents/AURXONQuant/backend/app/config.py).
- **Token Claims**:
  - `sub`: Immutable user identifier (`USR_...`).
  - `email`: User email address.
  - `role`: Assigned user role (e.g. `TRADER`, `ADMIN`).
  - `iat`: Timestamp of issuance (UNIX epoch).
  - `exp`: Timestamp of expiration (`iat + 86,400s` for 24 hours).
- **Validation**: Every incoming request decoding the token verifies signature integrity and expiration timestamp. Expired or tampered tokens return `HTTP 401 Unauthorized`.

---

## 2. Server-Enforced Authorization & IDOR Prevention

### Insecure Direct Object Reference (IDOR) Mitigation
In prior prototypes, endpoints accepted client-supplied query parameters like `portfolio_id` without authenticating who owned that portfolio. In Phase 5, server-side tenant ownership is enforced at the database layer:

1. **Database Schema Migration**:
   - The `paper_portfolios` table in `data/paper_portfolio.sqlite` now includes a `user_id TEXT DEFAULT 'USR_SYSTEM'` column with index `idx_portfolios_user`.
2. **Server-Enforced Access Verification**:
   - The `PaperPortfolioManager` exposes `verify_portfolio_access(portfolio_id, user_id, is_admin)` ([paper_manager.py](file:///home/karann/Documents/AURXONQuant/backend/app/trading/paper_manager.py#L1045)).
   - In [main.py](file:///home/karann/Documents/AURXONQuant/backend/app/main.py), all read, order, cancel, rebalance, and kill-switch endpoints invoke:
     ```python
     def check_portfolio_ownership(portfolio_id: str, current_user: User):
         is_admin = (current_user.role == UserRole.ADMIN)
         if not paper_manager.verify_portfolio_access(portfolio_id, current_user.user_id, is_admin=is_admin):
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail=f"FORBIDDEN: User {current_user.user_id} does not have access to portfolio '{portfolio_id}'. Cross-user access prohibited.",
             )
     ```
3. **Portfolio Listing Filtering**:
   - Calling `/api/v1/portfolio/list` filters portfolios by `WHERE user_id = ?` unless the authenticated user is an `ADMIN`. Tenant A can never enumerate Tenant B's portfolios.

---

## 3. Endpoints Implemented

| Endpoint | Method | Role Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/auth/register` | `POST` | Public | Registers a new user account with validated email and password. |
| `/api/v1/auth/login` | `POST` | Public | Verifies credentials and issues signed HMAC-SHA256 Bearer token. |
| `/api/v1/auth/me` | `GET` | Authenticated | Returns current authenticated user record and assigned role. |
| `/api/v1/portfolio/list` | `GET` | Authenticated | Returns portfolios owned strictly by the authenticated tenant. |
| `/api/v1/portfolio/create` | `POST` | Authenticated | Creates a new paper portfolio bound permanently to `current_user.user_id`. |
| `/api/v1/portfolio/intelligence` | `GET` | Owner or Admin | Returns unified portfolio analytics dossier after verifying ownership. |
| `/api/v1/paper/order` | `POST` | Owner or Admin | Places simulated order, ensuring order execution modifies owner's ledger only. |
| `/api/v1/admin/backup/*` | `*` | `ADMIN` | Administrative online backup creation and archive inspection. |

---

## 4. Verification & Two-User Acceptance Proof

The implementation is verified via `backend/tests/test_phase_5_hardening_and_security.py`:
- `test_unauthenticated_api_rejection`: Validates that unauthenticated requests to protected endpoints return `401 Unauthorized`.
- `test_invalid_or_expired_token_rejection`: Validates rejection of tampered tokens with invalid HMAC signatures.
- `test_idor_cross_user_portfolio_isolation`:
  - Registers User A and User B.
  - User B creates portfolio `PORT_PRIVATE_B`.
  - User A attempts direct read: receives **`HTTP 403 Forbidden`**.
  - User A attempts order placement: receives **`HTTP 403 Forbidden`**.
  - User A lists portfolios: `PORT_PRIVATE_B` is **completely absent**.
- All tests pass deterministically.
