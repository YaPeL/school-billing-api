from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from app.domain.dtos import InvoiceDTO, PaymentDTO, SchoolDTO, StudentDTO
from app.schemas.statement import InvoiceSummary, SchoolStatement, StatementTotals, StudentStatement
from app.services.billing_rules import ZERO, balance_due, net_paid_total, payments_total, refunds_total


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
    summary_payments_total = payments_total(payments)
    summary_refunds_total = refunds_total(payments)
    summary_paid_total = net_paid_total(payments)
    summary_balance_due = balance_due(invoice.total_amount, summary_paid_total)

    return InvoiceSummary(
        id=invoice.id,
        student_id=invoice.student_id,
        total_amount=invoice.total_amount,
        due_date=invoice.due_date,
        description=invoice.description,
        payments_total=summary_payments_total,
        refunds_total=summary_refunds_total,
        paid_total=summary_paid_total,
        balance_due=summary_balance_due,
        status=invoice.status,
    )


def _statement_totals(invoice_summaries: list[InvoiceSummary]) -> StatementTotals:
    return StatementTotals(
        invoiced_total=sum((item.total_amount for item in invoice_summaries), start=ZERO),
        payments_total=sum((item.payments_total for item in invoice_summaries), start=ZERO),
        refunds_total=sum((item.refunds_total for item in invoice_summaries), start=ZERO),
        paid_total=sum((item.paid_total for item in invoice_summaries), start=ZERO),
        balance_due_total=sum((item.balance_due for item in invoice_summaries), start=ZERO),
    )
