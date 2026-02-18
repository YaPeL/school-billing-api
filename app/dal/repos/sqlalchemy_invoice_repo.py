from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import cast
from uuid import UUID

from sqlalchemy.orm import Session

from app.dal import invoice as invoice_dal
from app.dal.update_types import InvoiceCreate, InvoiceUpdate
from app.domain.dtos import InvoiceDTO
from app.models.invoice import Invoice


class SQLAlchemyInvoiceRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: Mapping[str, object]) -> InvoiceDTO:
        payload: InvoiceCreate = {
            "student_id": cast(UUID, data["student_id"]),
            "total_amount": cast(Decimal, data["total_amount"]),
            "due_date": cast(date, data["due_date"]),
        }
        if "description" in data:
            payload["description"] = cast(str | None, data["description"])
        if "issued_at" in data:
            payload["issued_at"] = cast(datetime | None, data["issued_at"])

        invoice = invoice_dal.create_invoice(self._session, data=payload)
        return _to_invoice_dto(invoice)

    def list_all(self, *, offset: int, limit: int) -> list[InvoiceDTO]:
        invoices = invoice_dal.list_invoices(self._session, offset=offset, limit=limit)
        return [_to_invoice_dto(invoice) for invoice in invoices]

    def list_by_student_id(self, student_id: UUID) -> list[InvoiceDTO]:
        invoices = invoice_dal.list_invoices_by_student_id(self._session, student_id=student_id)
        return [_to_invoice_dto(invoice) for invoice in invoices]

    def list_by_student_ids(self, student_ids: Sequence[UUID]) -> list[InvoiceDTO]:
        invoices = invoice_dal.list_invoices_by_student_ids(self._session, student_ids=student_ids)
        return [_to_invoice_dto(invoice) for invoice in invoices]

    def get_by_id(self, invoice_id: UUID) -> InvoiceDTO | None:
        invoice = invoice_dal.get_invoice_by_id(self._session, invoice_id=invoice_id)
        return None if invoice is None else _to_invoice_dto(invoice)

    def update(self, invoice_id: UUID, data: Mapping[str, object]) -> InvoiceDTO | None:
        payload: InvoiceUpdate = {}
        if "student_id" in data:
            payload["student_id"] = cast(UUID, data["student_id"])
        if "total_amount" in data:
            payload["total_amount"] = cast(Decimal, data["total_amount"])
        if "due_date" in data:
            payload["due_date"] = cast(date, data["due_date"])
        if "description" in data:
            payload["description"] = cast(str | None, data["description"])
        if "issued_at" in data:
            payload["issued_at"] = cast(datetime | None, data["issued_at"])

        invoice = invoice_dal.update_invoice(self._session, invoice_id=invoice_id, data=payload)
        return None if invoice is None else _to_invoice_dto(invoice)

    def delete(self, invoice_id: UUID) -> bool:
        return invoice_dal.delete_invoice(self._session, invoice_id=invoice_id)


def _to_invoice_dto(invoice: Invoice) -> InvoiceDTO:
    return InvoiceDTO(
        id=invoice.id,
        student_id=invoice.student_id,
        total_amount=invoice.total_amount,
        due_date=invoice.due_date,
        issued_at=invoice.issued_at,
        description=invoice.description,
        created_at=cast(datetime | None, getattr(invoice, "created_at", None)),
        updated_at=cast(datetime | None, getattr(invoice, "updated_at", None)),
    )
