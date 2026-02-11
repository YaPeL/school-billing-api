from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.settings import settings
from app.db.session import get_db
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def override_db() -> Generator[None, None, None]:
    async def override_get_db() -> AsyncGenerator[Session, None]:
        yield MagicMock(spec=Session)

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def client(override_db: None) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.smoke
@pytest.mark.anyio
async def test_health_endpoint_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_school_requires_auth(client: httpx.AsyncClient) -> None:
    response = await client.post("/schools", json={"name": "Springfield Elementary"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.smoke
@pytest.mark.anyio
async def test_auth_login_returns_token(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password", "test-pass")

    response = await client.post("/auth/login", json={"username": "admin", "password": "test-pass"})

    body = response.json()
    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


@pytest.mark.smoke
@pytest.mark.anyio
async def test_auth_login_token_contains_admin_claims(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password", "test-pass")

    login_response = await client.post("/auth/login", json={"username": "admin", "password": "test-pass"})
    token = login_response.json()["access_token"]

    claims = decode_access_token(token)
    assert claims.sub == "admin"
    assert claims.role == "admin"
