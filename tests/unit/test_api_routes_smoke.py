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
from app.services import invoices as invoice_service
from app.services import payments as payment_service


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


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_invoice_response_includes_status(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password", "test-pass")
    login_response = await client.post("/auth/login", json={"username": "admin", "password": "test-pass"})
    token = login_response.json()["access_token"]

    invoice_id = uuid7()
    student_id = uuid7()

    async def fake_create_invoice(*_args: object, **_kwargs: object) -> InvoiceDTO:
        return InvoiceDTO(
            id=invoice_id,
            student_id=student_id,
            total_amount=Decimal("100.00"),
            due_date=date(2026, 3, 1),
            issued_at=datetime(2026, 2, 1),
            status=InvoiceStatus.PENDING,
            description=None,
        )

    monkeypatch.setattr(invoice_service, "create_invoice", fake_create_invoice)
    response = await client.post(
        "/invoices",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": str(student_id), "total_amount": "100.00", "due_date": "2026-03-01"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == InvoiceStatus.PENDING


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_response_includes_kind(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password", "test-pass")
    login_response = await client.post("/auth/login", json={"username": "admin", "password": "test-pass"})
    token = login_response.json()["access_token"]

    payment_id = uuid7()
    invoice_id = uuid7()

    async def fake_create_payment(*_args: object, **_kwargs: object) -> PaymentDTO:
        return PaymentDTO(
            id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("10.00"),
            kind=PaymentKind.REFUND,
        )

    monkeypatch.setattr(payment_service, "create_payment", fake_create_payment)
    response = await client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"invoice_id": str(invoice_id), "amount": "10.00", "kind": "REFUND"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["kind"] == PaymentKind.REFUND
