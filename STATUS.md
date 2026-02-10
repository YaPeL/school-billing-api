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
- DAL CRUD modules for school/student/invoice/payment with Session-injected functions
- DAL create/update functions refactored to single TypedDict payloads (`app/dal/_types.py`)
- Smoke tests verify metadata registration, FK indexing, relationships, and DAL session usage without DB

## Pending
- See PLAN.md
