from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.domain.enums import InvoiceStatus
from app.services import billing_rules
from app.services.statements import get_school_statement, get_student_statement


def _payment(amount: str, invoice_id: object) -> SimpleNamespace:
    return SimpleNamespace(amount=Decimal(amount), invoice_id=invoice_id)


@pytest.mark.smoke
def test_business_rule_helpers_support_partial_paid_and_credit() -> None:
    payments = [_payment("40.00", uuid4()), _payment("30.00", uuid4())]

    assert billing_rules.paid_total(payments) == Decimal("70.00")
    assert billing_rules.balance_due(Decimal("100.00"), payments) == Decimal("30.00")
    assert billing_rules.credit_amount(Decimal("50.00"), payments) == Decimal("20.00")
    assert billing_rules.invoice_status(Decimal("100.00"), payments) == InvoiceStatus.PARTIAL
    assert billing_rules.invoice_status(Decimal("70.00"), payments) == InvoiceStatus.PAID
    assert billing_rules.invoice_status(Decimal("50.00"), payments) == InvoiceStatus.CREDIT
    assert billing_rules.invoice_status(Decimal("100.00"), []) == InvoiceStatus.PENDING


@pytest.mark.smoke
def test_get_student_statement_aggregates_totals_and_invoice_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock(spec=Session)
    school_id = uuid4()
    student_id = uuid4()
    invoice_1_id = uuid4()
    invoice_2_id = uuid4()

    student = SimpleNamespace(id=student_id, school_id=school_id, full_name="Ada Lovelace")
    invoices = [
        SimpleNamespace(
            id=invoice_1_id,
            student_id=student_id,
            total_amount=Decimal("100.00"),
            due_date=date(2026, 3, 1),
            description="March tuition",
        ),
        SimpleNamespace(
            id=invoice_2_id,
            student_id=student_id,
            total_amount=Decimal("50.00"),
            due_date=date(2026, 4, 1),
            description="Materials",
        ),
    ]
    payments = [
        _payment("60.00", invoice_1_id),
        _payment("40.00", invoice_1_id),
        _payment("70.00", invoice_2_id),
    ]

    import app.dal.invoice as invoice_dal
    import app.dal.payment as payment_dal
    import app.dal.student as student_dal

    monkeypatch.setattr(student_dal, "get_student_by_id", lambda *_args, **_kwargs: student)
    monkeypatch.setattr(invoice_dal, "list_invoices_by_student_id", lambda *_args, **_kwargs: invoices)
    monkeypatch.setattr(payment_dal, "list_payments_by_invoice_ids", lambda *_args, **_kwargs: payments)

    statement = get_student_statement(session, student_id)

    assert statement.student_id == student_id
    assert statement.school_id == school_id
    assert statement.totals.invoiced_total == Decimal("150.00")
    assert statement.totals.paid_total == Decimal("170.00")
    assert statement.totals.balance_due_total == Decimal("-20.00")
    assert statement.totals.credit_total == Decimal("20.00")

    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PAID, InvoiceStatus.CREDIT]
    assert statement.invoices[0].balance_due == Decimal("0.00")
    assert statement.invoices[1].credit_amount == Decimal("20.00")


@pytest.mark.smoke
def test_get_school_statement_aggregates_across_students(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock(spec=Session)
    school_id = uuid4()
    student_1_id = uuid4()
    student_2_id = uuid4()
    invoice_1_id = uuid4()
    invoice_2_id = uuid4()

    school = SimpleNamespace(id=school_id, name="STEM Academy")
    students = [
        SimpleNamespace(id=student_1_id, school_id=school_id, full_name="Grace Hopper"),
        SimpleNamespace(id=student_2_id, school_id=school_id, full_name="Alan Turing"),
    ]
    invoices = [
        SimpleNamespace(
            id=invoice_1_id,
            student_id=student_1_id,
            total_amount=Decimal("80.00"),
            due_date=date(2026, 3, 10),
            description=None,
        ),
        SimpleNamespace(
            id=invoice_2_id,
            student_id=student_2_id,
            total_amount=Decimal("120.00"),
            due_date=date(2026, 3, 15),
            description=None,
        ),
    ]
    payments = [_payment("20.00", invoice_1_id), _payment("120.00", invoice_2_id)]

    import app.dal.invoice as invoice_dal
    import app.dal.payment as payment_dal
    import app.dal.school as school_dal
    import app.dal.student as student_dal

    monkeypatch.setattr(school_dal, "get_school_by_id", lambda *_args, **_kwargs: school)
    monkeypatch.setattr(student_dal, "list_students_by_school_id", lambda *_args, **_kwargs: students)
    monkeypatch.setattr(invoice_dal, "list_invoices_by_student_ids", lambda *_args, **_kwargs: invoices)
    monkeypatch.setattr(payment_dal, "list_payments_by_invoice_ids", lambda *_args, **_kwargs: payments)

    statement = get_school_statement(session, school_id)

    assert statement.school_id == school_id
    assert statement.students_count == 2
    assert statement.totals.invoiced_total == Decimal("200.00")
    assert statement.totals.paid_total == Decimal("140.00")
    assert statement.totals.balance_due_total == Decimal("60.00")
    assert statement.totals.credit_total == Decimal("0.00")
    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PARTIAL, InvoiceStatus.PAID]


@pytest.mark.smoke
def test_statement_services_raise_for_missing_entities(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock(spec=Session)
    missing_id = uuid4()

    import app.dal.school as school_dal
    import app.dal.student as student_dal

    monkeypatch.setattr(student_dal, "get_student_by_id", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(school_dal, "get_school_by_id", lambda *_args, **_kwargs: None)

    with pytest.raises(ValueError):
        get_student_statement(session, missing_id)

    with pytest.raises(ValueError):
        get_school_statement(session, missing_id)
