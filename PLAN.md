# PLAN

## 0. Project bootstrap
- [x] Initialize Poetry project + FastAPI skeleton + app/ structure
- [x] Configure ruff, mypy, pytest
- [x] Configure pytest markers: smoke, integration
- [x] Configure pre-commit: ruff, mypy, pytest -m smoke
- [x] Add Dockerfile + docker-compose (api + postgres)
- [x] Add settings (pydantic-settings)
- [x] Observability: structured logs + request_id + latency middleware
- [x] Add /health and /health/db
- [x] Add /metrics (Prometheus)

## 1. DB & models
- [x] SQLAlchemy engine/session dependency
- [x] ORM models: School, Student, Invoice, Payment + relationships + constraints
- [x] (Optional) Alembic + initial migration

## 2. Auth (basic, demo-friendly)
- [x] /auth/login: simple JWT (include role claim)
- [x] require_auth + require_role("admin")

## 3. Schemas + DAL + Services
- [x] Pydantic schemas (create/update/read) for all entities (Pydantic v2, Decimal amounts, UUID IDs, timestamp fields on read models)
- [x] DAL functions (only layer touching Session)
- [x] Services: business rules (invoice balances, statements)

## 4. API
- [x] CRUD /schools
- [x] CRUD /students
- [x] CRUD /invoices
- [x] CRUD /payments
- [x] Payments:
  - [x] POST /payments
  - [x] GET /invoices/{id}/payments
  - [x] (Optional) DELETE /payments/{id}
- [x] GET /students/{id}/statement
- [x] GET /schools/{id}/statement

## 5. Seed data
- [x] Idempotent seed script app/db/seed.py
- [x] README: seed command + example IDs

## 6. Tests
- [x] Smoke unit tests mocking DAL (fast, no DB)
- [x] (Optional) Integration tests using PostgreSQL (`@pytest.mark.integration`, real DB)
- [x] Integration DB safety gate (`TEST_DATABASE_URL` + safe local test DB validation before TRUNCATE)

## 7. Extras (optional)
- [x] Pagination on list endpoints
- [x] (Optional) OpenTelemetry local tracing (Jaeger)

## 8. Submission readiness
- [x] GitHub Actions CI (push/PR to main, Python 3.12, ruff + mypy + smoke)
- [x] README badges (CI + type-check + tests) and quickstart/auth polish
- [x] Ports + adapters sweet-spot refactor (domain DTO/errors, repo protocols, SQLAlchemy adapters, thin routers with use-case deps)
- [x] Convert DB-backed FastAPI handlers to sync `def` to avoid blocking the event loop with sync SQLAlchemy calls
- [ ] TODO: statement caching strategy (cache targets + invalidation plan)
