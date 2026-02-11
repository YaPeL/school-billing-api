from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import NotRequired, TypedDict


class SchoolCreate(TypedDict):
    name: str


class SchoolUpdate(TypedDict, total=False):
    name: str


class StudentCreate(TypedDict):
    school_id: uuid.UUID
    full_name: str


class StudentUpdate(TypedDict, total=False):
    school_id: uuid.UUID
    full_name: str


class InvoiceCreate(TypedDict):
    student_id: uuid.UUID
    total_amount: Decimal
    due_date: date
    description: NotRequired[str | None]
    issued_at: NotRequired[datetime | None]


class InvoiceUpdate(TypedDict, total=False):
    student_id: uuid.UUID
    total_amount: Decimal
    due_date: date
    description: str | None
    issued_at: datetime | None


class PaymentCreate(TypedDict):
    invoice_id: uuid.UUID
    amount: Decimal
    method: NotRequired[str | None]
    reference: NotRequired[str | None]
    paid_at: NotRequired[datetime | None]


class PaymentUpdate(TypedDict, total=False):
    invoice_id: uuid.UUID
    amount: Decimal
    method: str | None
    reference: str | None
    paid_at: datetime | None
