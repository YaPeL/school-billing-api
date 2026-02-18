from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import get_school_repo, get_school_statement_uc, require_admin
from app.schemas import SchoolCreate, SchoolRead, SchoolStatement, SchoolUpdate
from app.schemas.auth import UserClaims
from app.services import schools as school_service
from app.services.ports import SchoolRepo
from app.services.use_cases import GetSchoolStatement

router = APIRouter(prefix="/schools", tags=["schools"])

SchoolRepoDep = Annotated[SchoolRepo, Depends(get_school_repo)]
SchoolStatementUCDep = Annotated[GetSchoolStatement, Depends(get_school_statement_uc)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=SchoolRead)
def create_school(school_in: SchoolCreate, repo: SchoolRepoDep, _admin: AdminUser) -> SchoolRead:
    school = school_service.create_school(repo, data=school_in.model_dump())
    return SchoolRead.model_validate(school)


@router.get("", response_model=list[SchoolRead])
def list_schools(
    repo: SchoolRepoDep,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[SchoolRead]:
    schools = school_service.list_schools(repo, offset=offset, limit=limit)
    return [SchoolRead.model_validate(school) for school in schools]


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(school_id: UUID, repo: SchoolRepoDep) -> SchoolRead:
    school = school_service.get_school_by_id(repo, school_id=school_id)
    return SchoolRead.model_validate(school)


@router.patch("/{school_id}", response_model=SchoolRead)
def patch_school(school_id: UUID, school_in: SchoolUpdate, repo: SchoolRepoDep, _admin: AdminUser) -> SchoolRead:
    school = school_service.update_school(repo, school_id=school_id, data=school_in.model_dump(exclude_unset=True))
    return SchoolRead.model_validate(school)


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: UUID, repo: SchoolRepoDep, _admin: AdminUser) -> Response:
    school_service.delete_school(repo, school_id=school_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{school_id}/statement", response_model=SchoolStatement)
def get_school_statement(school_id: UUID, use_case: SchoolStatementUCDep) -> SchoolStatement:
    return use_case(school_id)
