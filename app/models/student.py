from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.school import School


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    school: Mapped[School] = relationship(back_populates="students")
    invoices: Mapped[list[Invoice]] = relationship(back_populates="student")
