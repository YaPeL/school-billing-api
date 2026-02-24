from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extensions import uuid7

from app.core.security import decode_access_token
from app.core.settings import settings
from app.db.session import get_db
from app.domain.dtos import InvoiceDTO, PaymentDTO
from app.domain.enums import InvoiceStatus, PaymentKind
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def override_db() -> Generator[None, None, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield MagicMock(spec=AsyncSession)

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


async def _admin_headers(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    monkeypatch.setattr(settings, "admin_password", "test-pass")
    response = await client.post("/auth/login", json={"username": "admin", "password": "test-pass"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.smoke
@pytest.mark.anyio
async def test_invoice_create_payload_includes_status(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_create_invoice(_repo: object, data: dict[str, object]) -> InvoiceDTO:
        return InvoiceDTO(
            id=uuid7(),
            student_id=data["student_id"],
            total_amount=data["total_amount"],
            due_date=data["due_date"],
            issued_at=datetime(2026, 2, 1),
            status=InvoiceStatus.PENDING,
        )

    monkeypatch.setattr("app.services.invoices.create_invoice", fake_create_invoice)
    headers = await _admin_headers(client, monkeypatch)

    response = await client.post(
        "/invoices",
        json={"student_id": str(uuid7()), "total_amount": "100.00", "due_date": str(date(2026, 3, 1))},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


@pytest.mark.smoke
@pytest.mark.anyio
async def test_payment_create_payload_includes_kind(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_create_payment(_payment_repo: object, _invoice_repo: object, data: dict[str, object]) -> PaymentDTO:
        return PaymentDTO(
            id=uuid7(),
            invoice_id=data["invoice_id"],
            amount=Decimal("25.00"),
            kind=PaymentKind.REFUND,
            paid_at=None,
            method=None,
            reference=None,
        )

    monkeypatch.setattr("app.services.payments.create_payment", fake_create_payment)
    headers = await _admin_headers(client, monkeypatch)

    response = await client.post(
        "/payments",
        json={"invoice_id": str(uuid7()), "amount": "25.00", "kind": "REFUND"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "REFUND"


@pytest.mark.smoke
@pytest.mark.anyio
async def test_payment_patch_rejects_null_kind_with_422(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_if_called(*_args: object, **_kwargs: object) -> PaymentDTO:
        raise AssertionError("service update should not run for schema-invalid payload")

    monkeypatch.setattr("app.services.payments.update_payment", fail_if_called)
    headers = await _admin_headers(client, monkeypatch)

    response = await client.patch(f"/payments/{uuid7()}", json={"kind": None}, headers=headers)

    assert response.status_code == 422
