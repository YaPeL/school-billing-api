from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import get_invoice_repo, get_list_invoice_payments_uc, require_admin
from app.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate, PaymentRead
from app.schemas.auth import UserClaims
from app.services import invoices as invoice_service
from app.services.ports import InvoiceRepo
from app.services.use_cases import ListInvoicePayments

router = APIRouter(prefix="/invoices", tags=["invoices"])

InvoiceRepoDep = Annotated[InvoiceRepo, Depends(get_invoice_repo)]
ListInvoicePaymentsUCDep = Annotated[ListInvoicePayments, Depends(get_list_invoice_payments_uc)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=InvoiceRead)
def create_invoice(invoice_in: InvoiceCreate, repo: InvoiceRepoDep, _admin: AdminUser) -> InvoiceRead:
    invoice = invoice_service.create_invoice(repo, data=invoice_in.model_dump())
    return InvoiceRead.model_validate(invoice)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    repo: InvoiceRepoDep,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[InvoiceRead]:
    invoices = invoice_service.list_invoices(repo, offset=offset, limit=limit)
    return [InvoiceRead.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: UUID, repo: InvoiceRepoDep) -> InvoiceRead:
    invoice = invoice_service.get_invoice_by_id(repo, invoice_id=invoice_id)
    return InvoiceRead.model_validate(invoice)


@router.get("/{invoice_id}/payments", response_model=list[PaymentRead])
def list_invoice_payments(invoice_id: UUID, use_case: ListInvoicePaymentsUCDep) -> list[PaymentRead]:
    payments = use_case(invoice_id)
    return [PaymentRead.model_validate(payment) for payment in payments]


@router.patch("/{invoice_id}", response_model=InvoiceRead)
def patch_invoice(invoice_id: UUID, invoice_in: InvoiceUpdate, repo: InvoiceRepoDep, _admin: AdminUser) -> InvoiceRead:
    invoice = invoice_service.update_invoice(
        repo, invoice_id=invoice_id, data=invoice_in.model_dump(exclude_unset=True)
    )
    return InvoiceRead.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: UUID, repo: InvoiceRepoDep, _admin: AdminUser) -> Response:
    invoice_service.delete_invoice(repo, invoice_id=invoice_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
