from __future__ import annotations

from collections.abc import Generator
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_db
from app.main import app
from app.schemas.statement import StatementTotals, StudentStatement


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def override_db() -> Generator[None, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
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
async def test_create_school_endpoint_happy_path_with_admin_token(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "admin_password", "test-pass")

    school_id = uuid4()
    school = SimpleNamespace(id=school_id, name="Springfield Elementary", created_at=None, updated_at=None)

    import app.dal.school as school_dal

    monkeypatch.setattr(school_dal, "create_school", lambda *_args, **_kwargs: school)

    login_response = await client.post("/auth/login", json={"username": "admin", "password": "test-pass"})
    token = login_response.json()["access_token"]

    response = await client.post(
        "/schools",
        json={"name": "Springfield Elementary"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(school_id),
        "name": "Springfield Elementary",
        "created_at": None,
        "updated_at": None,
    }


@pytest.mark.smoke
@pytest.mark.anyio
async def test_student_statement_endpoint_happy_path(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    student_id = uuid4()
    school_id = uuid4()

    statement = StudentStatement(
        student_id=student_id,
        school_id=school_id,
        totals=StatementTotals(
            invoiced_total=Decimal("100.00"),
            paid_total=Decimal("40.00"),
            balance_due_total=Decimal("60.00"),
            credit_total=Decimal("0.00"),
        ),
        invoices=[],
    )

    import app.services.statements as statements_service

    monkeypatch.setattr(
        statements_service,
        "get_student_statement",
        lambda *_args, **_kwargs: statement,
    )

    response = await client.get(f"/students/{student_id}/statement")

    assert response.status_code == 200
    assert response.json() == {
        "student_id": str(student_id),
        "school_id": str(school_id),
        "totals": {
            "invoiced_total": "100.00",
            "paid_total": "40.00",
            "balance_due_total": "60.00",
            "credit_total": "0.00",
        },
        "invoices": [],
    }


@pytest.mark.smoke
@pytest.mark.anyio
async def test_get_invoice_payments_endpoint_happy_path(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoice_id = uuid4()
    payment_id = uuid4()

    invoice = SimpleNamespace(id=invoice_id)
    payment = SimpleNamespace(
        id=payment_id,
        invoice_id=invoice_id,
        amount=Decimal("30.00"),
        method="card",
        reference="pay-123",
        paid_at=None,
        created_at=None,
        updated_at=None,
    )

    import app.dal.invoice as invoice_dal
    import app.dal.payment as payment_dal

    monkeypatch.setattr(invoice_dal, "get_invoice_by_id", lambda *_args, **_kwargs: invoice)
    monkeypatch.setattr(payment_dal, "list_payments_by_invoice_id", lambda *_args, **_kwargs: [payment])

    response = await client.get(f"/invoices/{invoice_id}/payments")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(payment_id),
            "invoice_id": str(invoice_id),
            "amount": "30.00",
            "method": "card",
            "reference": "pay-123",
            "paid_at": None,
            "created_at": None,
            "updated_at": None,
        }
    ]
