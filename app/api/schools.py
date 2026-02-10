from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT, SCHOOLS
from app.api.exceptions import NotFoundError
from app.dal import school as school_dal
from app.dal._types import SchoolCreate as DalSchoolCreate
from app.dal._types import SchoolUpdate as DalSchoolUpdate
from app.db.session import get_db
from app.schemas import SchoolCreate, SchoolRead, SchoolStatement, SchoolUpdate
from app.services import statements as statement_service

router = APIRouter(prefix="/schools", tags=["schools"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=SchoolRead)
def create_school(school_in: SchoolCreate, session: DbSession) -> SchoolRead:
    payload = cast(DalSchoolCreate, school_in.model_dump())
    school = school_dal.create_school(session, data=payload)
    return SchoolRead.model_validate(school)


@router.get("", response_model=list[SchoolRead])
def list_schools(
    session: DbSession,
    offset: int = Query(default=DEFAULT_OFFSET, ge=0),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> list[SchoolRead]:
    schools = school_dal.list_schools(session, offset=offset, limit=limit)
    return [SchoolRead.model_validate(school) for school in schools]


@router.get("/{school_id}", response_model=SchoolRead)
def get_school(school_id: UUID, session: DbSession) -> SchoolRead:
    school = school_dal.get_school_by_id(session, school_id=school_id)
    if school is None:
        raise NotFoundError(SCHOOLS, str(school_id))
    return SchoolRead.model_validate(school)


@router.patch("/{school_id}", response_model=SchoolRead)
def patch_school(school_id: UUID, school_in: SchoolUpdate, session: DbSession) -> SchoolRead:
    payload = cast(DalSchoolUpdate, school_in.model_dump(exclude_unset=True))
    school = school_dal.update_school(session, school_id=school_id, data=payload)
    if school is None:
        raise NotFoundError(SCHOOLS, str(school_id))
    return SchoolRead.model_validate(school)


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(school_id: UUID, session: DbSession) -> Response:
    deleted = school_dal.delete_school(session, school_id=school_id)
    if not deleted:
        raise NotFoundError(SCHOOLS, str(school_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{school_id}/statement", response_model=SchoolStatement)
def get_school_statement(school_id: UUID, session: DbSession) -> SchoolStatement:
    try:
        return statement_service.get_school_statement(session, school_id=school_id)
    except ValueError as exc:
        raise NotFoundError(SCHOOLS, str(school_id)) from exc
