from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.api.constants import STUDENTS
from app.domain.dtos import StudentDTO
from app.domain.errors import NotFoundError
from app.services.ports import StudentRepo


async def create_student(repo: StudentRepo, data: Mapping[str, object]) -> StudentDTO:
    return await repo.create(data)


async def list_students(repo: StudentRepo, *, offset: int, limit: int) -> list[StudentDTO]:
    return await repo.list_all(offset=offset, limit=limit)


async def list_students_by_school_id(repo: StudentRepo, school_id: UUID, offset: int, limit: int) -> list[StudentDTO]:
    return await repo.list_by_school_id(school_id=school_id, offset=offset, limit=limit)


async def get_student_by_id(repo: StudentRepo, student_id: UUID) -> StudentDTO:
    student = await repo.get_by_id(student_id)
    if student is None:
        raise NotFoundError(STUDENTS, str(student_id))
    return student


async def update_student(repo: StudentRepo, student_id: UUID, data: Mapping[str, object]) -> StudentDTO:
    student = await repo.update(student_id, data)
    if student is None:
        raise NotFoundError(STUDENTS, str(student_id))
    return student


async def delete_student(repo: StudentRepo, student_id: UUID) -> bool:
    deleted = await repo.delete(student_id)
    if not deleted:
        raise NotFoundError(STUDENTS, str(student_id))
    return deleted
