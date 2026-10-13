"""AURXON QuantX — Cryptographic Security & Token Management.
Implements:
- PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and per-user salt.
- Cryptographically signed HMAC-SHA256 Bearer tokens with expiration.
- Zero external C-library dependency constraints.
"""

import base64
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Optional

from app.config import settings
from app.auth.schemas import User, UserRole


def hash_password(password: str) -> str:
    """Generates a secure PBKDF2-HMAC-SHA256 password hash with 16-byte random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_record: str) -> bool:
    """Verifies a plain text password against stored salt$key hash."""
    try:
        salt, expected_hex = hashed_record.split("$", 1)
        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return hmac.compare_digest(actual_key.hex(), expected_hex)
    except Exception:
        return False


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("utf-8"))


from typing import Any, Dict, Optional, Union

def create_access_token(
    user: Union[User, str],
    role: Optional[str] = None,
    email: Optional[str] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """Generates a cryptographically signed HMAC-SHA256 access token."""
    expiry_min = expires_minutes or settings.AUTH_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    exp = int((now + timedelta(minutes=expiry_min)).timestamp())

    if isinstance(user, User):
        user_id = user.user_id
        user_email = user.email
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    else:
        user_id = str(user)
        user_email = email or f"{user_id.lower()}@aurxon.internal"
        user_role = role or "TRADER"

    payload = {
        "sub": user_id,
        "email": user_email,
        "role": user_role,
        "iat": int(now.timestamp()),
        "exp": exp,
    }

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates signature and expiration of access token, returning payload dict."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        actual_sig = _b64decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if not exp or datetime.now(timezone.utc).timestamp() > exp:
            return None

        return payload
    except Exception:
        return None
