from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from uuid_extensions import uuid7

from app.domain.enums import InvoiceStatus, PaymentKind
from app.schemas.invoice import InvoiceCreate, InvoiceRead
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate


@pytest.mark.smoke
@pytest.mark.parametrize(
    "amount",
    [Decimal("0.00"), Decimal("-1.00")],
)
def test_invoice_create_rejects_non_positive_total_amount(amount: Decimal) -> None:
    with pytest.raises(ValidationError):
        InvoiceCreate(student_id=uuid7(), total_amount=amount, due_date=date(2026, 3, 1))


@pytest.mark.smoke
@pytest.mark.parametrize(
    "amount",
    [Decimal("0.00"), Decimal("-5.00")],
)
def test_payment_create_rejects_non_positive_amount(amount: Decimal) -> None:
    with pytest.raises(ValidationError):
        PaymentCreate(invoice_id=uuid7(), amount=amount)


@pytest.mark.smoke
def test_payment_create_defaults_kind_to_payment() -> None:
    payment = PaymentCreate(invoice_id=uuid7(), amount=Decimal("1.00"))
    assert payment.kind == PaymentKind.PAYMENT


@pytest.mark.smoke
def test_payment_update_kind_is_optional_but_not_nullable() -> None:
    omitted = PaymentUpdate()
    assert omitted.kind is None

    with pytest.raises(ValidationError):
        PaymentUpdate(kind=None)


@pytest.mark.smoke
def test_read_schemas_include_invoice_status_and_payment_kind() -> None:
    invoice = InvoiceRead(
        id=uuid7(),
        student_id=uuid7(),
        total_amount=Decimal("10.00"),
        issued_at=datetime(2026, 2, 1),
        due_date=date(2026, 3, 1),
        status=InvoiceStatus.PENDING,
    )
    payment = PaymentRead(
        id=uuid7(),
        invoice_id=uuid7(),
        amount=Decimal("10.00"),
        kind=PaymentKind.PAYMENT,
    )

    assert invoice.status == InvoiceStatus.PENDING
    assert payment.kind == PaymentKind.PAYMENT
