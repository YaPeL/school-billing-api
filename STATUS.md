# STATUS

## Running
- Install:
  - poetry install
  - pre-commit install
- Run (local):
  - docker compose up -d db
  - poetry run uvicorn app.main:app --reload
- Run (docker):
  - docker compose up --build
- Tests:
  - poetry run pytest -m smoke
  - poetry run pytest -m "smoke or integration" (optional)

## Implemented
- Bootstrap project structure
- Settings + logging middleware
- /health, /health/db, /metrics
- SQLAlchemy typed ORM models for School/Student/Invoice/Payment with FK indexes and relationships
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

## Pending
- See PLAN.md
