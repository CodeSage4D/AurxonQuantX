"""AURXON QuantX — Authentication & Authorization Schemas.
Enforces typed user models, role definitions, and token payloads.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    TRADER = "TRADER"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"


class User(BaseModel):
    """Authenticated user profile with role-based access attributes."""
    user_id: str = Field(description="Unique immutable user identifier (e.g. USR_xxx)")
    email: str = Field(description="Canonical user email address")
    full_name: str = Field(default="Aurxon User", description="Display name")
    role: UserRole = Field(default=UserRole.TRADER, description="Assigned role")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserRegisterRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="User email address")
    password: str = Field(min_length=8, description="User password (min 8 characters)")
    full_name: Optional[str] = Field(default=None, description="Optional full name")
    role: Optional[UserRole] = Field(default=UserRole.TRADER, description="Initial requested role")


class UserLoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="User email address")
    password: str = Field(description="User password")


class TokenResponse(BaseModel):
    access_token: str = Field(description="Signed Bearer JWT / HMAC access token")
    token_type: str = Field(default="bearer")
    expires_in_seconds: int
    user: User
