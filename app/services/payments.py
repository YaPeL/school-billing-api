from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from uuid import UUID

from app.api.constants import INVOICES, PAYMENTS
from app.domain.dtos import InvoiceDTO, PaymentDTO
from app.domain.enums import InvoiceStatus, PaymentKind
from app.domain.errors import ConflictError, DomainValidationError, NotFoundError
from app.services.billing_rules import invoice_status, paid_total
from app.services.ports import InvoiceRepo, PaymentRepo

_MISSING_KIND = object()


async def create_payment(
    payment_repo: PaymentRepo, invoice_repo: InvoiceRepo, data: Mapping[str, object]
) -> PaymentDTO:
    return await create_invoice_movement(payment_repo, invoice_repo, data)


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
    payment_repo: PaymentRepo, invoice_repo: InvoiceRepo, payment_id: UUID, data: Mapping[str, object]
) -> PaymentDTO:
    return await update_invoice_movement(payment_repo, invoice_repo, payment_id, data)


async def delete_payment(payment_repo: PaymentRepo, invoice_repo: InvoiceRepo, payment_id: UUID) -> bool:
    return await delete_invoice_movement(payment_repo, invoice_repo, payment_id)


def _movement_delta(amount: Decimal, kind: PaymentKind) -> Decimal:
    return amount if kind == PaymentKind.PAYMENT else -amount


def _status_for(invoice_total: Decimal, net_paid: Decimal) -> InvoiceStatus:
    return invoice_status(invoice_total, net_paid)


def _validate_net_paid(invoice_total: Decimal, net_paid: Decimal) -> None:
    if net_paid < Decimal("0.00"):
        raise ConflictError("Refund exceeds paid amount for invoice")
    if net_paid > invoice_total:
        raise ConflictError("Payment exceeds invoice total amount")


def _resolve_payment_kind(data: Mapping[str, object], *, fallback: PaymentKind) -> PaymentKind:
    raw_kind = data.get("kind", _MISSING_KIND)
    if raw_kind is _MISSING_KIND:
        return fallback
    if raw_kind is None:
        raise DomainValidationError("kind may be omitted but cannot be null")
    if isinstance(raw_kind, PaymentKind):
        return raw_kind
    try:
        return PaymentKind(str(raw_kind))
    except ValueError as exc:
        raise DomainValidationError("kind must be PAYMENT or REFUND") from exc


async def _require_invoice(invoice_repo: InvoiceRepo, invoice_id: UUID) -> InvoiceDTO:
    invoice = await invoice_repo.get_by_id(invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


async def _sync_invoice_status(invoice_repo: InvoiceRepo, invoice_id: UUID, status: InvoiceStatus) -> None:
    await invoice_repo.update(invoice_id, {"status": status})


async def create_invoice_movement(
    payment_repo: PaymentRepo,
    invoice_repo: InvoiceRepo,
    data: Mapping[str, object],
) -> PaymentDTO:
    invoice_id = UUID(str(data["invoice_id"]))
    amount = Decimal(str(data["amount"]))
    kind = _resolve_payment_kind(data, fallback=PaymentKind.PAYMENT)

    invoice = await _require_invoice(invoice_repo, invoice_id)
    existing_movements = await payment_repo.list_by_invoice_id(invoice_id)
    projected_net = paid_total(existing_movements) + _movement_delta(amount, kind)
    _validate_net_paid(invoice.total_amount, projected_net)

    payment = await payment_repo.create({**data, "kind": kind})
    await _sync_invoice_status(invoice_repo, invoice.id, _status_for(invoice.total_amount, projected_net))
    return payment


async def update_invoice_movement(
    payment_repo: PaymentRepo,
    invoice_repo: InvoiceRepo,
    payment_id: UUID,
    data: Mapping[str, object],
) -> PaymentDTO:
    current_payment = await payment_repo.get_by_id(payment_id)
    if current_payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))

    new_invoice_id = UUID(str(data.get("invoice_id", current_payment.invoice_id)))
    new_amount = Decimal(str(data.get("amount", current_payment.amount)))
    new_kind = _resolve_payment_kind(data, fallback=current_payment.kind)

    old_invoice = await _require_invoice(invoice_repo, current_payment.invoice_id)
    old_movements = await payment_repo.list_by_invoice_id(current_payment.invoice_id)

    current_delta = _movement_delta(current_payment.amount, current_payment.kind)
    old_projected_net = paid_total(old_movements) - current_delta
    if new_invoice_id == current_payment.invoice_id:
        old_projected_net += _movement_delta(new_amount, new_kind)
    _validate_net_paid(old_invoice.total_amount, old_projected_net)

    new_invoice = old_invoice
    new_projected_net = old_projected_net
    if new_invoice_id != current_payment.invoice_id:
        new_invoice = await _require_invoice(invoice_repo, new_invoice_id)
        new_movements = await payment_repo.list_by_invoice_id(new_invoice_id)
        new_projected_net = paid_total(new_movements) + _movement_delta(new_amount, new_kind)
        _validate_net_paid(new_invoice.total_amount, new_projected_net)

    updated = await payment_repo.update(payment_id, {**data, "kind": new_kind})
    if updated is None:
        raise NotFoundError(PAYMENTS, str(payment_id))

    await _sync_invoice_status(invoice_repo, old_invoice.id, _status_for(old_invoice.total_amount, old_projected_net))
    if new_invoice.id != old_invoice.id:
        await _sync_invoice_status(
            invoice_repo, new_invoice.id, _status_for(new_invoice.total_amount, new_projected_net)
        )
    return updated


async def delete_invoice_movement(payment_repo: PaymentRepo, invoice_repo: InvoiceRepo, payment_id: UUID) -> bool:
    payment = await payment_repo.get_by_id(payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))

    invoice = await _require_invoice(invoice_repo, payment.invoice_id)
    movements = await payment_repo.list_by_invoice_id(invoice.id)
    projected_net = paid_total(movements) - _movement_delta(payment.amount, payment.kind)
    _validate_net_paid(invoice.total_amount, projected_net)

    deleted = await payment_repo.delete(payment_id)
    if not deleted:
        raise NotFoundError(PAYMENTS, str(payment_id))
    await _sync_invoice_status(invoice_repo, invoice.id, _status_for(invoice.total_amount, projected_net))
    return deleted
