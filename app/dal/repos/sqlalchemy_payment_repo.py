from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import cast
from uuid import UUID

from sqlalchemy.orm import Session

from app.dal import payment as payment_dal
from app.dal.update_types import PaymentCreate, PaymentUpdate
from app.domain.dtos import PaymentDTO
from app.models.payment import Payment


class SQLAlchemyPaymentRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: Mapping[str, object]) -> PaymentDTO:
        payload: PaymentCreate = {
            "invoice_id": cast(UUID, data["invoice_id"]),
            "amount": cast(Decimal, data["amount"]),
        }
        if "method" in data:
            payload["method"] = cast(str | None, data["method"])
        if "reference" in data:
            payload["reference"] = cast(str | None, data["reference"])
        if "paid_at" in data:
            payload["paid_at"] = cast(datetime | None, data["paid_at"])

        payment = payment_dal.create_payment(self._session, data=payload)
        return _to_payment_dto(payment)

    def list_all(self, *, offset: int, limit: int) -> list[PaymentDTO]:
        payments = payment_dal.list_payments(self._session, offset=offset, limit=limit)
        return [_to_payment_dto(payment) for payment in payments]

    def list_by_invoice_id(self, invoice_id: UUID) -> list[PaymentDTO]:
        payments = payment_dal.list_payments_by_invoice_id(self._session, invoice_id=invoice_id)
        return [_to_payment_dto(payment) for payment in payments]

    def list_by_invoice_ids(self, invoice_ids: Sequence[UUID]) -> list[PaymentDTO]:
        payments = payment_dal.list_payments_by_invoice_ids(self._session, invoice_ids=invoice_ids)
        return [_to_payment_dto(payment) for payment in payments]

    def get_by_id(self, payment_id: UUID) -> PaymentDTO | None:
        payment = payment_dal.get_payment_by_id(self._session, payment_id=payment_id)
        return None if payment is None else _to_payment_dto(payment)

    def update(self, payment_id: UUID, data: Mapping[str, object]) -> PaymentDTO | None:
        payload: PaymentUpdate = {}
        if "invoice_id" in data:
            payload["invoice_id"] = cast(UUID, data["invoice_id"])
        if "amount" in data:
            payload["amount"] = cast(Decimal, data["amount"])
        if "paid_at" in data:
            payload["paid_at"] = cast(datetime | None, data["paid_at"])
        if "method" in data:
            payload["method"] = cast(str | None, data["method"])
        if "reference" in data:
            payload["reference"] = cast(str | None, data["reference"])

        payment = payment_dal.update_payment(self._session, payment_id=payment_id, data=payload)
        return None if payment is None else _to_payment_dto(payment)

    def delete(self, payment_id: UUID) -> bool:
        return payment_dal.delete_payment(self._session, payment_id=payment_id)


def _to_payment_dto(payment: Payment) -> PaymentDTO:
    return PaymentDTO(
        id=payment.id,
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        paid_at=payment.paid_at,
        method=payment.method,
        reference=payment.reference,
        created_at=cast(datetime | None, getattr(payment, "created_at", None)),
        updated_at=cast(datetime | None, getattr(payment, "updated_at", None)),
    )
