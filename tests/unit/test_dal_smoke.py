from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.dal.invoice import create_invoice, delete_invoice, get_invoice_by_id, list_invoices, update_invoice
from app.dal.payment import create_payment, delete_payment, get_payment_by_id, list_payments, update_payment
from app.dal.school import create_school, delete_school, get_school_by_id, list_schools, update_school
from app.dal.student import create_student, delete_student, get_student_by_id, list_students, update_student
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.school import School
from app.models.student import Student


@pytest.mark.smoke
def test_school_crud_uses_session_methods() -> None:
    session = MagicMock(spec=Session)
    school_id = uuid4()

    created = create_school(session, data={"name": "Hogwarts"})
    assert isinstance(created, School)
    assert created.name == "Hogwarts"
    session.add.assert_called_once_with(created)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(created)

    session.get.return_value = created
    fetched = get_school_by_id(session, school_id=school_id)
    assert fetched is created
    session.get.assert_called_with(School, school_id)

    session.scalars.return_value = [created]
    listed = list_schools(session, offset=5, limit=10)
    assert listed == [created]
    session.scalars.assert_called_once()

    session.get.return_value = created
    updated = update_school(session, school_id=school_id, data={"name": "Beauxbatons"})
    assert updated is created
    assert created.name == "Beauxbatons"

    session.get.return_value = created
    deleted = delete_school(session, school_id=school_id)
    assert deleted is True
    session.delete.assert_called_with(created)


@pytest.mark.smoke
def test_student_crud_uses_session_methods() -> None:
    session = MagicMock(spec=Session)
    school_id = uuid4()
    student_id = uuid4()

    created = create_student(session, data={"school_id": school_id, "full_name": "Hermione Granger"})
    assert isinstance(created, Student)
    assert created.school_id == school_id
    assert created.full_name == "Hermione Granger"
    session.add.assert_called_once_with(created)

    session.get.return_value = created
    fetched = get_student_by_id(session, student_id=student_id)
    assert fetched is created
    session.get.assert_called_with(Student, student_id)

    session.scalars.return_value = [created]
    listed = list_students(session)
    assert listed == [created]

    session.get.return_value = created
    updated = update_student(session, student_id=student_id, data={"full_name": "H. Granger"})
    assert updated is created
    assert created.full_name == "H. Granger"

    session.get.return_value = created
    deleted = delete_student(session, student_id=student_id)
    assert deleted is True
    session.delete.assert_called_with(created)


@pytest.mark.smoke
def test_invoice_crud_uses_session_methods() -> None:
    session = MagicMock(spec=Session)
    student_id = uuid4()
    invoice_id = uuid4()

    created = create_invoice(
        session,
        data={
            "student_id": student_id,
            "total_amount": Decimal("100.00"),
            "due_date": date(2026, 2, 28),
            "description": "Tuition",
        },
    )
    assert isinstance(created, Invoice)
    assert created.student_id == student_id
    assert created.total_amount == Decimal("100.00")
    assert created.due_date == date(2026, 2, 28)
    assert created.description == "Tuition"

    session.get.return_value = created
    fetched = get_invoice_by_id(session, invoice_id=invoice_id)
    assert fetched is created
    session.get.assert_called_with(Invoice, invoice_id)

    session.scalars.return_value = [created]
    listed = list_invoices(session)
    assert listed == [created]

    session.get.return_value = created
    updated = update_invoice(session, invoice_id=invoice_id, data={"total_amount": Decimal("120.00")})
    assert updated is created
    assert created.total_amount == Decimal("120.00")

    session.get.return_value = created
    deleted = delete_invoice(session, invoice_id=invoice_id)
    assert deleted is True
    session.delete.assert_called_with(created)


@pytest.mark.smoke
def test_payment_crud_uses_session_methods() -> None:
    session = MagicMock(spec=Session)
    invoice_id = uuid4()
    payment_id = uuid4()

    created = create_payment(
        session,
        data={
            "invoice_id": invoice_id,
            "amount": Decimal("25.50"),
            "method": "bank_transfer",
            "reference": "ABC123",
        },
    )
    assert isinstance(created, Payment)
    assert created.invoice_id == invoice_id
    assert created.amount == Decimal("25.50")
    assert created.method == "bank_transfer"
    assert created.reference == "ABC123"

    session.get.return_value = created
    fetched = get_payment_by_id(session, payment_id=payment_id)
    assert fetched is created
    session.get.assert_called_with(Payment, payment_id)

    session.scalars.return_value = [created]
    listed = list_payments(session)
    assert listed == [created]

    session.get.return_value = created
    updated = update_payment(session, payment_id=payment_id, data={"amount": Decimal("30.00")})
    assert updated is created
    assert created.amount == Decimal("30.00")

    session.get.return_value = created
    deleted = delete_payment(session, payment_id=payment_id)
    assert deleted is True
    session.delete.assert_called_with(created)


@pytest.mark.smoke
def test_update_and_delete_return_none_or_false_when_record_does_not_exist() -> None:
    session = MagicMock(spec=Session)
    missing_id = uuid4()
    session.get.return_value = None

    assert update_school(session, school_id=missing_id, data={"name": "Missing"}) is None
    assert update_student(session, student_id=missing_id, data={"full_name": "Missing"}) is None
    assert update_invoice(session, invoice_id=missing_id, data={"total_amount": Decimal("1.00")}) is None
    assert update_payment(session, payment_id=missing_id, data={"amount": Decimal("1.00")}) is None

    assert delete_school(session, school_id=missing_id) is False
    assert delete_student(session, student_id=missing_id) is False
    assert delete_invoice(session, invoice_id=missing_id) is False
    assert delete_payment(session, payment_id=missing_id) is False
