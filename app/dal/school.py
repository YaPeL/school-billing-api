import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.update_types import SchoolCreate, SchoolUpdate
from app.models.school import School


async def create_school(session: AsyncSession, data: SchoolCreate) -> School:
    school = School(name=data["name"])
    session.add(school)
    await session.commit()
    await session.refresh(school)
    return school


async def get_school_by_id(session: AsyncSession, school_id: uuid.UUID) -> School | None:
    return await session.get(School, school_id)


async def list_schools(session: AsyncSession, *, offset: int = 0, limit: int = 100) -> list[School]:
    stmt = select(School).offset(offset).limit(limit)
    result = await session.scalars(stmt)
    return list(result)


async def update_school(session: AsyncSession, school_id: uuid.UUID, data: SchoolUpdate) -> School | None:
    school = await get_school_by_id(session, school_id)
    if school is None:
        return None

    if "name" in data:
        school.name = data["name"]

    await session.commit()
    await session.refresh(school)
    return school


async def delete_school(session: AsyncSession, school_id: uuid.UUID) -> bool:
    school = await get_school_by_id(session, school_id)
    if school is None:
        return False

    await session.delete(school)
    await session.commit()
    return True
