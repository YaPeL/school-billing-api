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
  - export TEST_DATABASE_URL=postgresql+psycopg://school_billing:school_billing@localhost:5432/school_billing_test
  - poetry run pytest -m integration (optional, real DB)
- CI:
  - GitHub Actions workflow on push/PR to `main` (Python 3.12, ruff, mypy, smoke)

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
- DAL create/update functions refactored to single TypedDict payloads (`app/dal/update_types.py`)
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
- GitHub Actions CI workflow added at `.github/workflows/ci.yml` (Python 3.12 only, Poetry install, ruff, mypy, smoke tests)
- README polished with CI/type-check/tests badges, clearer quickstart, and bearer-auth examples for protected endpoints
- Smoke test added to verify CI workflow quality gates exist (`tests/unit/test_ci_smoke.py`)
- Integration test suite scaffolded under `tests/integration/` with real-PostgreSQL setup/skip logic and a statement flow test covering PENDING/PARTIAL/PAID/CREDIT status derivation from persisted payments
- Integration DB safety hardened: tests now require `TEST_DATABASE_URL` and skip unless URL points to a local, explicitly test-named database before any destructive TRUNCATE
- Branding cleanup completed: defaults/config/docs now use neutral `school-billing` / `school_billing` naming
- Architecture refactor completed to a lightweight ports+adapters shape:
  - Domain DTOs + domain errors under `app/domain/`
  - Repo protocols in `app/services/ports.py`
  - SQLAlchemy repo adapters in `app/dal/repos/`
  - Statement and invoice-payment listing moved to explicit use-cases with dependency wiring in `app/api/deps.py`
  - Global domain exception registration centralized in `app/api/exception_handlers.py`
- DB-backed route handlers in `app/api/schools.py`, `app/api/students.py`, `app/api/invoices.py`, and `app/api/payments.py` are synchronous (`def`), ensuring sync SQLAlchemy work runs in FastAPI's threadpool instead of the event loop

## Pending
- Statement caching design: define what to cache and invalidation strategy when invoices/payments change
