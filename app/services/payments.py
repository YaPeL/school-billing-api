from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast
from uuid import UUID

from app.api.constants import INVOICES, PAYMENTS
from app.domain.dtos import InvoiceDTO, PaymentDTO
from app.domain.enums import PaymentKind
from app.domain.errors import ConflictError, NotFoundError
from app.services.billing_rules import (
    derive_invoice_status,
    movement_delta,
    net_paid_total,
    validate_net_paid_bounds,
)
from app.services.ports import InvoiceRepo, PaymentRepo


async def create_payment(
    payment_repo: PaymentRepo, invoice_repo: InvoiceRepo, data: Mapping[str, object]
) -> PaymentDTO:
    invoice_id = cast(UUID, data["invoice_id"])
    invoice = await _get_invoice_or_raise(invoice_repo, invoice_id)

    payments = await payment_repo.list_by_invoice_id(invoice.id)
    candidate_kind = cast(PaymentKind, data.get("kind", PaymentKind.PAYMENT))
    candidate_amount = cast(Decimal, data["amount"])
    _validate_movement_payload(kind=candidate_kind, amount=candidate_amount)
    next_net_paid = net_paid_total(payments) + movement_delta(candidate_kind, candidate_amount)
    validate_net_paid_bounds(invoice.total_amount, next_net_paid)

    created = await payment_repo.create(data)
    await _persist_invoice_status(invoice_repo, invoice, next_net_paid)
    return created


async def list_payments(repo: PaymentRepo, *, offset: int, limit: int) -> list[PaymentDTO]:
    return await repo.list_all(offset=offset, limit=limit)


async def list_payments_by_invoice_id(repo: PaymentRepo, invoice_id: UUID) -> list[PaymentDTO]:
    return await repo.list_by_invoice_id(invoice_id)


async def list_payments_by_invoice_ids(repo: PaymentRepo, invoice_ids: Sequence[UUID]) -> list[PaymentDTO]:
    return await repo.list_by_invoice_ids(invoice_ids)


async def get_payment_by_id(repo: PaymentRepo, payment_id: UUID) -> PaymentDTO:
    payment = await repo.get_by_id(payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return payment


async def update_payment(
    payment_repo: PaymentRepo,
    invoice_repo: InvoiceRepo,
    payment_id: UUID,
    data: Mapping[str, object],
) -> PaymentDTO:
    payment = await payment_repo.get_by_id(payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))

    target_invoice_id = cast(UUID, data.get("invoice_id", payment.invoice_id))
    updated_kind = cast(PaymentKind, data.get("kind", payment.kind))
    updated_amount = cast(Decimal, data.get("amount", payment.amount))
    _validate_movement_payload(kind=updated_kind, amount=updated_amount)
    updated_delta = movement_delta(updated_kind, updated_amount)
    old_delta = movement_delta(payment.kind, payment.amount)

    if target_invoice_id == payment.invoice_id:
        invoice = await _get_invoice_or_raise(invoice_repo, payment.invoice_id)
        payments = await payment_repo.list_by_invoice_id(invoice.id)
        current_net_paid = net_paid_total(payments)
        next_net_paid = current_net_paid - old_delta + updated_delta
        validate_net_paid_bounds(invoice.total_amount, next_net_paid)

        updated = await payment_repo.update(payment_id, data)
        if updated is None:
            raise NotFoundError(PAYMENTS, str(payment_id))
        await _persist_invoice_status(invoice_repo, invoice, next_net_paid)
        return updated

    source_invoice = await _get_invoice_or_raise(invoice_repo, payment.invoice_id)
    target_invoice = await _get_invoice_or_raise(invoice_repo, target_invoice_id)

    source_payments = await payment_repo.list_by_invoice_id(source_invoice.id)
    source_next_net_paid = net_paid_total(source_payments) - old_delta
    validate_net_paid_bounds(source_invoice.total_amount, source_next_net_paid)

    target_payments = await payment_repo.list_by_invoice_id(target_invoice.id)
    target_next_net_paid = net_paid_total(target_payments) + updated_delta
    validate_net_paid_bounds(target_invoice.total_amount, target_next_net_paid)

    updated = await payment_repo.update(payment_id, data)
    if updated is None:
        raise NotFoundError(PAYMENTS, str(payment_id))

    await _persist_invoice_status(invoice_repo, source_invoice, source_next_net_paid)
    await _persist_invoice_status(invoice_repo, target_invoice, target_next_net_paid)
    return updated


async def delete_payment(payment_repo: PaymentRepo, invoice_repo: InvoiceRepo, payment_id: UUID) -> bool:
    payment = await payment_repo.get_by_id(payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))

    invoice = await _get_invoice_or_raise(invoice_repo, payment.invoice_id)
    payments = await payment_repo.list_by_invoice_id(invoice.id)
    current_net_paid = net_paid_total(payments)
    next_net_paid = current_net_paid - movement_delta(payment.kind, payment.amount)
    validate_net_paid_bounds(invoice.total_amount, next_net_paid)

    deleted = await payment_repo.delete(payment_id)
    if not deleted:
        raise NotFoundError(PAYMENTS, str(payment_id))

    await _persist_invoice_status(invoice_repo, invoice, next_net_paid)
    return deleted


async def _persist_invoice_status(invoice_repo: InvoiceRepo, invoice: InvoiceDTO, next_net_paid: Decimal) -> None:
    next_status = derive_invoice_status(invoice.total_amount, next_net_paid)
    if next_status == invoice.status:
        return
    await invoice_repo.update(invoice.id, {"status": next_status})


async def _get_invoice_or_raise(invoice_repo: InvoiceRepo, invoice_id: UUID) -> InvoiceDTO:
    invoice = await invoice_repo.get_by_id(invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


def _validate_movement_payload(*, kind: PaymentKind | None, amount: Decimal | None) -> None:
    if kind is None:
        raise ConflictError("payment movement kind cannot be null")
    if amount is None or amount <= Decimal("0"):
        raise ConflictError("movement amount must be greater than zero")
