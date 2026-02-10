from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.schemas.auth import UserClaims

bearer_scheme = HTTPBearer(auto_error=False)


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserClaims:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_error()

    try:
        return decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise _auth_error() from exc


async def require_admin(current_user: Annotated[UserClaims, Depends(get_current_user)]) -> UserClaims:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
