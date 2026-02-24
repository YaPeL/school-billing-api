from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from app.api.constants import INVOICES
from app.domain.dtos import InvoiceDTO
from app.domain.errors import NotFoundError
from app.services.ports import InvoiceRepo


async def create_invoice(repo: InvoiceRepo, data: Mapping[str, object]) -> InvoiceDTO:
    return await repo.create(data)


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


async def update_invoice(repo: InvoiceRepo, invoice_id: UUID, data: Mapping[str, object]) -> InvoiceDTO:
    invoice = await repo.update(invoice_id, data)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


async def delete_invoice(repo: InvoiceRepo, invoice_id: UUID) -> bool:
    deleted = await repo.delete(invoice_id)
    if not deleted:
        raise NotFoundError(INVOICES, str(invoice_id))
    return deleted
