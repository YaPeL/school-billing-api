from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.constants import INVOICES
from app.api.exceptions import NotFoundError
from app.dal import invoice as invoice_dal
from app.dal._types import InvoiceCreate, InvoiceUpdate
from app.models.invoice import Invoice


def create_invoice(session: Session, data: InvoiceCreate) -> Invoice:
    return invoice_dal.create_invoice(session, data=data)


def list_invoices(session: Session, *, offset: int, limit: int) -> list[Invoice]:
    return invoice_dal.list_invoices(session, offset=offset, limit=limit)


def get_invoice_by_id(session: Session, invoice_id: UUID) -> Invoice:
    invoice = invoice_dal.get_invoice_by_id(session, invoice_id=invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


def update_invoice(session: Session, invoice_id: UUID, data: InvoiceUpdate) -> Invoice:
    invoice = invoice_dal.update_invoice(session, invoice_id=invoice_id, data=data)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return invoice


def delete_invoice(session: Session, invoice_id: UUID) -> bool:
    deleted = invoice_dal.delete_invoice(session, invoice_id=invoice_id)
    if not deleted:
        raise NotFoundError(INVOICES, str(invoice_id))
    return deleted
