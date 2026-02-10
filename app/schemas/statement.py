from datetime import date
from decimal import Decimal
from uuid import UUID

from app.domain.enums import InvoiceStatus
from app.schemas.base import SchemaModel


class StatementTotals(SchemaModel):
    invoiced_total: Decimal
    paid_total: Decimal
    balance_due_total: Decimal
    credit_total: Decimal


class InvoiceSummary(SchemaModel):
    id: UUID
    student_id: UUID
    total_amount: Decimal
    due_date: date
    description: str | None = None
    paid_total: Decimal
    balance_due: Decimal
    credit_amount: Decimal
    status: InvoiceStatus


class StudentStatement(SchemaModel):
    student_id: UUID
    school_id: UUID
    totals: StatementTotals
    invoices: list[InvoiceSummary]


class SchoolStatement(SchemaModel):
    school_id: UUID
    totals: StatementTotals
    students_count: int
    invoices: list[InvoiceSummary]
