from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.invoice import create_invoice
from app.dal.payment import create_payment
from app.dal.repos.sqlalchemy_invoice_repo import SQLAlchemyInvoiceRepo
from app.dal.repos.sqlalchemy_payment_repo import SQLAlchemyPaymentRepo
from app.dal.repos.sqlalchemy_school_repo import SQLAlchemySchoolRepo
from app.dal.repos.sqlalchemy_student_repo import SQLAlchemyStudentRepo
from app.dal.school import create_school
from app.dal.student import create_student
from app.domain.enums import InvoiceStatus
from app.services.use_cases import GetSchoolStatement, GetStudentStatement


@pytest.mark.integration
@pytest.mark.anyio
async def test_statements_with_real_postgres_support_partial_paid_and_credit(db_session: AsyncSession) -> None:
    school = await create_school(db_session, data={"name": "Integration Academy"})
    student = await create_student(db_session, data={"school_id": school.id, "full_name": "Integration Student"})

    pending_invoice = await create_invoice(
        db_session,
        data={
            "student_id": student.id,
            "total_amount": Decimal("100.00"),
            "due_date": date(2026, 3, 15),
            "description": "Pending",
        },
    )
    partial_invoice = await create_invoice(
        db_session,
        data={
            "student_id": student.id,
            "total_amount": Decimal("80.00"),
            "due_date": date(2026, 3, 20),
            "description": "Partial",
        },
    )
    paid_invoice = await create_invoice(
        db_session,
        data={
            "student_id": student.id,
            "total_amount": Decimal("60.00"),
            "due_date": date(2026, 3, 25),
            "description": "Paid",
        },
    )
    credit_invoice = await create_invoice(
        db_session,
        data={
            "student_id": student.id,
            "total_amount": Decimal("40.00"),
            "due_date": date(2026, 3, 30),
            "description": "Credit",
        },
    )

    await create_payment(db_session, data={"invoice_id": partial_invoice.id, "amount": Decimal("50.00")})
    await create_payment(db_session, data={"invoice_id": paid_invoice.id, "amount": Decimal("60.00")})
    await create_payment(db_session, data={"invoice_id": credit_invoice.id, "amount": Decimal("50.00")})

    student_statement = await GetStudentStatement(
        student_repo=SQLAlchemyStudentRepo(db_session),
        invoice_repo=SQLAlchemyInvoiceRepo(db_session),
        payment_repo=SQLAlchemyPaymentRepo(db_session),
    )(student.id)

    assert student_statement.student_id == student.id
    assert student_statement.totals.invoiced_total == Decimal("280.00")
    assert student_statement.totals.paid_total == Decimal("160.00")
    assert student_statement.totals.balance_due_total == Decimal("120.00")
    assert student_statement.totals.credit_total == Decimal("10.00")

    invoice_statuses = {invoice.id: invoice.status for invoice in student_statement.invoices}
    assert invoice_statuses[pending_invoice.id] == InvoiceStatus.PENDING
    assert invoice_statuses[partial_invoice.id] == InvoiceStatus.PARTIAL
    assert invoice_statuses[paid_invoice.id] == InvoiceStatus.PAID
    assert invoice_statuses[credit_invoice.id] == InvoiceStatus.CREDIT

    school_statement = await GetSchoolStatement(
        school_repo=SQLAlchemySchoolRepo(db_session),
        student_repo=SQLAlchemyStudentRepo(db_session),
        invoice_repo=SQLAlchemyInvoiceRepo(db_session),
        payment_repo=SQLAlchemyPaymentRepo(db_session),
    )(school.id)

    assert school_statement.school_id == school.id
    assert school_statement.students_count == 1
    assert school_statement.totals == student_statement.totals
