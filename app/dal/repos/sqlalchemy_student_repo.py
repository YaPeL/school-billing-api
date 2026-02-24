from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.dal import student as student_dal
from app.dal.update_types import StudentCreate, StudentUpdate
from app.domain.dtos import StudentDTO
from app.models.student import Student


class SQLAlchemyStudentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: Mapping[str, object]) -> StudentDTO:
        payload: StudentCreate = {
            "school_id": cast(UUID, data["school_id"]),
            "full_name": cast(str, data["full_name"]),
        }
        student = await student_dal.create_student(
            self._session,
            data=payload,
        )
        return _to_student_dto(student)

    async def list_all(self, *, offset: int, limit: int) -> list[StudentDTO]:
        students = await student_dal.list_students(self._session, offset=offset, limit=limit)
        return [_to_student_dto(student) for student in students]

    async def list_by_school_id(self, school_id: UUID, *, offset: int = 0, limit: int = 100) -> list[StudentDTO]:
        students = await student_dal.list_students_by_school_id(
            self._session, school_id=school_id, offset=offset, limit=limit
        )
        return [_to_student_dto(student) for student in students]

    async def get_by_id(self, student_id: UUID) -> StudentDTO | None:
        student = await student_dal.get_student_by_id(self._session, student_id=student_id)
        return None if student is None else _to_student_dto(student)

    async def update(self, student_id: UUID, data: Mapping[str, object]) -> StudentDTO | None:
        payload: StudentUpdate = {}
        if "school_id" in data:
            payload["school_id"] = cast(UUID, data["school_id"])
        if "full_name" in data:
            payload["full_name"] = cast(str, data["full_name"])

        student = await student_dal.update_student(self._session, student_id=student_id, data=payload)
        return None if student is None else _to_student_dto(student)

    async def delete(self, student_id: UUID) -> bool:
        return await student_dal.delete_student(self._session, student_id=student_id)


def _to_student_dto(student: Student) -> StudentDTO:
    return StudentDTO(
        id=student.id,
        school_id=student.school_id,
        full_name=student.full_name,
        created_at=cast(datetime | None, getattr(student, "created_at", None)),
        updated_at=cast(datetime | None, getattr(student, "updated_at", None)),
    )
