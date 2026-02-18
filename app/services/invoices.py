from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from app.api.constants import INVOICES
from app.domain.dtos import InvoiceDTO
from app.domain.errors import NotFoundError
from app.services.ports import InvoiceRepo


def create_invoice(repo: InvoiceRepo, data: Mapping[str, object]) -> InvoiceDTO:
    return repo.create(data)


def list_invoices(repo: InvoiceRepo, *, offset: int, limit: int) -> list[InvoiceDTO]:
    return repo.list_all(offset=offset, limit=limit)


def list_invoices_by_student_id(repo: InvoiceRepo, *, student_id: UUID) -> list[InvoiceDTO]:
    return repo.list_by_student_id(student_id)


def list_invoices_by_student_ids(repo: InvoiceRepo, *, student_ids: Sequence[UUID]) -> list[InvoiceDTO]:
    return repo.list_by_student_ids(student_ids)


def get_invoice_by_id(repo: InvoiceRepo, invoice_id: UUID) -> InvoiceDTO:
    invoice = repo.get_by_id(invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


def update_invoice(repo: InvoiceRepo, invoice_id: UUID, data: Mapping[str, object]) -> InvoiceDTO:
    invoice = repo.update(invoice_id, data)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


def delete_invoice(repo: InvoiceRepo, invoice_id: UUID) -> bool:
    deleted = repo.delete(invoice_id)
    if not deleted:
        raise NotFoundError(INVOICES, str(invoice_id))
    return deleted
