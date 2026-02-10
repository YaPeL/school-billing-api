from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.base import ReadSchemaModel, SchemaModel
from app.schemas.types import PositiveAmount


class InvoiceCreate(SchemaModel):
    student_id: UUID
    total_amount: PositiveAmount
    due_date: date


class InvoiceUpdate(SchemaModel):
    student_id: UUID | None = None
    total_amount: PositiveAmount | None = None
    due_date: date | None = None
    description: str | None = None
    issued_at: datetime | None = None


class InvoiceRead(ReadSchemaModel):
    id: UUID
    student_id: UUID
    total_amount: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None
    issued_at: datetime
    due_date: date
    description: str | None = None
