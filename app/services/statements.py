from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.dal import invoice as invoice_dal
from app.dal import payment as payment_dal
from app.dal import school as school_dal
from app.dal import student as student_dal
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.statement import InvoiceSummary, SchoolStatement, StatementTotals, StudentStatement
from app.services.billing_rules import ZERO, balance_due, credit_amount, invoice_status, paid_total


def get_student_statement(session: Session, student_id: UUID) -> StudentStatement:
    student = student_dal.get_student_by_id(session, student_id=student_id)
    if student is None:
        raise ValueError(f"student {student_id} not found")

    invoices = invoice_dal.list_invoices_by_student_id(session, student_id=student.id)
    payments_by_invoice = _payments_by_invoice(session, invoices)
    invoice_summaries = [_build_invoice_summary(invoice, payments_by_invoice[invoice.id]) for invoice in invoices]

    return StudentStatement(
        student_id=student.id,
        school_id=student.school_id,
        totals=_statement_totals(invoice_summaries),
        invoices=invoice_summaries,
    )


def get_school_statement(session: Session, school_id: UUID) -> SchoolStatement:
    school = school_dal.get_school_by_id(session, school_id=school_id)
    if school is None:
        raise ValueError(f"school {school_id} not found")

    students = student_dal.list_students_by_school_id(session, school_id=school.id)
    student_ids = [student.id for student in students]
    invoices = invoice_dal.list_invoices_by_student_ids(session, student_ids=student_ids)
    payments_by_invoice = _payments_by_invoice(session, invoices)
    invoice_summaries = [_build_invoice_summary(invoice, payments_by_invoice[invoice.id]) for invoice in invoices]

    return SchoolStatement(
        school_id=school.id,
        students_count=len(students),
        totals=_statement_totals(invoice_summaries),
        invoices=invoice_summaries,
    )


def _payments_by_invoice(session: Session, invoices: list[Invoice]) -> dict[UUID, list[Payment]]:
    invoice_ids = [invoice.id for invoice in invoices]
    payments = payment_dal.list_payments_by_invoice_ids(session, invoice_ids=invoice_ids)

    grouped: dict[UUID, list[Payment]] = defaultdict(list)
    for payment in payments:
        grouped[payment.invoice_id].append(payment)
    return grouped


def _build_invoice_summary(invoice: Invoice, payments: list[Payment]) -> InvoiceSummary:
    summary_paid_total = paid_total(payments)
    summary_balance_due = balance_due(invoice.total_amount, payments)
    summary_credit_amount = credit_amount(invoice.total_amount, payments)

    return InvoiceSummary(
        id=invoice.id,
        student_id=invoice.student_id,
        total_amount=invoice.total_amount,
        due_date=invoice.due_date,
        description=invoice.description,
        paid_total=summary_paid_total,
        balance_due=summary_balance_due,
        credit_amount=summary_credit_amount,
        status=invoice_status(invoice.total_amount, payments),
    )


def _statement_totals(invoice_summaries: list[InvoiceSummary]) -> StatementTotals:
    return StatementTotals(
        invoiced_total=sum((item.total_amount for item in invoice_summaries), start=ZERO),
        paid_total=sum((item.paid_total for item in invoice_summaries), start=ZERO),
        balance_due_total=sum((item.balance_due for item in invoice_summaries), start=ZERO),
        credit_total=sum((item.credit_amount for item in invoice_summaries), start=ZERO),
    )
