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
- [ ] (Optional) Integration tests using PostgreSQL

## 7. Extras (optional)
- [x] Pagination on list endpoints
- [x] (Optional) OpenTelemetry local tracing (Jaeger)
