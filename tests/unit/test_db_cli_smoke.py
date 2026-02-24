from __future__ import annotations

import subprocess
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db import cli


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.smoke
def test_db_upgrade_runs_alembic_upgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    run_mock = MagicMock()
    monkeypatch.setattr(subprocess, "run", run_mock)

    cli.db_upgrade()

    run_mock.assert_called_once_with(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=True)


@pytest.mark.smoke
def test_db_revision_runs_alembic_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    run_mock = MagicMock()
    monkeypatch.setattr(subprocess, "run", run_mock)
    monkeypatch.setattr(sys, "argv", ["db-revision", "-m", "init schema"])

    cli.db_revision()

    run_mock.assert_called_once_with(
        ["alembic", "-c", "alembic.ini", "revision", "--autogenerate", "-m", "init schema"],
        check=True,
    )


@pytest.mark.smoke
@pytest.mark.anyio
async def test_db_seed_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()
    seed_mock = AsyncMock()

    class SessionFactory:
        async def __aenter__(self) -> AsyncMock:
            return session

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    monkeypatch.setattr(cli, "SessionLocal", lambda: SessionFactory())
    monkeypatch.setattr(cli, "seed_db", seed_mock)

    await cli._db_seed_async()

    seed_mock.assert_awaited_once_with(session)
    session.commit.assert_awaited_once_with()
    session.rollback.assert_not_called()


@pytest.mark.smoke
@pytest.mark.anyio
async def test_db_seed_rolls_back_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    session = AsyncMock()

    async def fail_seed(_session: object) -> None:
        raise RuntimeError("seed failed")

    class SessionFactory:
        async def __aenter__(self) -> AsyncMock:
            return session

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    monkeypatch.setattr(cli, "SessionLocal", lambda: SessionFactory())
    monkeypatch.setattr(cli, "seed_db", fail_seed)

    with pytest.raises(RuntimeError, match="seed failed"):
        await cli._db_seed_async()

    session.commit.assert_not_called()
    session.rollback.assert_awaited_once_with()
