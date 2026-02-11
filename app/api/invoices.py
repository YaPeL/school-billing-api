from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import require_admin
from app.dal._types import InvoiceCreate as DalInvoiceCreate
from app.dal._types import InvoiceUpdate as DalInvoiceUpdate
from app.db.session import get_db
from app.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate, PaymentRead
from app.schemas.auth import UserClaims
from app.services import invoices as invoice_service
from app.services import payments as payments_service

router = APIRouter(prefix="/invoices", tags=["invoices"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=InvoiceRead)
def create_invoice(invoice_in: InvoiceCreate, session: DbSession, _admin: AdminUser) -> InvoiceRead:
    payload = cast(DalInvoiceCreate, invoice_in.model_dump())
    invoice = invoice_service.create_invoice(session, data=payload)
    return InvoiceRead.model_validate(invoice)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[InvoiceRead]:
    invoices = invoice_service.list_invoices(session, offset=offset, limit=limit)
    return [InvoiceRead.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: UUID, session: DbSession) -> InvoiceRead:
    invoice = invoice_service.get_invoice_by_id(session, invoice_id=invoice_id)
    return InvoiceRead.model_validate(invoice)


@router.get("/{invoice_id}/payments", response_model=list[PaymentRead])
def list_invoice_payments(invoice_id: UUID, session: DbSession) -> list[PaymentRead]:
    invoice_service.get_invoice_by_id(session, invoice_id=invoice_id)
    payments = payments_service.list_payments_by_invoice_id(session, invoice_id=invoice_id)
    return [PaymentRead.model_validate(payment) for payment in payments]


@router.patch("/{invoice_id}", response_model=InvoiceRead)
def patch_invoice(invoice_id: UUID, invoice_in: InvoiceUpdate, session: DbSession, _admin: AdminUser) -> InvoiceRead:
    payload = cast(DalInvoiceUpdate, invoice_in.model_dump(exclude_unset=True))
    invoice = invoice_service.update_invoice(session, invoice_id=invoice_id, data=payload)
    return InvoiceRead.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: UUID, session: DbSession, _admin: AdminUser) -> Response:
    invoice_service.delete_invoice(session, invoice_id=invoice_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
