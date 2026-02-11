from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.constants import SCHOOLS
from app.api.exceptions import NotFoundError
from app.dal import school as school_dal
from app.dal.update_types import SchoolCreate, SchoolUpdate
from app.models.school import School


def create_school(session: Session, data: SchoolCreate) -> School:
    return school_dal.create_school(session, data=data)


def list_schools(session: Session, *, offset: int, limit: int) -> list[School]:
    return school_dal.list_schools(session, offset=offset, limit=limit)


def get_school_by_id(session: Session, school_id: UUID) -> School:
    school = school_dal.get_school_by_id(session, school_id=school_id)
    if school is None:
        raise NotFoundError(SCHOOLS, str(school_id))
    return school


def update_school(session: Session, school_id: UUID, data: SchoolUpdate) -> School:
    school = school_dal.update_school(session, school_id=school_id, data=data)
    if school is None:
        raise NotFoundError(SCHOOLS, str(school_id))
    return school


def delete_school(session: Session, school_id: UUID) -> bool:
    deleted = school_dal.delete_school(session, school_id=school_id)
    if not deleted:
        raise NotFoundError(SCHOOLS, str(school_id))
    return deleted
