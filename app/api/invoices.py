from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import get_invoice_repo, get_list_invoice_payments_uc, get_payment_repo, require_admin
from app.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate, PaymentRead
from app.schemas.auth import UserClaims
from app.services import invoices as invoice_service
from app.services.ports import InvoiceRepo, PaymentRepo
from app.services.use_cases import ListInvoicePayments

router = APIRouter(prefix="/invoices", tags=["invoices"])

InvoiceRepoDep = Annotated[InvoiceRepo, Depends(get_invoice_repo)]
ListInvoicePaymentsUCDep = Annotated[ListInvoicePayments, Depends(get_list_invoice_payments_uc)]
PaymentRepoDep = Annotated[PaymentRepo, Depends(get_payment_repo)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=InvoiceRead)
async def create_invoice(invoice_in: InvoiceCreate, invoice_repo: InvoiceRepoDep, _admin: AdminUser) -> InvoiceRead:
    invoice = await invoice_service.create_invoice(invoice_repo, data=invoice_in.model_dump())
    return InvoiceRead.model_validate(invoice_service.serialize_invoice_with_totals(invoice, []))


@router.get("", response_model=list[InvoiceRead])
async def list_invoices(
    invoice_repo: InvoiceRepoDep,
    payment_repo: PaymentRepoDep,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[InvoiceRead]:
    invoices = await invoice_service.list_invoices_with_totals(
        invoice_repo,
        payment_repo,
        offset=offset,
        limit=limit,
    )
    return [InvoiceRead.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(invoice_id: UUID, invoice_repo: InvoiceRepoDep, payment_repo: PaymentRepoDep) -> InvoiceRead:
    invoice = await invoice_service.get_invoice_with_totals(
        invoice_repo,
        payment_repo,
        invoice_id=invoice_id,
    )
    return InvoiceRead.model_validate(invoice)


@router.get("/{invoice_id}/payments", response_model=list[PaymentRead])
async def list_invoice_payments(invoice_id: UUID, use_case: ListInvoicePaymentsUCDep) -> list[PaymentRead]:
    payments = await use_case(invoice_id)
    return [PaymentRead.model_validate(payment) for payment in payments]


@router.patch("/{invoice_id}", response_model=InvoiceRead)
async def patch_invoice(
    invoice_id: UUID,
    invoice_in: InvoiceUpdate,
    invoice_repo: InvoiceRepoDep,
    payment_repo: PaymentRepoDep,
    _admin: AdminUser,
) -> InvoiceRead:
    invoice = await invoice_service.update_invoice(
        invoice_repo,
        payment_repo,
        invoice_id=invoice_id,
        data=invoice_in.model_dump(exclude_unset=True),
    )
    payments = await payment_repo.list_by_invoice_id(invoice.id)
    return InvoiceRead.model_validate(invoice_service.serialize_invoice_with_totals(invoice, payments))


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: UUID, repo: InvoiceRepoDep, _admin: AdminUser) -> Response:
    await invoice_service.delete_invoice(repo, invoice_id=invoice_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
