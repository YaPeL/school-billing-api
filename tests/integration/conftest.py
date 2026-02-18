from __future__ import annotations

from collections.abc import Generator
from os import getenv

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

LOCAL_TEST_DB_HOSTS = {"localhost", "127.0.0.1", "::1"}


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


@pytest.fixture(scope="session")
def integration_engine() -> Generator[Engine, None, None]:
    test_database_url = get_test_db_url_or_skip()
    engine = create_engine(test_database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        pytest.skip(f"Integration DB unavailable at {test_database_url}: {exc}")

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(integration_engine: Engine) -> Generator[Session, None, None]:
    session_local = sessionmaker(bind=integration_engine, autoflush=False, autocommit=False)
    session = session_local()

    session.execute(text("TRUNCATE TABLE payments, invoices, students, schools RESTART IDENTITY CASCADE"))
    session.commit()

    try:
        yield session
    finally:
        session.close()
