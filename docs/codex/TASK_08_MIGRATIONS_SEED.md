Add Alembic migrations + DB init/seed for local demo.

Goals:
- Introduce Alembic with SQLAlchemy 2.0 models:
  - Create alembic/ directory, env.py wired to app.models Base metadata
  - Add initial migration creating tables: schools, students, invoices, payments
- Provide a simple seed mechanism for local dev:
  - `app/db/seed.py` with `seed_db(session)` idempotent-ish (safe to run twice)
  - Seed at least:
    - 1 school
    - 2 students
    - 2 invoices (one paid, one partial or credit scenario)
    - 2+ payments
- Add CLI entrypoints via Poetry scripts:
  - `poetry run db-upgrade` -> alembic upgrade head
  - `poetry run db-revision -m "msg"` -> alembic revision --autogenerate
  - `poetry run db-seed` -> run seed script against DATABASE_URL
- Docker/local ergonomics:
  - Ensure app can run without migrations auto-running on import.
  - Update README with quickstart:
    - docker compose up db
    - db-upgrade
    - db-seed
    - run api
- Tests:
  - Keep existing smoke tests fast and DB-free.
  - Optional: add 1 integration test marked `integration` that spins a real DB only if DATABASE_URL points to local docker (skip otherwise). Keep it minimal.

Constraints:
- Do not change API contracts.
- ruff + mypy + pytest -m smoke must pass.
