from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import get_payment_repo, require_admin
from app.schemas import PaymentCreate, PaymentRead, PaymentUpdate
from app.schemas.auth import UserClaims
from app.services import payments as payment_service
from app.services.ports import PaymentRepo

router = APIRouter(prefix="/payments", tags=["payments"])

PaymentRepoDep = Annotated[PaymentRepo, Depends(get_payment_repo)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=PaymentRead)
def create_payment(payment_in: PaymentCreate, repo: PaymentRepoDep, _admin: AdminUser) -> PaymentRead:
    payment = payment_service.create_payment(repo, data=payment_in.model_dump())
    return PaymentRead.model_validate(payment)


@router.get("", response_model=list[PaymentRead])
def list_payments(
    repo: PaymentRepoDep,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[PaymentRead]:
    payments = payment_service.list_payments(repo, offset=offset, limit=limit)
    return [PaymentRead.model_validate(payment) for payment in payments]


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: UUID, repo: PaymentRepoDep) -> PaymentRead:
    payment = payment_service.get_payment_by_id(repo, payment_id=payment_id)
    return PaymentRead.model_validate(payment)


@router.patch("/{payment_id}", response_model=PaymentRead)
def patch_payment(payment_id: UUID, payment_in: PaymentUpdate, repo: PaymentRepoDep, _admin: AdminUser) -> PaymentRead:
    payment = payment_service.update_payment(
        repo, payment_id=payment_id, data=payment_in.model_dump(exclude_unset=True)
    )
    return PaymentRead.model_validate(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: UUID, repo: PaymentRepoDep, _admin: AdminUser) -> Response:
    payment_service.delete_payment(repo, payment_id=payment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
