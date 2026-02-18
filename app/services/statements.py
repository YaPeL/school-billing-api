from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from app.domain.dtos import InvoiceDTO, PaymentDTO, SchoolDTO, StudentDTO
from app.schemas.statement import InvoiceSummary, SchoolStatement, StatementTotals, StudentStatement
from app.services.billing_rules import ZERO, balance_due, credit_amount, invoice_status, paid_total


def build_student_statement(
    student: StudentDTO,
    invoices: list[InvoiceDTO],
    payments: list[PaymentDTO],
) -> StudentStatement:
    payments_by_invoice = _group_payments_by_invoice(payments)
    invoice_summaries = [_build_invoice_summary(invoice, payments_by_invoice[invoice.id]) for invoice in invoices]

    return StudentStatement(
        student_id=student.id,
        school_id=student.school_id,
        totals=_statement_totals(invoice_summaries),
        invoices=invoice_summaries,
    )


def build_school_statement(
    school: SchoolDTO,
    students: list[StudentDTO],
    invoices: list[InvoiceDTO],
    payments: list[PaymentDTO],
) -> SchoolStatement:
    payments_by_invoice = _group_payments_by_invoice(payments)
    invoice_summaries = [_build_invoice_summary(invoice, payments_by_invoice[invoice.id]) for invoice in invoices]

    return SchoolStatement(
        school_id=school.id,
        students_count=len(students),
        totals=_statement_totals(invoice_summaries),
        invoices=invoice_summaries,
    )


def _group_payments_by_invoice(payments: list[PaymentDTO]) -> dict[UUID, list[PaymentDTO]]:
    grouped: dict[UUID, list[PaymentDTO]] = defaultdict(list)
    for payment in payments:
        grouped[payment.invoice_id].append(payment)
    return grouped


def _build_invoice_summary(invoice: InvoiceDTO, payments: list[PaymentDTO]) -> InvoiceSummary:
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
