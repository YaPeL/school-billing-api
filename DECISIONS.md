# DECISIONS

- Payments are first-class: invoices can have multiple payments (partial payments supported).
- Invoice status is derived from payments; overpaid invoices use `CREDIT` status (PENDING/PARTIAL/PAID/CREDIT via `InvoiceStatus` enum).
- DAL is the only layer touching SQLAlchemy `Session`; services orchestrate DAL and apply business rules.
- Primary keys for School/Student/Invoice/Payment use UUIDv7; all related foreign keys are UUID.
- DAL create/update inputs use TypedDict payloads (not many function params).
- Auth is demo-basic JWT with a role claim (admin). No user table unless required.
- Auth transport uses HTTP Bearer tokens with JSON login (`POST /auth/login`) to keep smoke tests and local usage simple (no OAuth form flow).
- Admin credentials are env-configured (`ADMIN_USERNAME`, `ADMIN_PASSWORD`), with demo defaults and warning logs when insecure defaults are used.
- Observability is free/simple: structured logs, `/health`, `/health/db`, `/metrics`.
- Database migrations are manual local/dev operations via Alembic CLI wrappers (`db-upgrade`, `db-revision`) and never auto-run on app import/startup.
- Seed data is intentionally idempotent-ish using stable demo natural keys (school/student names, invoice attributes, payment references) so `db-seed` is safe to run repeatedly.
- API smoke tests for HTTP routes use HTTPX `AsyncClient` + `ASGITransport` (not `TestClient`) for Python 3.13 compatibility; DB access is mocked via dependency override.
- 404 handling uses a custom `NotFoundError` with a global exception handler; routers raise `NotFoundError` instead of `HTTPException` for missing resources.
- Pagination defaults are centralized (offset/limit/max) in `app/api/constants.py`.
