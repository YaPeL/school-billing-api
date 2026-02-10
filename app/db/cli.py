from __future__ import annotations

import argparse
import subprocess

from app.db.seed import seed_db
from app.db.session import SessionLocal


def db_upgrade() -> None:
    subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], check=True)


def db_revision() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message", required=True)
    args = parser.parse_args()

    subprocess.run(
        ["alembic", "-c", "alembic.ini", "revision", "--autogenerate", "-m", args.message],
        check=True,
    )


def db_seed() -> None:
    session = SessionLocal()
    try:
        seed_db(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
