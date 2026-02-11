from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import require_admin
from app.dal._types import StudentCreate as DalStudentCreate
from app.dal._types import StudentUpdate as DalStudentUpdate
from app.db.session import get_db
from app.schemas import StudentCreate, StudentRead, StudentStatement, StudentUpdate
from app.schemas.auth import UserClaims
from app.services import statements as statement_service
from app.services import students as student_service

router = APIRouter(prefix="/students", tags=["students"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=StudentRead)
def create_student(student_in: StudentCreate, session: DbSession, _admin: AdminUser) -> StudentRead:
    payload = cast(DalStudentCreate, student_in.model_dump())
    student = student_service.create_student(session, data=payload)
    return StudentRead.model_validate(student)


@router.get("", response_model=list[StudentRead])
def list_students(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[StudentRead]:
    students = student_service.list_students(session, offset=offset, limit=limit)
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: UUID, session: DbSession) -> StudentRead:
    student = student_service.get_student_by_id(session, student_id=student_id)
    return StudentRead.model_validate(student)


@router.patch("/{student_id}", response_model=StudentRead)
def patch_student(student_id: UUID, student_in: StudentUpdate, session: DbSession, _admin: AdminUser) -> StudentRead:
    payload = cast(DalStudentUpdate, student_in.model_dump(exclude_unset=True))
    student = student_service.update_student(session, student_id=student_id, data=payload)
    return StudentRead.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: UUID, session: DbSession, _admin: AdminUser) -> Response:
    student_service.delete_student(session, student_id=student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{student_id}/statement", response_model=StudentStatement)
def get_student_statement(student_id: UUID, session: DbSession) -> StudentStatement:
    return statement_service.get_student_statement(session, student_id=student_id)
