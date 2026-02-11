import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dal._types import SchoolCreate, SchoolUpdate
from app.models.school import School


def create_school(session: Session, data: SchoolCreate) -> School:
    school = School(name=data["name"])
    session.add(school)
    session.commit()
    session.refresh(school)
    return school


def get_school_by_id(session: Session, school_id: uuid.UUID) -> School | None:
    return session.get(School, school_id)


def list_schools(session: Session, *, offset: int = 0, limit: int = 100) -> list[School]:
    stmt = select(School).offset(offset).limit(limit)
    return list(session.scalars(stmt))


def update_school(session: Session, school_id: uuid.UUID, data: SchoolUpdate) -> School | None:
    school = get_school_by_id(session, school_id)
    if school is None:
        return None

    if "name" in data:
        school.name = data["name"]

    session.commit()
    session.refresh(school)
    return school


def delete_school(session: Session, school_id: uuid.UUID) -> bool:
    school = get_school_by_id(session, school_id)
    if school is None:
        return False

    session.delete(school)
    session.commit()
    return True
