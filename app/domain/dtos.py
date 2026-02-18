from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SchoolDTO:
    id: UUID
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class StudentDTO:
    id: UUID
    school_id: UUID
    full_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class InvoiceDTO:
    id: UUID
    student_id: UUID
    total_amount: Decimal
    due_date: date
    issued_at: datetime
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PaymentDTO:
    id: UUID
    invoice_id: UUID
    amount: Decimal
    paid_at: datetime | None = None
    method: str | None = None
    reference: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
