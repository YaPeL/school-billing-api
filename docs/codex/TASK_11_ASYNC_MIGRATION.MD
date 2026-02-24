# TASK_ASYNC_MIGRATION.md

You are a senior Python backend engineer working inside this repository.

Goal:
Migrate the codebase from synchronous SQLAlchemy/PostgreSQL access to fully asynchronous SQLAlchemy 2.0 using the `asyncpg` driver, while preserving the existing layered architecture:

- Routers -> Services -> DAL -> DB
- DAL is the ONLY layer that touches SQLAlchemy sessions
- Services remain easy to unit test by mocking DAL
- Keep code style, naming, and project conventions consistent with the current repo

## Target stack
- SQLAlchemy 2.x async API (`AsyncSession`, `create_async_engine`, `async_sessionmaker`)
- PostgreSQL driver: `asyncpg`
- FastAPI async routes and async dependencies
- pytest async support for integration tests

## High-level migration requirements

1. Database / engine / session
- Replace sync engine/session with async engine/session.
- Database URL must use:
  `postgresql+asyncpg://...`
- Introduce async session factory with:
  - `async_sessionmaker`
  - `expire_on_commit=False`
- Expose an async DB session dependency for FastAPI using `async def` + `yield`.

2. DAL layer
- Convert DAL functions to async.
- DAL functions must accept `AsyncSession`.
- Replace sync operations with awaited async equivalents:
  - `await session.execute(...)`
  - `await session.scalar(...)` / `await session.scalars(...)`
  - `await session.get(...)`
  - `await session.commit()`
  - `await session.refresh(...)`
  - `await session.delete(...)` if needed
- Use SQLAlchemy 2.0 style `select()` statements (avoid legacy `session.query()`).

3. Service layer
- Convert service functions to async where they call DAL.
- Keep business rules in services, DB access in DAL only.
- Preserve existing service contracts and validations as much as possible.
- Ensure transaction boundaries remain explicit and correct (commit/rollback behavior should stay consistent with current behavior).

4. Router layer
- Convert route handlers to `async def`.
- Update dependencies to inject `AsyncSession`.
- Await service calls.
- Keep request/response schemas and HTTP behavior unchanged unless a bug fix is necessary.

5. Tests
- Smoke tests:
  - Keep them fast and DB-free
  - They should continue mocking DAL (or services if that is the current project pattern)
  - Update tests to support async call sites (`AsyncMock`, async test functions only if needed)
- Integration tests:
  - Migrate to async DB/session usage
  - Use async fixtures where appropriate
  - Ensure setup/teardown and transaction rollback patterns work with async sessions
- Preserve or improve current test readability.

6. Migrations / tooling / dependencies
- Update dependencies in `pyproject.toml` (or equivalent) to include `asyncpg`.
- If Alembic is present:
  - Keep migrations working
  - Only update migration env wiring if required for compatibility
  - Do NOT rewrite historical migrations unnecessarily
- Keep lint/typecheck/tests passing.

## Constraints and pitfalls to avoid
- Do NOT mix sync SQLAlchemy session usage inside async routes/services.
- Do NOT leave any blocking DB calls in async handlers.
- Do NOT collapse architecture layers.
- Do NOT move business logic into routers or DAL.
- Minimize unrelated refactors.
- Keep public API behavior stable.

## Deliverables

1. Code changes across:
- DB/session setup
- DAL
- Services
- Routers
- Tests
- Dependency/config files (if needed)

2. A short migration summary in `ASYNC_MIGRATION_NOTES.md` including:
- What changed
- Any behavior-preserving assumptions
- Any follow-up tasks (if something could not be fully migrated)

## Implementation plan (execute in this order)

1. Inspect current sync DB/session wiring and identify all session entry points.
2. Migrate DB engine/session factory and FastAPI DB dependency to async.
3. Migrate DAL modules to `AsyncSession` and awaited SQLAlchemy calls.
4. Migrate services to async and update call chains.
5. Migrate routers to async and update dependency injection.
6. Fix smoke tests (mocks, `AsyncMock`, await assertions).
7. Fix integration tests and async fixtures.
8. Run and fix QA:
   - formatter
   - linter
   - type checks
   - smoke tests
   - integration tests (if available)

## Validation checklist (must pass)
- [ ] No sync SQLAlchemy Session usage remains in app runtime paths
- [ ] All DB URLs for runtime use `postgresql+asyncpg://`
- [ ] FastAPI routes calling DB-backed services are `async def`
- [ ] DAL only layer touching `AsyncSession`
- [ ] Smoke tests pass without DB
- [ ] Integration tests pass (or document blockers in ASYNC_MIGRATION_NOTES.md)
- [ ] No API contract regressions detected

## Notes for implementation
- Prefer small, focused commits logically grouped by layer if you are allowed to commit.
- Keep changes mechanical and reviewable.
- If you encounter ambiguous transaction ownership (service vs DAL), preserve current behavior first, then document follow-up improvements in ASYNC_MIGRATION_NOTES.md.
