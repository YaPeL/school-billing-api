from datetime import datetime
from uuid import UUID

from app.schemas.base import ReadSchemaModel, SchemaModel


class SchoolCreate(SchemaModel):
    name: str


class SchoolUpdate(SchemaModel):
    name: str | None = None


class SchoolRead(ReadSchemaModel):
    id: UUID
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
