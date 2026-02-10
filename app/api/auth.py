from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, validate_admin_credentials
from app.core.settings import settings
from app.schemas.auth import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("app.auth")


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest) -> Token:
    if settings.admin_password == "change_me":
        log.warning("ADMIN_PASSWORD is set to 'change_me' (demo default). Do not use in production.")

    if not validate_admin_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token = create_access_token(subject=payload.username, role="admin")
    return Token(access_token=access_token)
