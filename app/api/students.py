from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import get_student_repo, get_student_statement_uc, require_admin
from app.schemas import StudentCreate, StudentRead, StudentStatement, StudentUpdate
from app.schemas.auth import UserClaims
from app.services import students as student_service
from app.services.ports import StudentRepo
from app.services.use_cases import GetStudentStatement

router = APIRouter(prefix="/students", tags=["students"])

StudentRepoDep = Annotated[StudentRepo, Depends(get_student_repo)]
StudentStatementUCDep = Annotated[GetStudentStatement, Depends(get_student_statement_uc)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=StudentRead)
def create_student(student_in: StudentCreate, repo: StudentRepoDep, _admin: AdminUser) -> StudentRead:
    student = student_service.create_student(repo, data=student_in.model_dump())
    return StudentRead.model_validate(student)


@router.get("", response_model=list[StudentRead])
def list_students(
    repo: StudentRepoDep,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[StudentRead]:
    students = student_service.list_students(repo, offset=offset, limit=limit)
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: UUID, repo: StudentRepoDep) -> StudentRead:
    student = student_service.get_student_by_id(repo, student_id=student_id)
    return StudentRead.model_validate(student)


@router.patch("/{student_id}", response_model=StudentRead)
def patch_student(student_id: UUID, student_in: StudentUpdate, repo: StudentRepoDep, _admin: AdminUser) -> StudentRead:
    student = student_service.update_student(
        repo, student_id=student_id, data=student_in.model_dump(exclude_unset=True)
    )
    return StudentRead.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: UUID, repo: StudentRepoDep, _admin: AdminUser) -> Response:
    student_service.delete_student(repo, student_id=student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{student_id}/statement", response_model=StudentStatement)
def get_student_statement(student_id: UUID, use_case: StudentStatementUCDep) -> StudentStatement:
    return use_case(student_id)
