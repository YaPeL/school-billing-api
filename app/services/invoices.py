from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import TypedDict, cast
from uuid import UUID

from app.api.constants import INVOICES
from app.domain.dtos import InvoiceDTO, PaymentDTO
from app.domain.enums import InvoiceStatus
from app.domain.errors import NotFoundError
from app.services.billing_rules import (
    balance_due,
    derive_invoice_status,
    net_paid_total,
    payments_total,
    refunds_total,
    validate_net_paid_bounds,
)
from app.services.ports import InvoiceRepo, PaymentRepo


class InvoiceComputed(TypedDict):
    id: UUID
    student_id: UUID
    total_amount: Decimal
    status: InvoiceStatus
    created_at: datetime | None
    updated_at: datetime | None
    issued_at: datetime
    due_date: date
    description: str | None
    payments_total: Decimal
    refunds_total: Decimal
    paid_total: Decimal
    balance_due: Decimal


async def create_invoice(repo: InvoiceRepo, data: Mapping[str, object]) -> InvoiceDTO:
    payload = dict(data)
    payload.setdefault("status", InvoiceStatus.PENDING)
    return await repo.create(payload)


async def list_invoices(repo: InvoiceRepo, *, offset: int, limit: int) -> list[InvoiceDTO]:
    return await repo.list_all(offset=offset, limit=limit)


async def list_invoices_by_student_id(repo: InvoiceRepo, *, student_id: UUID) -> list[InvoiceDTO]:
    return await repo.list_by_student_id(student_id)


async def list_invoices_by_student_ids(repo: InvoiceRepo, *, student_ids: Sequence[UUID]) -> list[InvoiceDTO]:
    return await repo.list_by_student_ids(student_ids)


async def get_invoice_by_id(repo: InvoiceRepo, invoice_id: UUID) -> InvoiceDTO:
    invoice = await repo.get_by_id(invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


async def list_invoices_with_totals(
    invoice_repo: InvoiceRepo,
    payment_repo: PaymentRepo,
    *,
    offset: int,
    limit: int,
) -> list[InvoiceComputed]:
    invoices = await list_invoices(invoice_repo, offset=offset, limit=limit)
    if not invoices:
        return []

    invoice_ids = [invoice.id for invoice in invoices]
    payments = await payment_repo.list_by_invoice_ids(invoice_ids)
    payments_by_invoice: dict[UUID, list[PaymentDTO]] = {invoice_id: [] for invoice_id in invoice_ids}
    for payment in payments:
        payments_by_invoice.setdefault(payment.invoice_id, []).append(payment)

    return [serialize_invoice_with_totals(invoice, payments_by_invoice[invoice.id]) for invoice in invoices]


async def get_invoice_with_totals(
    invoice_repo: InvoiceRepo,
    payment_repo: PaymentRepo,
    invoice_id: UUID,
) -> InvoiceComputed:
    invoice = await get_invoice_by_id(invoice_repo, invoice_id=invoice_id)
    payments = await payment_repo.list_by_invoice_id(invoice.id)
    return serialize_invoice_with_totals(invoice, payments)


async def update_invoice(
    invoice_repo: InvoiceRepo,
    payment_repo: PaymentRepo,
    invoice_id: UUID,
    data: Mapping[str, object],
) -> InvoiceDTO:
    invoice = await invoice_repo.get_by_id(invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))

    next_total_amount = cast(Decimal, data.get("total_amount", invoice.total_amount))
    payments = await payment_repo.list_by_invoice_id(invoice_id)
    net_paid = net_paid_total(payments)
    validate_net_paid_bounds(next_total_amount, net_paid)

    payload = dict(data)
    payload["status"] = derive_invoice_status(next_total_amount, net_paid)

    updated = await invoice_repo.update(invoice_id, payload)
    if updated is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return updated


async def delete_invoice(repo: InvoiceRepo, invoice_id: UUID) -> bool:
    deleted = await repo.delete(invoice_id)
    if not deleted:
        raise NotFoundError(INVOICES, str(invoice_id))
    return deleted


def serialize_invoice_with_totals(invoice: InvoiceDTO, payments: Sequence[PaymentDTO]) -> InvoiceComputed:
    invoice_payments_total = payments_total(payments)
    invoice_refunds_total = refunds_total(payments)
    net_paid = invoice_payments_total - invoice_refunds_total
    return {
        "id": invoice.id,
        "student_id": invoice.student_id,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "created_at": invoice.created_at,
        "updated_at": invoice.updated_at,
        "issued_at": invoice.issued_at,
        "due_date": invoice.due_date,
        "description": invoice.description,
        "payments_total": invoice_payments_total,
        "refunds_total": invoice_refunds_total,
        "paid_total": net_paid,
        "balance_due": balance_due(invoice.total_amount, net_paid),
    }
