# PLAN

## 0. Project bootstrap
- [ ] Initialize Poetry project + FastAPI skeleton + app/ structure
- [ ] Configure ruff, mypy, pytest
- [ ] Configure pytest markers: smoke, integration
- [ ] Configure pre-commit: ruff, mypy, pytest -m smoke
- [ ] Add Dockerfile + docker-compose (api + postgres)
- [ ] Add settings (pydantic-settings)
- [ ] Observability: structured logs + request_id + latency middleware
- [ ] Add /health and /health/db
- [ ] Add /metrics (Prometheus)

## 1. DB & models
- [ ] SQLAlchemy engine/session dependency
- [x] ORM models: School, Student, Invoice, Payment + relationships + constraints
- [ ] (Optional) Alembic + initial migration

## 2. Auth (basic, demo-friendly)
- [ ] /auth/login: simple JWT (include role claim)
- [ ] require_auth + require_role("admin")

## 3. Schemas + DAL + Services
- [ ] Pydantic schemas (create/update/read) for all entities
- [x] DAL functions (only layer touching Session)
- [ ] Services: business rules (invoice balances, statements)

## 4. API
- [ ] CRUD /schools
- [ ] CRUD /students
- [ ] CRUD /invoices
- [ ] Payments:
  - [ ] POST /payments
  - [ ] GET /invoices/{id}/payments
  - [ ] (Optional) DELETE /payments/{id}
- [ ] GET /students/{id}/statement
- [ ] GET /schools/{id}/statement

## 5. Seed data
- [ ] Idempotent seed script app/db/seed.py
- [ ] README: seed command + example IDs

## 6. Tests
- [x] Smoke unit tests mocking DAL (fast, no DB)
- [ ] (Optional) Integration tests using PostgreSQL

## 7. Extras (optional)
- [ ] Pagination on list endpoints
- [ ] (Optional) OpenTelemetry local tracing (Jaeger)
