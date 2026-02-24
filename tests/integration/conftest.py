from __future__ import annotations

from collections.abc import AsyncGenerator
from os import getenv

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base

LOCAL_TEST_DB_HOSTS = {"localhost", "127.0.0.1", "::1"}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _is_test_database_name(database_name: str) -> bool:
    return database_name.startswith("test_") or database_name.endswith("_test") or "_test" in database_name


def assert_safe_test_db(database_url: str) -> None:
    parsed_url = make_url(database_url)
    database_name = parsed_url.database or ""

    if not database_name:
        pytest.skip(f"Integration tests skipped: test DB URL has no database name: {database_url}")

    if not _is_test_database_name(database_name):
        pytest.skip(
            "Integration tests skipped: test DB name must include a test marker "
            "(contains '_test', starts with 'test_', or ends with '_test'). "
            f"Got database='{database_name}'."
        )

    if parsed_url.host not in LOCAL_TEST_DB_HOSTS:
        pytest.skip(
            "Integration tests skipped: test DB host must be local "
            f"(one of {sorted(LOCAL_TEST_DB_HOSTS)}). Got host='{parsed_url.host}'."
        )


def get_test_db_url_or_skip() -> str:
    test_database_url = getenv("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Integration tests skipped: set TEST_DATABASE_URL to an isolated local test database URL.")

    assert_safe_test_db(test_database_url)
    return test_database_url


@pytest_asyncio.fixture(scope="session")
async def integration_engine() -> AsyncGenerator[AsyncEngine, None]:
    test_database_url = get_test_db_url_or_skip()
    engine = create_async_engine(test_database_url, pool_pre_ping=True)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as exc:
        pytest.skip(f"Integration DB unavailable at {test_database_url}: {exc}")

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(integration_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_local = async_sessionmaker(bind=integration_engine, autoflush=False, expire_on_commit=False)
    async with session_local() as session:
        await session.execute(text("TRUNCATE TABLE payments, invoices, students, schools RESTART IDENTITY CASCADE"))
        await session.commit()

        yield session
