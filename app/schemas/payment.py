from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import model_validator

from app.domain.enums import PaymentKind
from app.schemas.base import ReadSchemaModel, SchemaModel
from app.schemas.types import PositiveAmount


class PaymentCreate(SchemaModel):
    invoice_id: UUID
    amount: PositiveAmount
    kind: PaymentKind = PaymentKind.PAYMENT


class PaymentUpdate(SchemaModel):
    invoice_id: UUID | None = None
    amount: PositiveAmount | None = None
    kind: PaymentKind | None = None
    paid_at: datetime | None = None
    method: str | None = None
    reference: str | None = None

    @model_validator(mode="after")
    def validate_kind_not_null_when_provided(self) -> "PaymentUpdate":
        if "kind" in self.model_fields_set and self.kind is None:
            raise ValueError("kind may be omitted but cannot be null")
        return self


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
