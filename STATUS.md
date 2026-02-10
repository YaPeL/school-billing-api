# STATUS

## Running
- Install:
  - poetry install
  - pre-commit install
- Run (local):
  - docker compose up -d db
  - poetry run db-upgrade
  - poetry run db-seed
  - poetry run uvicorn app.main:app --reload
- Run (docker):
  - docker compose up --build
- Tests:
  - poetry run pytest -m smoke
  - poetry run pytest -m "smoke or integration" (optional)

## Implemented
- PLAN milestone updated: project bootstrap checkbox "Initialize Poetry project + FastAPI skeleton + app/ structure" marked complete
- Bootstrap project structure
- Settings + logging middleware
- /health, /health/db, /metrics
- SQLAlchemy typed ORM models for School/Student/Invoice/Payment with FK indexes and relationships
- Alembic configured (`alembic/`, `alembic.ini`, env wired to `Base.metadata`) with initial migration for schools/students/invoices/payments
- Poetry DB CLI scripts:
  - `poetry run db-upgrade`
  - `poetry run db-revision -m "msg"`
  - `poetry run db-seed`
- Local idempotent-ish seed script `app/db/seed.py` creating demo school/students/invoices/payments
- UUIDv7 primary keys for School/Student/Invoice/Payment and UUID foreign keys across relationships
- Pydantic v2 schemas for School/Student/Invoice/Payment (Create/Update/Read) under `app/schemas/`
- Create schemas include only required fields; update schemas support partial updates (all fields optional)
- Read schemas include UUID ids, related entity ids, and timestamp fields (including `created_at`/`updated_at` placeholders to keep response shapes consistent)
- Schema validation enforces positive amounts for invoice totals and payment amounts (Decimal-based)
- DAL CRUD modules for school/student/invoice/payment with Session-injected functions
- DAL create/update functions refactored to single TypedDict payloads (`app/dal/_types.py`)
- DAL query helpers for statements: invoices-by-student(s), students-by-school, payments-by-invoice(s)
- Service layer business rules for payment-derived invoice math (`paid_total`, `balance_due`, `credit_amount`, `invoice_status`)
- Student and school statement services with Decimal totals and invoice-level derived fields
- Statement schemas under `app/schemas/statement.py` (`InvoiceSummary`, `StudentStatement`, `SchoolStatement`)
- Smoke tests verify metadata registration, FK indexing, relationships, DAL session usage, and schema validation without DB
- Smoke tests verify statement business rules and statement service aggregation using mocked DAL (no DB)
- FastAPI API routes wired for CRUD on `/schools`, `/students`, `/invoices`, `/payments` with offset/limit pagination and 404 handling
- Payments-by-invoice endpoint wired: `GET /invoices/{invoice_id}/payments` (returns payment list for a specific invoice)
- Statement endpoints wired to services: `GET /students/{student_id}/statement` and `GET /schools/{school_id}/statement`
- Demo JWT auth added: `POST /auth/login` issuing bearer token with `sub`, `role=admin`, `exp`
- Write endpoints (`POST/PATCH/DELETE`) for schools/students/invoices/payments now require admin bearer token; read endpoints remain public
- API smoke tests added with HTTPX `AsyncClient` for `/health`, auth/login, protected writes, and statement happy-path using monkeypatched DAL/services (no DB required)
- Smoke tests for DB CLI entrypoints added (alembic command invocation and seed transaction handling) with subprocess/session mocking
- Smoke test added to validate FastAPI skeleton wiring (`app.main.app` title + key routes) without DB access

## Pending
- See PLAN.md
