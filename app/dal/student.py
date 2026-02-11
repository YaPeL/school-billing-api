import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dal.update_types import StudentCreate, StudentUpdate
from app.models.student import Student


def create_student(session: Session, data: StudentCreate) -> Student:
    student = Student(school_id=data["school_id"], full_name=data["full_name"])
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def get_student_by_id(session: Session, student_id: uuid.UUID) -> Student | None:
    return session.get(Student, student_id)


def list_students(session: Session, *, offset: int = 0, limit: int = 100) -> list[Student]:
    stmt = select(Student).offset(offset).limit(limit)
    return list(session.scalars(stmt))


def list_students_by_school_id(
    session: Session, school_id: uuid.UUID, offset: int = 0, limit: int = 100
) -> list[Student]:
    stmt = select(Student).where(Student.school_id == school_id).offset(offset).limit(limit)
    return list(session.scalars(stmt))


def update_student(
    session: Session,
    student_id: uuid.UUID,
    data: StudentUpdate,
) -> Student | None:
    student = get_student_by_id(session, student_id)
    if student is None:
        return None

    if "school_id" in data:
        student.school_id = data["school_id"]
    if "full_name" in data:
        student.full_name = data["full_name"]

    session.commit()
    session.refresh(student)
    return student


def delete_student(session: Session, student_id: uuid.UUID) -> bool:
    student = get_student_by_id(session, student_id)
    if student is None:
        return False

    session.delete(student)
    session.commit()
    return True
