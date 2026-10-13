"""AURXON QuantX — Authentication & Role Dependencies.
FastAPI dependencies enforcing authenticated user contexts and role authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.auth.schemas import User, UserRole
from app.auth.security import decode_access_token
from app.auth.user_store import user_store

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> User:
    """Enforces valid Bearer access token and resolves active User record."""
    if not credentials or not credentials.credentials:
        if settings.AUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED: Missing or invalid authentication token. Please authenticate via /api/v1/auth/login.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Fallback when AUTH_ENABLED is False (dev convenience)
        fallback = user_store.get_user_by_email("trader@aurxon.internal")
        if fallback:
            return fallback
        return User(
            user_id="USR_DEV_DEFAULT",
            email="developer@aurxon.internal",
            role=UserRole.ADMIN,
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="UNAUTHORIZED: Token has expired or signature is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    if user_id == "USR_SYSTEM":
        return User(
            user_id="USR_SYSTEM",
            email="system@aurxon.internal",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )

    user = user_store.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="UNAUTHORIZED: User account does not exist or has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Optional[User]:
    """Resolves authenticated user if valid token present, otherwise None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(*roles: UserRole):
    """Enforces specific user role authorization."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"FORBIDDEN: User role '{current_user.role.value}' is not authorized for this operation.",
            )
        return current_user
    return role_checker
