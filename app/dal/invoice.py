import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.update_types import InvoiceCreate, InvoiceUpdate
from app.domain.enums import InvoiceStatus
from app.models.invoice import Invoice


async def create_invoice(session: AsyncSession, data: InvoiceCreate) -> Invoice:
    invoice = Invoice(
        student_id=data["student_id"],
        total_amount=data["total_amount"],
        due_date=data["due_date"],
        description=data.get("description"),
    )
    status = data.get("status")
    invoice.status = status if status is not None else InvoiceStatus.PENDING
    issued_at = data.get("issued_at")
    if issued_at is not None:
        invoice.issued_at = issued_at

    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)
    return invoice


async def get_invoice_by_id(session: AsyncSession, invoice_id: uuid.UUID) -> Invoice | None:
    return await session.get(Invoice, invoice_id)


async def list_invoices(session: AsyncSession, *, offset: int = 0, limit: int = 100) -> list[Invoice]:
    stmt = select(Invoice).offset(offset).limit(limit)
    result = await session.scalars(stmt)
    return list(result)


async def list_invoices_by_student_id(session: AsyncSession, student_id: uuid.UUID) -> list[Invoice]:
    stmt = select(Invoice).where(Invoice.student_id == student_id)
    result = await session.scalars(stmt)
    return list(result)


async def list_invoices_by_student_ids(session: AsyncSession, student_ids: Sequence[uuid.UUID]) -> list[Invoice]:
    if not student_ids:
        return []
    stmt = select(Invoice).where(Invoice.student_id.in_(student_ids))
    result = await session.scalars(stmt)
    return list(result)


async def update_invoice(
    session: AsyncSession,
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
) -> Invoice | None:
    invoice = await get_invoice_by_id(session, invoice_id)
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
    if "status" in data:
        invoice.status = data["status"]
    if "issued_at" in data and data["issued_at"] is not None:
        invoice.issued_at = data["issued_at"]

    await session.commit()
    await session.refresh(invoice)
    return invoice


async def delete_invoice(session: AsyncSession, invoice_id: uuid.UUID) -> bool:
    invoice = await get_invoice_by_id(session, invoice_id)
    if invoice is None:
        return False

    await session.delete(invoice)
    await session.commit()
    return True
