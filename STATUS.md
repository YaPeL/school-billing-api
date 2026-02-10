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
- Smoke tests verify metadata registration, FK indexing, relationships, DAL session usage, and schema validation without DB

## Pending
- See PLAN.md
