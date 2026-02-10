from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.base import ReadSchemaModel, SchemaModel
from app.schemas.types import PositiveAmount


class PaymentCreate(SchemaModel):
    invoice_id: UUID
    amount: PositiveAmount


class PaymentUpdate(SchemaModel):
    invoice_id: UUID | None = None
    amount: PositiveAmount | None = None
    paid_at: datetime | None = None
    method: str | None = None
    reference: str | None = None


class PaymentRead(ReadSchemaModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None
    paid_at: datetime | None = None
    method: str | None = None
    reference: str | None = None
