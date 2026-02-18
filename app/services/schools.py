from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.api.constants import SCHOOLS
from app.domain.dtos import SchoolDTO
from app.domain.errors import NotFoundError
from app.services.ports import SchoolRepo


def create_school(repo: SchoolRepo, data: Mapping[str, object]) -> SchoolDTO:
    return repo.create(data)


def list_schools(repo: SchoolRepo, *, offset: int, limit: int) -> list[SchoolDTO]:
    return repo.list_all(offset=offset, limit=limit)


def get_school_by_id(repo: SchoolRepo, school_id: UUID) -> SchoolDTO:
    school = repo.get_by_id(school_id)
    if school is None:
        raise NotFoundError(SCHOOLS, str(school_id))
    return school


def update_school(repo: SchoolRepo, school_id: UUID, data: Mapping[str, object]) -> SchoolDTO:
    school = repo.update(school_id, data)
    if school is None:
        raise NotFoundError(SCHOOLS, str(school_id))
    return school


def delete_school(repo: SchoolRepo, school_id: UUID) -> bool:
    deleted = repo.delete(school_id)
    if not deleted:
        raise NotFoundError(SCHOOLS, str(school_id))
    return deleted
