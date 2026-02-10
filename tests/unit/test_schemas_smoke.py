from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.invoice import InvoiceCreate
from app.schemas.payment import PaymentCreate


@pytest.mark.smoke
@pytest.mark.parametrize(
    "amount",
    [Decimal("0.00"), Decimal("-1.00")],
)
def test_invoice_create_rejects_non_positive_total_amount(amount: Decimal) -> None:
    with pytest.raises(ValidationError):
        InvoiceCreate(student_id=uuid4(), total_amount=amount, due_date=date(2026, 3, 1))


@pytest.mark.smoke
@pytest.mark.parametrize(
    "amount",
    [Decimal("0.00"), Decimal("-5.00")],
)
def test_payment_create_rejects_non_positive_amount(amount: Decimal) -> None:
    with pytest.raises(ValidationError):
        PaymentCreate(invoice_id=uuid4(), amount=amount)
