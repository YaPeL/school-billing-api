import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.update_types import StudentCreate, StudentUpdate
from app.models.student import Student


async def create_student(session: AsyncSession, data: StudentCreate) -> Student:
    student = Student(school_id=data["school_id"], full_name=data["full_name"])
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return student


async def get_student_by_id(session: AsyncSession, student_id: uuid.UUID) -> Student | None:
    return await session.get(Student, student_id)


async def list_students(session: AsyncSession, *, offset: int = 0, limit: int = 100) -> list[Student]:
    stmt = select(Student).offset(offset).limit(limit)
    result = await session.scalars(stmt)
    return list(result)


async def list_students_by_school_id(
    session: AsyncSession, school_id: uuid.UUID, offset: int = 0, limit: int = 100
) -> list[Student]:
    stmt = select(Student).where(Student.school_id == school_id).offset(offset).limit(limit)
    result = await session.scalars(stmt)
    return list(result)


async def update_student(
    session: AsyncSession,
    student_id: uuid.UUID,
    data: StudentUpdate,
) -> Student | None:
    student = await get_student_by_id(session, student_id)
    if student is None:
        return None

    if "school_id" in data:
        student.school_id = data["school_id"]
    if "full_name" in data:
        student.full_name = data["full_name"]

    await session.commit()
    await session.refresh(student)
    return student


async def delete_student(session: AsyncSession, student_id: uuid.UUID) -> bool:
    student = await get_student_by_id(session, student_id)
    if student is None:
        return False

    await session.delete(student)
    await session.commit()
    return True
