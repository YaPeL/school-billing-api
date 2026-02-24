from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import cast
from uuid import UUID

from app.api.constants import INVOICES
from app.domain.dtos import InvoiceDTO
from app.domain.enums import InvoiceStatus
from app.domain.errors import NotFoundError
from app.services.billing_rules import derive_invoice_status, net_paid_total, validate_net_paid_bounds
from app.services.ports import InvoiceRepo, PaymentRepo


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
