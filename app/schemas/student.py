from datetime import datetime
from uuid import UUID

from app.schemas.base import ReadSchemaModel, SchemaModel


class StudentCreate(SchemaModel):
    school_id: UUID
    full_name: str


class StudentUpdate(SchemaModel):
    school_id: UUID | None = None
    full_name: str | None = None


class StudentRead(ReadSchemaModel):
    id: UUID
    school_id: UUID
    full_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
