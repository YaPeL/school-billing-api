from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt

from app.core.settings import settings
from app.schemas.auth import UserClaims


def create_access_token(subject: str, role: str, ttl_minutes: int | None = None) -> str:
    ttl = ttl_minutes if ttl_minutes is not None else settings.admin_token_ttl_minutes
    expires_at = datetime.now(UTC) + timedelta(minutes=ttl)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": int(expires_at.timestamp()),
    }
    return cast(str, jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm))


def decode_access_token(token: str) -> UserClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("invalid token") from exc

    try:
        return UserClaims.model_validate(payload)
    except Exception as exc:
        raise ValueError("invalid claims") from exc


def validate_admin_credentials(username: str, password: str) -> bool:
    return secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(
        password,
        settings.admin_password,
    )
