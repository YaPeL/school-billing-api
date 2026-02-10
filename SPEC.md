# SPEC

## Goal
Build a small backend that models:
- Schools
- Students
- Invoices
- Payments

The system must be able to answer:
- how much a student owes to a school
- how much all students owe to a school
- how many students a school has
- account statement for a school and for a student
- track partial and full payments per invoice (audit-friendly)

## Scope

### Data model & persistence
- Entities: School, Student, Invoice, Payment
- Relationships:
  - Student belongs to a School
  - Invoice belongs to a Student
  - Payment belongs to an Invoice (one invoice can have many payments)
- ORM: SQLAlchemy 2.0
- Migrations are optional (nice to have)

### Business rules
- Invoice totals:
  - paid_total = sum(payments.amount)
  - balance = total_amount - paid_total
- Invoice status can be derived:
  - PENDING if paid_total == 0
  - PARTIAL if 0 < paid_total < total_amount
  - PAID if paid_total >= total_amount

### API (FastAPI)
Minimum endpoints:
- CRUD Schools
- CRUD Students
- CRUD Invoices
- CRUD Payments (at least create + list by invoice, delete optional)
- Student statement endpoint:
  - totals (invoiced/paid/due) + invoices with balances and payment summaries
- School statement endpoint:
  - totals + student breakdown (optional) + invoices summary

Swagger/OpenAPI docs should be available.

## Technical requirements
- Python + FastAPI
- PostgreSQL via Docker Compose
- Poetry for dependencies
- Tests with pytest
- pre-commit with ruff, mypy, and pytest (smoke)
- README with instructions to run the project, run tests, and optionally load sample data

## Nice-to-haves (optional)
- Pagination
- Basic auth/authorization (JWT)
- Simple observability: logs, metrics, health checks
- Local tracing with OpenTelemetry (no paid services)
