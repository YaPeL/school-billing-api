from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from app.db import cli


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
def test_db_seed_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    seed_mock = MagicMock()

    monkeypatch.setattr(cli, "SessionLocal", lambda: session)
    monkeypatch.setattr(cli, "seed_db", seed_mock)

    cli.db_seed()

    seed_mock.assert_called_once_with(session)
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


@pytest.mark.smoke
def test_db_seed_rolls_back_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()

    def fail_seed(_session: object) -> None:
        raise RuntimeError("seed failed")

    monkeypatch.setattr(cli, "SessionLocal", lambda: session)
    monkeypatch.setattr(cli, "seed_db", fail_seed)

    with pytest.raises(RuntimeError, match="seed failed"):
        cli.db_seed()

    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
