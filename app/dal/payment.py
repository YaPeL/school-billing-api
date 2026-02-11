import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dal._types import PaymentCreate, PaymentUpdate
from app.models.payment import Payment


def create_payment(session: Session, data: PaymentCreate) -> Payment:
    payment = Payment(
        invoice_id=data["invoice_id"],
        amount=data["amount"],
        method=data.get("method"),
        reference=data.get("reference"),
    )
    paid_at = data.get("paid_at")
    if paid_at is not None:
        payment.paid_at = paid_at

    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def get_payment_by_id(session: Session, payment_id: uuid.UUID) -> Payment | None:
    return session.get(Payment, payment_id)


def list_payments(session: Session, *, offset: int = 0, limit: int = 100) -> list[Payment]:
    stmt = select(Payment).offset(offset).limit(limit)
    return list(session.scalars(stmt))


def list_payments_by_invoice_id(session: Session, invoice_id: uuid.UUID) -> list[Payment]:
    stmt = select(Payment).where(Payment.invoice_id == invoice_id)
    return list(session.scalars(stmt))


def list_payments_by_invoice_ids(session: Session, invoice_ids: Sequence[uuid.UUID]) -> list[Payment]:
    if not invoice_ids:
        return []
    stmt = select(Payment).where(Payment.invoice_id.in_(invoice_ids))
    return list(session.scalars(stmt))


def update_payment(
    session: Session,
    payment_id: uuid.UUID,
    data: PaymentUpdate,
) -> Payment | None:
    payment = get_payment_by_id(session, payment_id)
    if payment is None:
        return None

    if "invoice_id" in data:
        payment.invoice_id = data["invoice_id"]
    if "amount" in data:
        payment.amount = data["amount"]
    if "method" in data:
        payment.method = data["method"]
    if "reference" in data:
        payment.reference = data["reference"]
    if "paid_at" in data:
        payment.paid_at = data["paid_at"]

    session.commit()
    session.refresh(payment)
    return payment


def delete_payment(session: Session, payment_id: uuid.UUID) -> bool:
    payment = get_payment_by_id(session, payment_id)
    if payment is None:
        return False

    session.delete(payment)
    session.commit()
    return True
