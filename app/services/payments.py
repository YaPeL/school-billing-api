from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from app.api.constants import PAYMENTS
from app.domain.dtos import PaymentDTO
from app.domain.errors import NotFoundError
from app.services.ports import PaymentRepo


def create_payment(repo: PaymentRepo, data: Mapping[str, object]) -> PaymentDTO:
    return repo.create(data)


def list_payments(repo: PaymentRepo, *, offset: int, limit: int) -> list[PaymentDTO]:
    return repo.list_all(offset=offset, limit=limit)


def list_payments_by_invoice_id(repo: PaymentRepo, invoice_id: UUID) -> list[PaymentDTO]:
    return repo.list_by_invoice_id(invoice_id)


def list_payments_by_invoice_ids(repo: PaymentRepo, invoice_ids: Sequence[UUID]) -> list[PaymentDTO]:
    return repo.list_by_invoice_ids(invoice_ids)


def get_payment_by_id(repo: PaymentRepo, payment_id: UUID) -> PaymentDTO:
    payment = repo.get_by_id(payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return payment


def update_payment(repo: PaymentRepo, payment_id: UUID, data: Mapping[str, object]) -> PaymentDTO:
    payment = repo.update(payment_id, data)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return payment


def delete_payment(repo: PaymentRepo, payment_id: UUID) -> bool:
    deleted = repo.delete(payment_id)
    if not deleted:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return deleted
