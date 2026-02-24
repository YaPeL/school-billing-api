import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.update_types import PaymentCreate, PaymentUpdate
from app.domain.enums import PaymentKind
from app.models.payment import Payment


async def create_payment(session: AsyncSession, data: PaymentCreate) -> Payment:
    payment = Payment(
        invoice_id=data["invoice_id"],
        amount=data["amount"],
        method=data.get("method"),
        reference=data.get("reference"),
    )
    kind = data.get("kind")
    payment.kind = kind if kind is not None else PaymentKind.PAYMENT
    paid_at = data.get("paid_at")
    if paid_at is not None:
        payment.paid_at = paid_at

    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment_by_id(session: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
    return await session.get(Payment, payment_id)


async def list_payments(session: AsyncSession, *, offset: int = 0, limit: int = 100) -> list[Payment]:
    stmt = select(Payment).offset(offset).limit(limit)
    result = await session.scalars(stmt)
    return list(result)


async def list_payments_by_invoice_id(session: AsyncSession, invoice_id: uuid.UUID) -> list[Payment]:
    stmt = select(Payment).where(Payment.invoice_id == invoice_id)
    result = await session.scalars(stmt)
    return list(result)


async def list_payments_by_invoice_ids(session: AsyncSession, invoice_ids: Sequence[uuid.UUID]) -> list[Payment]:
    if not invoice_ids:
        return []
    stmt = select(Payment).where(Payment.invoice_id.in_(invoice_ids))
    result = await session.scalars(stmt)
    return list(result)


async def update_payment(
    session: AsyncSession,
    payment_id: uuid.UUID,
    data: PaymentUpdate,
) -> Payment | None:
    payment = await get_payment_by_id(session, payment_id)
    if payment is None:
        return None

    if "invoice_id" in data:
        payment.invoice_id = data["invoice_id"]
    if "amount" in data:
        payment.amount = data["amount"]
    if "kind" in data:
        payment.kind = data["kind"]
    if "method" in data:
        payment.method = data["method"]
    if "reference" in data:
        payment.reference = data["reference"]
    if "paid_at" in data:
        payment.paid_at = data["paid_at"]

    await session.commit()
    await session.refresh(payment)
    return payment


async def delete_payment(session: AsyncSession, payment_id: uuid.UUID) -> bool:
    payment = await get_payment_by_id(session, payment_id)
    if payment is None:
        return False

    await session.delete(payment)
    await session.commit()
    return True
