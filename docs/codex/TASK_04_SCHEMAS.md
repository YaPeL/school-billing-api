Implement PLAN item: "Pydantic schemas (create/update/read) for all entities".

Scope:
- Add Pydantic schemas for:
  - School
  - Student
  - Invoice
  - Payment
- Place them under app/schemas/ (one file per entity).
- Keep DAL and models unchanged.

Requirements:
- Use Pydantic v2 style.
- Amounts must be Decimal (not float).
- Create/Update/Read schemas:
  - Create: required fields only
  - Update: all optional fields (partial updates)
  - Read: include id fields (UUID), timestamps, and nested IDs where relevant
- Use UUID types for ids.
- Add minimal validations:
  - Invoice.total_amount > 0
  - Payment.amount > 0
- Keep schema names consistent:
  - SchoolCreate, SchoolUpdate, SchoolRead
  - StudentCreate, StudentUpdate, StudentRead
  - InvoiceCreate, InvoiceUpdate, InvoiceRead
  - PaymentCreate, PaymentUpdate, PaymentRead

Extra (optional but nice):
- Add a shared base schema config (e.g., from_attributes = True for Read models).

Testing:
- Add 2-4 smoke tests that validate schema validation behavior:
  - rejects negative/zero amounts
  - accepts valid payloads
No DB access in tests.

Constraints:
- Ensure ruff + mypy + pytest -m smoke pass.
- Do NOT add API routes yet.
- Update PLAN.md and STATUS.md accordingly.
