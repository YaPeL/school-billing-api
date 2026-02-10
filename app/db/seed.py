from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.school import School
from app.models.student import Student


def _get_or_create_school(session: Session, name: str) -> School:
    school = session.scalar(select(School).where(School.name == name))
    if school is not None:
        return school

    school = School(name=name)
    session.add(school)
    session.flush()
    return school


def _get_or_create_student(session: Session, school_id: uuid.UUID, full_name: str) -> Student:
    student = session.scalar(select(Student).where(Student.school_id == school_id, Student.full_name == full_name))
    if student is not None:
        return student

    student = Student(school_id=school_id, full_name=full_name)
    session.add(student)
    session.flush()
    return student


def _get_or_create_invoice(
    session: Session,
    student_id: uuid.UUID,
    total_amount: Decimal,
    due_date: date,
    description: str,
) -> Invoice:
    invoice = session.scalar(
        select(Invoice).where(
            Invoice.student_id == student_id,
            Invoice.total_amount == total_amount,
            Invoice.due_date == due_date,
            Invoice.description == description,
        )
    )
    if invoice is not None:
        return invoice

    invoice = Invoice(
        student_id=student_id,
        total_amount=total_amount,
        due_date=due_date,
        description=description,
    )
    session.add(invoice)
    session.flush()
    return invoice


def _get_or_create_payment(
    session: Session,
    invoice_id: uuid.UUID,
    amount: Decimal,
    method: str,
    reference: str,
    paid_at: datetime,
) -> Payment:
    payment = session.scalar(
        select(Payment).where(
            Payment.invoice_id == invoice_id,
            Payment.amount == amount,
            Payment.method == method,
            Payment.reference == reference,
        )
    )
    if payment is not None:
        return payment

    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
        method=method,
        reference=reference,
        paid_at=paid_at,
    )
    session.add(payment)
    session.flush()
    return payment


def seed_db(session: Session) -> None:
    school = _get_or_create_school(session, "Springfield Elementary")

    lisa = _get_or_create_student(session, school.id, "Lisa Simpson")
    bart = _get_or_create_student(session, school.id, "Bart Simpson")

    paid_invoice = _get_or_create_invoice(
        session=session,
        student_id=lisa.id,
        total_amount=Decimal("1000.00"),
        due_date=date(2026, 2, 28),
        description="Annual tuition",
    )
    partial_invoice = _get_or_create_invoice(
        session=session,
        student_id=bart.id,
        total_amount=Decimal("800.00"),
        due_date=date(2026, 2, 28),
        description="Annual tuition",
    )

    _get_or_create_payment(
        session=session,
        invoice_id=paid_invoice.id,
        amount=Decimal("600.00"),
        method="bank_transfer",
        reference="DEMO-PAID-1",
        paid_at=datetime(2026, 1, 10, 13, 0, tzinfo=UTC),
    )
    _get_or_create_payment(
        session=session,
        invoice_id=paid_invoice.id,
        amount=Decimal("400.00"),
        method="card",
        reference="DEMO-PAID-2",
        paid_at=datetime(2026, 1, 20, 13, 0, tzinfo=UTC),
    )
    _get_or_create_payment(
        session=session,
        invoice_id=partial_invoice.id,
        amount=Decimal("300.00"),
        method="cash",
        reference="DEMO-PARTIAL-1",
        paid_at=datetime(2026, 1, 15, 13, 0, tzinfo=UTC),
    )
