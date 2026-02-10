Implement PLAN item: "API routes: CRUD + statements (wire schemas + services)".

Scope:
- Add FastAPI routers for:
  - /schools
  - /students
  - /invoices
  - /payments
  - /statements (or nested endpoints, see below)
- Wire routers into app/main.py.

Endpoints (minimum):
Schools
- POST /schools -> SchoolRead
- GET /schools?offset=&limit= -> list[SchoolRead]
- GET /schools/{school_id} -> SchoolRead
- PATCH /schools/{school_id} -> SchoolRead
- DELETE /schools/{school_id} -> 204

Students
- POST /students -> StudentRead
- GET /students?offset=&limit= -> list[StudentRead]
- GET /students/{student_id} -> StudentRead
- PATCH /students/{student_id} -> StudentRead
- DELETE /students/{student_id} -> 204

Invoices
- POST /invoices -> InvoiceRead
- GET /invoices?offset=&limit= -> list[InvoiceRead]
- GET /invoices/{invoice_id} -> InvoiceRead
- PATCH /invoices/{invoice_id} -> InvoiceRead
- DELETE /invoices/{invoice_id} -> 204

Payments
- POST /payments -> PaymentRead
- GET /payments?offset=&limit= -> list[PaymentRead]
- GET /payments/{payment_id} -> PaymentRead
- PATCH /payments/{payment_id} -> PaymentRead
- DELETE /payments/{payment_id} -> 204

Statements (use services from Task 05)
- GET /students/{student_id}/statement -> StudentStatement
- GET /schools/{school_id}/statement -> SchoolStatement

Rules:
- Use dependencies to get a DB session (from app/db/session.py).
- Use schemas from app/schemas.
- Use DAL for CRUD routes; use services for statement routes.
- Proper HTTP errors:
  - 404 when entity not found
  - 422 handled by FastAPI/Pydantic
- Keep responses consistent (Read schemas).
- Add pagination params (offset/limit) to list endpoints.

Testing (smoke):
- Add 2-4 smoke tests using FastAPI TestClient:
  - /health ok
  - one CRUD happy-path can be mocked (monkeypatch DAL) to avoid DB
  - statement endpoint happy-path mocked (monkeypatch services)
- Do NOT require a real DB in smoke tests.

Constraints:
- ruff + mypy + pytest -m smoke must pass.
- No auth yet (that is Task 07).
- Update PLAN.md and STATUS.md accordingly.
