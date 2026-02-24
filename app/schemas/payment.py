from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import field_validator

from app.domain.enums import PaymentKind
from app.schemas.base import ReadSchemaModel, SchemaModel
from app.schemas.types import PositiveAmount


class PaymentCreate(SchemaModel):
    invoice_id: UUID
    amount: PositiveAmount
    kind: PaymentKind = PaymentKind.PAYMENT
    reference: str | None = None
    method: str | None = None


class PaymentUpdate(SchemaModel):
    invoice_id: UUID | None = None
    amount: PositiveAmount | None = None
    kind: PaymentKind | None = None
    paid_at: datetime | None = None
    method: str | None = None
    reference: str | None = None

    @field_validator("invoice_id", "amount", "kind", mode="before")
    @classmethod
    def reject_null_values(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null")
        return value


class PaymentRead(ReadSchemaModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    kind: PaymentKind
    created_at: datetime | None = None
    updated_at: datetime | None = None
    paid_at: datetime | None = None
    method: str | None = None
    reference: str | None = None
