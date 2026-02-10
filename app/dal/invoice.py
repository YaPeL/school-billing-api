import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dal._types import InvoiceCreate, InvoiceUpdate
from app.models import Invoice


def create_invoice(session: Session, data: InvoiceCreate) -> Invoice:
    invoice = Invoice(
        student_id=data["student_id"],
        total_amount=data["total_amount"],
        due_date=data["due_date"],
        description=data.get("description"),
    )
    issued_at = data.get("issued_at")
    if issued_at is not None:
        invoice.issued_at = issued_at

    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


def get_invoice_by_id(session: Session, invoice_id: uuid.UUID) -> Invoice | None:
    return session.get(Invoice, invoice_id)


def list_invoices(session: Session, *, offset: int = 0, limit: int = 100) -> list[Invoice]:
    stmt = select(Invoice).offset(offset).limit(limit)
    return list(session.scalars(stmt))


def update_invoice(
    session: Session,
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
) -> Invoice | None:
    invoice = get_invoice_by_id(session, invoice_id)
    if invoice is None:
        return None

    if "student_id" in data:
        invoice.student_id = data["student_id"]
    if "total_amount" in data:
        invoice.total_amount = data["total_amount"]
    if "due_date" in data:
        invoice.due_date = data["due_date"]
    if "description" in data:
        invoice.description = data["description"]
    if "issued_at" in data and data["issued_at"] is not None:
        invoice.issued_at = data["issued_at"]

    session.commit()
    session.refresh(invoice)
    return invoice


def delete_invoice(session: Session, invoice_id: uuid.UUID) -> bool:
    invoice = get_invoice_by_id(session, invoice_id)
    if invoice is None:
        return False

    session.delete(invoice)
    session.commit()
    return True
