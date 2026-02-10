Implement PLAN item: "Services: business rules (invoice balances, statements)".

Architecture:
- Routers (later) -> Services (app/services) -> DAL (app/dal)
- DAL is the only layer touching Session. Services must not import SessionLocal.

Scope:
1) Add pure business rule helpers (no DB):
- paid_total(payments) -> Decimal
- balance_due(invoice_total, payments) -> Decimal (can be negative if overpaid)
- credit_amount(invoice_total, payments) -> Decimal (>= 0)
- invoice_status(invoice_total, payments) -> Enum-like str:
  - PENDING (paid_total == 0)
  - PARTIAL (0 < paid_total < total)
  - PAID (paid_total == total)
  - CREDIT (paid_total > total)

2) Add service functions that use DAL:
- get_student_statement(student_id):
  - fetch student (and school if needed) via DAL
  - fetch invoices for student via DAL
  - fetch payments per invoice via DAL (bulk if available, otherwise per invoice)
  - return a statement object (Pydantic schema) with:
    - totals: invoiced_total, paid_total, balance_due_total, credit_total
    - invoices: list with invoice fields + derived fields (paid_total, balance_due, credit_amount, status)
    - payments: optionally nested under invoice or summarized

- get_school_statement(school_id):
  - fetch school
  - fetch students for school
  - fetch invoices for those students
  - fetch payments for those invoices
  - compute totals at school level (same totals)
  - optionally include per-student breakdown (keep minimal)

3) Create statement schemas:
- app/schemas/statement.py with:
  - InvoiceSummary (invoice read + derived fields)
  - StudentStatement
  - SchoolStatement

Testing (smoke, fast, no DB):
- Write smoke tests for pure helper functions (status/balance/credit).
- Write smoke tests for statement services by mocking DAL functions:
  - Use monkeypatch or unittest.mock to make DAL return deterministic objects
  - Validate totals and per-invoice derived fields
- Ensure tests do NOT touch a real database.

Constraints:
- Use Decimal everywhere for amounts.
- Keep ruff + mypy + pytest -m smoke passing.
- Do NOT add API routes yet.
- Update PLAN.md and STATUS.md accordingly.

Notes:
- Overpayments are allowed: balance_due may be negative, credit_amount positive.
- If you add any new DAL helpers (e.g., list_invoices_by_student_id), keep them in DAL.
