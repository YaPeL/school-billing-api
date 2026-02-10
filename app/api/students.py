from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT, STUDENTS
from app.api.exceptions import NotFoundError
from app.dal import student as student_dal
from app.dal._types import StudentCreate as DalStudentCreate
from app.dal._types import StudentUpdate as DalStudentUpdate
from app.db.session import get_db
from app.schemas import StudentCreate, StudentRead, StudentStatement, StudentUpdate
from app.services import statements as statement_service

router = APIRouter(prefix="/students", tags=["students"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=StudentRead)
def create_student(student_in: StudentCreate, session: DbSession) -> StudentRead:
    payload = cast(DalStudentCreate, student_in.model_dump())
    student = student_dal.create_student(session, data=payload)
    return StudentRead.model_validate(student)


@router.get("", response_model=list[StudentRead])
def list_students(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[StudentRead]:
    students = student_dal.list_students(session, offset=offset, limit=limit)
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: UUID, session: DbSession) -> StudentRead:
    student = student_dal.get_student_by_id(session, student_id=student_id)
    if student is None:
        raise NotFoundError(STUDENTS, str(student_id))
    return StudentRead.model_validate(student)


@router.patch("/{student_id}", response_model=StudentRead)
def patch_student(student_id: UUID, student_in: StudentUpdate, session: DbSession) -> StudentRead:
    payload = cast(DalStudentUpdate, student_in.model_dump(exclude_unset=True))
    student = student_dal.update_student(session, student_id=student_id, data=payload)
    if student is None:
        raise NotFoundError(STUDENTS, str(student_id))
    return StudentRead.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: UUID, session: DbSession) -> Response:
    deleted = student_dal.delete_student(session, student_id=student_id)
    if not deleted:
        raise NotFoundError(STUDENTS, str(student_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{student_id}/statement", response_model=StudentStatement)
def get_student_statement(student_id: UUID, session: DbSession) -> StudentStatement:
    try:
        return statement_service.get_student_statement(session, student_id=student_id)
    except ValueError as exc:
        raise NotFoundError(STUDENTS, str(student_id)) from exc
