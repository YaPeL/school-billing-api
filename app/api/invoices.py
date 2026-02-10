from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, INVOICES, MAX_LIMIT
from app.api.exceptions import NotFoundError
from app.dal import invoice as invoice_dal
from app.dal._types import InvoiceCreate as DalInvoiceCreate
from app.dal._types import InvoiceUpdate as DalInvoiceUpdate
from app.db.session import get_db
from app.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate

router = APIRouter(prefix="/invoices", tags=["invoices"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=InvoiceRead)
def create_invoice(invoice_in: InvoiceCreate, session: DbSession) -> InvoiceRead:
    payload = cast(DalInvoiceCreate, invoice_in.model_dump())
    invoice = invoice_dal.create_invoice(session, data=payload)
    return InvoiceRead.model_validate(invoice)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[InvoiceRead]:
    invoices = invoice_dal.list_invoices(session, offset=offset, limit=limit)
    return [InvoiceRead.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: UUID, session: DbSession) -> InvoiceRead:
    invoice = invoice_dal.get_invoice_by_id(session, invoice_id=invoice_id)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return InvoiceRead.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceRead)
def patch_invoice(invoice_id: UUID, invoice_in: InvoiceUpdate, session: DbSession) -> InvoiceRead:
    payload = cast(DalInvoiceUpdate, invoice_in.model_dump(exclude_unset=True))
    invoice = invoice_dal.update_invoice(session, invoice_id=invoice_id, data=payload)
    if invoice is None:
        raise NotFoundError(INVOICES, str(invoice_id))
    return InvoiceRead.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: UUID, session: DbSession) -> Response:
    deleted = invoice_dal.delete_invoice(session, invoice_id=invoice_id)
    if not deleted:
        raise NotFoundError(INVOICES, str(invoice_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
