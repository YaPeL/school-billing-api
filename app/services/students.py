from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.constants import STUDENTS
from app.api.exceptions import NotFoundError
from app.dal import student as student_dal
from app.dal.update_types import StudentCreate, StudentUpdate
from app.models.student import Student


def create_student(session: Session, data: StudentCreate) -> Student:
    return student_dal.create_student(session, data=data)


def list_students(session: Session, *, offset: int, limit: int) -> list[Student]:
    return student_dal.list_students(session, offset=offset, limit=limit)


def list_students_by_school_id(session: Session, school_id: UUID, offset: int, limit: int) -> list[Student]:
    return student_dal.list_students_by_school_id(session, school_id=school_id, offset=offset, limit=limit)


def get_student_by_id(session: Session, student_id: UUID) -> Student:
    student = student_dal.get_student_by_id(session, student_id=student_id)
    if student is None:
        raise NotFoundError(STUDENTS, str(student_id))
    return student


def update_student(session: Session, student_id: UUID, data: StudentUpdate) -> Student:
    student = student_dal.update_student(session, student_id=student_id, data=data)
    if student is None:
        raise NotFoundError(STUDENTS, str(student_id))
    return student


def delete_student(session: Session, student_id: UUID) -> bool:
    deleted = student_dal.delete_student(session, student_id=student_id)
    if not deleted:
        raise NotFoundError(STUDENTS, str(student_id))
    return deleted
