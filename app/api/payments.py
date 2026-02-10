from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT, PAYMENTS
from app.api.deps import require_admin
from app.api.exceptions import NotFoundError
from app.dal import payment as payment_dal
from app.dal._types import PaymentCreate as DalPaymentCreate
from app.dal._types import PaymentUpdate as DalPaymentUpdate
from app.db.session import get_db
from app.schemas import PaymentCreate, PaymentRead, PaymentUpdate
from app.schemas.auth import UserClaims

router = APIRouter(prefix="/payments", tags=["payments"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=PaymentRead)
async def create_payment(payment_in: PaymentCreate, session: DbSession, _admin: AdminUser) -> PaymentRead:
    payload = cast(DalPaymentCreate, payment_in.model_dump())
    payment = payment_dal.create_payment(session, data=payload)
    return PaymentRead.model_validate(payment)


@router.get("", response_model=list[PaymentRead])
async def list_payments(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[PaymentRead]:
    payments = payment_dal.list_payments(session, offset=offset, limit=limit)
    return [PaymentRead.model_validate(payment) for payment in payments]


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(payment_id: UUID, session: DbSession) -> PaymentRead:
    payment = payment_dal.get_payment_by_id(session, payment_id=payment_id)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return PaymentRead.model_validate(payment)


@router.patch("/{payment_id}", response_model=PaymentRead)
async def patch_payment(
    payment_id: UUID, payment_in: PaymentUpdate, session: DbSession, _admin: AdminUser
) -> PaymentRead:
    payload = cast(DalPaymentUpdate, payment_in.model_dump(exclude_unset=True))
    payment = payment_dal.update_payment(session, payment_id=payment_id, data=payload)
    if payment is None:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return PaymentRead.model_validate(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: UUID, session: DbSession, _admin: AdminUser) -> Response:
    deleted = payment_dal.delete_payment(session, payment_id=payment_id)
    if not deleted:
        raise NotFoundError(PAYMENTS, str(payment_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
