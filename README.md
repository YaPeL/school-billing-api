# Mattilda Backend Challenge

[![CI](https://github.com/YaPeL/school-billing-api/actions/workflows/ci.yml/badge.svg)](https://github.com/YaPeL/school-billing-api/actions/workflows/ci.yml)
![Type Check](https://img.shields.io/badge/type%20check-mypy-blue)
![Tests](https://img.shields.io/badge/tests-smoke%20in%20CI-brightgreen)

TODO: add coverage badge once integration coverage reporting is added.

## Requirements
- Python 3.12
- Poetry
- Docker + Docker Compose

## Quickstart
1. Install dependencies:
   - `poetry install`
   - `pre-commit install`
2. Start PostgreSQL:
   - `docker compose up -d db`
3. Apply migrations:
   - `poetry run db-upgrade`
4. Seed demo data:
   - `poetry run db-seed`
5. Run the API:
   - `poetry run uvicorn app.main:app --reload`
   
Extra generate migrations:
   - `poetry run db-revision -m "message"`

Open:
- http://localhost:8000/docs
- http://localhost:8000/health
- http://localhost:8000/health/db
- http://localhost:8000/metrics

## Auth (demo JWT)
1. Login and capture token:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change_me"}' \
  | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')
```
2. Call a protected write endpoint with Bearer token:
```bash
curl -X POST http://localhost:8000/schools \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Springfield Elementary"}'
```

Read endpoints remain public (`GET` schools/students/invoices/payments, statements, health, metrics).

## Run (docker)
- `docker compose up --build`

## Tests
- Fast tests (no DB):
  - `poetry run pytest -m smoke`

## Notes
- Observability: structured logs + `/health` + `/health/db` + `/metrics`
- Payments are first-class (partial payments supported)
- Migrations are manual by design (they are not auto-run on app import/startup)
- CI runs `ruff`, `mypy`, and smoke tests on push/PR to `main`

## TODO / Future improvements

### Async DB + fully async API
- Switch to an **async SQLAlchemy stack** so endpoints can be truly async end-to-end:
  - Use an async driver (eg `asyncpg`) + `create_async_engine`
  - Replace `Session` with `AsyncSession` + async dependency (`async with` session)
  - Update DAL to `async def` and use `await session.execute(...)`
  - Ensure middleware + auth deps remain compatible with async execution
- Goal: remove sync DB calls from async routes and make the whole request path non-blocking.

### Layer contracts (Service <-> DAL)
- Replace `TypedDict` update payloads with a **Patch dataclass + `UNSET` sentinel** to make partial updates explicit:
  - `UNSET` = field not provided (do not touch)
  - `None` = explicitly set to NULL (if allowed)
  - value = set value
- Prefer returning **DTO dataclasses** from DAL (instead of ORM objects) to avoid accidental lazy-loads and to improve testability.

### Error handling: integrity / constraint mapping
- Map DB constraint errors (`IntegrityError`) to clean API errors (409/422) with readable messages.
- Example:
  - Deleting an invoice with payments attached currently yields a 500.
  - Preferred behavior:
    - Option A: 409 Conflict with message like "Cannot delete invoice with payments"
    - Option B: enforce cascade rules explicitly (only if product wants it)
- Add a small error-mapper layer (DB exception -> domain/API error) and reuse it across routes.

### Caching (Redis)
- Add optional Redis caching for **statements** (student/school):
  - Cache keys: `statement:{scope}:{id}:{version}`
  - Invalidation strategy:
    - Option A: delete affected statement keys on any invoice/payment write
    - Option B: bump a per-student/per-school version number and include it in the cache key
  - Short TTL (eg 30–120s) for demo.
- Keep cache optional: if `REDIS_URL` is not set, caching is disabled.

### Integration tests (real DB)
- Add `integration` tests that run against a real Postgres (docker-compose).
- Keep smoke tests DB-free.
- Make integration opt-in:
  - Local: `pytest -m integration`
  - CI: smoke only (for this challenge)

### Observability extras
- Add Sentry via `SENTRY_DSN`:
  - capture unhandled exceptions
  - optional performance tracing
- Add OpenTelemetry behind env flags (export to a local collector, no paid backend required).

### Test runtime / parallelism
- Add `pytest-xdist`:
  - `pytest -m smoke -n auto`
- Ensure tests remain isolated and do not depend on global mutable state.

### Docker image size (multi-stage build)
- Switch to a **multi-stage Docker build**:
  - builder stage installs deps and builds wheels / venv
  - runtime stage copies only what’s needed + app code
- Use `python:3.12-slim` and avoid build tools in the final image.

### Coverage
- Add `pytest-cov` and document local usage:
  - `poetry run pytest -m smoke --cov=app --cov-report=term-missing`
  - `poetry run pytest -m smoke --cov=app --cov-report=html`
- Add CI coverage artifact + badge later.

### Aggregations: push down to DB (perf)
- Current statements compute totals in Python (`sum(...)` over invoices/payments).
- Future: move aggregation to DAL using SQL (`SUM`, `GROUP BY`) to reduce memory/IO for large datasets:
  - `paid_total_by_invoice(invoice_ids)` -> `{invoice_id: Decimal}`
  - `statement_totals_for_student(student_id)` / `...for_school(school_id)` -> `StatementTotals`
- Keep business rules (status derivation) in service, but fetch pre-aggregated numbers from DB when possible.

### CI: AI review bot on PRs
- Add an optional PR check that runs an LLM review (Claude/Codex) and posts a comment:
  - Trigger: `pull_request` (maybe only for repo members or via manual `/ai-review` comment)
  - Inputs: git diff vs base branch + repo conventions + review rubric
  - Output: top issues + quick wins, no auto-merge
- Keep it non-blocking at first (informational), then decide if any checks should become required.

### Other small improvements
- Centralize invoice status derivation behind a single domain/service function and reuse it consistently.
- Propagate request ids consistently and return `X-Request-Id` header.
