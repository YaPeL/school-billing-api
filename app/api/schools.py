from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.api.deps import require_admin
from app.dal.update_types import SchoolCreate as DalSchoolCreate
from app.dal.update_types import SchoolUpdate as DalSchoolUpdate
from app.db.session import get_db
from app.schemas import SchoolCreate, SchoolRead, SchoolStatement, SchoolUpdate
from app.schemas.auth import UserClaims
from app.services import schools as school_service
from app.services import statements as statement_service

router = APIRouter(prefix="/schools", tags=["schools"])

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[UserClaims, Depends(require_admin)]


@router.post("", response_model=SchoolRead)
def create_school(school_in: SchoolCreate, session: DbSession, _admin: AdminUser) -> SchoolRead:
    payload = cast(DalSchoolCreate, school_in.model_dump())
    school = school_service.create_school(session, data=payload)
    return SchoolRead.model_validate(school)


@router.get("", response_model=list[SchoolRead])
def list_schools(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[SchoolRead]:
    schools = school_service.list_schools(session, offset=offset, limit=limit)
    return [SchoolRead.model_validate(school) for school in schools]


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(school_id: UUID, session: DbSession) -> SchoolRead:
    school = school_service.get_school_by_id(session, school_id=school_id)
    return SchoolRead.model_validate(school)


@router.patch("/{school_id}", response_model=SchoolRead)
def patch_school(school_id: UUID, school_in: SchoolUpdate, session: DbSession, _admin: AdminUser) -> SchoolRead:
    payload = cast(DalSchoolUpdate, school_in.model_dump(exclude_unset=True))
    school = school_service.update_school(session, school_id=school_id, data=payload)
    return SchoolRead.model_validate(school)


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: UUID, session: DbSession, _admin: AdminUser) -> Response:
    school_service.delete_school(session, school_id=school_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{school_id}/statement", response_model=SchoolStatement)
def get_school_statement(school_id: UUID, session: DbSession) -> SchoolStatement:
    return statement_service.get_school_statement(session, school_id=school_id)
