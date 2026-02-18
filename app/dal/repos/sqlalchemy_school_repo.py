from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy.orm import Session

from app.dal import school as school_dal
from app.dal.update_types import SchoolCreate, SchoolUpdate
from app.domain.dtos import SchoolDTO
from app.models.school import School


class SQLAlchemySchoolRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: Mapping[str, object]) -> SchoolDTO:
        payload: SchoolCreate = {"name": cast(str, data["name"])}
        school = school_dal.create_school(self._session, data=payload)
        return _to_school_dto(school)

    def list_all(self, *, offset: int, limit: int) -> list[SchoolDTO]:
        schools = school_dal.list_schools(self._session, offset=offset, limit=limit)
        return [_to_school_dto(school) for school in schools]

    def get_by_id(self, school_id: UUID) -> SchoolDTO | None:
        school = school_dal.get_school_by_id(self._session, school_id=school_id)
        return None if school is None else _to_school_dto(school)

    def update(self, school_id: UUID, data: Mapping[str, object]) -> SchoolDTO | None:
        payload: SchoolUpdate = {}
        if "name" in data:
            payload["name"] = cast(str, data["name"])

        school = school_dal.update_school(self._session, school_id=school_id, data=payload)
        return None if school is None else _to_school_dto(school)

    def delete(self, school_id: UUID) -> bool:
        return school_dal.delete_school(self._session, school_id=school_id)


def _to_school_dto(school: School) -> SchoolDTO:
    return SchoolDTO(
        id=school.id,
        name=school.name,
        created_at=cast(datetime | None, getattr(school, "created_at", None)),
        updated_at=cast(datetime | None, getattr(school, "updated_at", None)),
    )
