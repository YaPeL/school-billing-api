from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.constants import PAYMENTS
from app.api.exceptions import NotFoundError
from app.dal import payment as payment_dal
from app.dal._types import PaymentCreate, PaymentUpdate
from app.models.payment import Payment


def create_payment(session: Session, data: PaymentCreate) -> Payment:
    return payment_dal.create_payment(session, data=data)


def list_payments(session: Session, *, offset: int, limit: int) -> list[Payment]:
    return payment_dal.list_payments(session, offset=offset, limit=limit)


def list_payments_by_invoice_id(session: Session, invoice_id: UUID) -> list[Payment]:
    return payment_dal.list_payments_by_invoice_id(session, invoice_id=invoice_id)


def get_payment_by_id(session: Session, payment_id: UUID) -> Payment:
    payment = payment_dal.get_payment_by_id(session, payment_id=payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return payment


def update_payment(session: Session, payment_id: UUID, data: PaymentUpdate) -> Payment:
    payment = payment_dal.update_payment(session, payment_id=payment_id, data=data)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return payment


def delete_payment(session: Session, payment_id: UUID) -> bool:
    deleted = payment_dal.delete_payment(session, payment_id=payment_id)
    if not deleted:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return deleted
