Add persisted invoice status + refund support (typed payment movements) across DB, domain, services, and API.

Goal:
- Persist `invoice.status` in the database (not only computed at read time)
- Support refunds without introducing a CREDIT status
- Keep only 3 invoice statuses: `PENDING`, `PARTIAL`, `PAID`
- Prevent overpayment and over-refund via service-level validation
- Update API schemas/routes/tests/migrations/seed accordingly

Business rules:
1) Invoice status values:
   - PENDING
   - PARTIAL
   - PAID

2) Payment rows become typed money movements:
   - PAYMENT: adds money to invoice
   - REFUND: subtracts money from invoice
   - `amount` is always positive (no negative amounts in API/DB)

3) Net paid amount for an invoice:
   - sum(PAYMENT amounts) - sum(REFUND amounts)

4) Validations:
   - net_paid must NEVER exceed invoice.total_amount (no credit allowed)
   - net_paid must NEVER go below 0 (cannot refund more than paid)
   - if validation fails, return a clean API error (422 or 409, pick one and use consistently)

5) Persisted invoice.status must be updated whenever:
   - invoice is created (default should be PENDING)
   - payment/refund is created
   - payment/refund is updated
   - payment/refund is deleted
   - invoice total_amount is updated (recompute status)

Implementation requirements:

## 1) Domain / enums
- Add or update domain enums:
  - `InvoiceStatus` with PENDING, PARTIAL, PAID
  - `PaymentKind` with PAYMENT, REFUND
- Reuse enums consistently in models, schemas, and services
- Remove any `CREDIT` references from code/tests/docs

## 2) Database models (SQLAlchemy)
- Invoice model:
  - add `status` column (string or SQLAlchemy Enum)
  - non-null
  - default `PENDING`
- Payment model:
  - add `kind` column (string or SQLAlchemy Enum)
  - non-null
  - default `PAYMENT`
- Keep `amount` positive in app validation (DB check optional but nice to have)
- Do not break UUID usage

## 3) Alembic migration
Create a migration that:
- adds `invoices.status`
- backfills existing invoices status based on current payments (for demo/simple migration, acceptable to:
  - set PENDING first
  - then recompute from payments in Python/SQL if practical
  - if too complex, document and set PENDING for old rows, but prefer proper backfill)
- adds `payments.kind` with default PAYMENT for existing rows
- makes new columns non-null
- migration must be safe for local dev db

## 4) Schemas (Pydantic)
Update schemas:
- `InvoiceRead` includes `status`
- `PaymentCreate` includes optional `kind` (default PAYMENT)
- `PaymentRead` includes `kind`
- `PaymentUpdate` can update `kind` if needed (or explicitly forbid if you want simpler behavior; choose one and document)
- Ensure amount validation remains > 0
- Remove schema-level references to CREDIT in statements/status enums

## 5) Services (business logic)
Centralize invoice status recomputation logic in service layer.

Add service helpers (or a dedicated billing service) to:
- compute net paid from a list of payments/refunds
- derive invoice status from `invoice.total_amount` and `net_paid`
- validate no overpayment / no over-refund
- persist updated status on invoice

Important:
- Write endpoints should go through services (not routers -> DAL directly)
- Services should raise domain exceptions (not HTTPException)
- Reuse existing global exception handler pattern

Recommended flow for create payment/refund:
1. load invoice
2. load existing payments for invoice
3. simulate net_paid after new movement
4. validate bounds [0, total_amount]
5. create payment row
6. recompute and persist invoice.status
7. return created payment

Do the same for payment update and delete:
- recalc based on resulting set of movements
- update invoice.status

For invoice total update:
- if total_amount changes, recompute status using existing movements
- reject if new total would make state invalid (e.g., paid > total and credit is not allowed)

## 6) DAL updates
- DAL functions can stay sync (do NOT convert to async in this task)
- Add needed DAL queries:
  - list payments by invoice id (already exists)
  - get invoice by id
  - update invoice status
- Keep DAL focused on persistence only
- No HTTP concerns in DAL

## 7) API routes
- Keep current routes, but `POST /payments` now supports `kind`
- No separate `/refunds` route required (refunds are `POST /payments` with `kind=REFUND`)
- Return clear errors for invalid operations:
  - overpayment
  - over-refund
  - invoice not found
  - payment not found

## 8) Statement behavior
- Statements should still work, but update calculations:
  - paid_total in statement should represent NET paid (payments - refunds)
- Since CREDIT is removed:
  - remove credit-related fields/status if still present
  - if statement schema still has `credit_amount`, remove it and update callers/tests/docs
- Status in statement should match persisted invoice.status (or same derivation logic)

## 9) Seeds
Update seed data to reflect the new model:
- include `kind` for payments (PAYMENT)
- optionally include a small REFUND example to demonstrate behavior
- keep seed idempotent-ish

## 10) Tests (smoke)
Update/add smoke tests for:
- invoice status defaults to PENDING on create
- creating PAYMENT updates status:
  - PENDING -> PARTIAL
  - PARTIAL -> PAID
- creating REFUND updates status:
  - PAID -> PARTIAL or PENDING depending on amount
- overpayment is rejected
- over-refund is rejected
- API payloads include `status` on invoices and `kind` on payments
- statement tests updated to no longer expect CREDIT behavior

Constraints:
- Keep code style and architecture consistent with current repo
- Do not introduce async DB in this task
- ruff + mypy + pytest -m smoke must pass
- Update README / DECISIONS / TODO only where needed (briefly)

Notes for Codex:
- Prefer small, safe diffs
- Do not rework the whole architecture
- Focus on correctness and consistency
- 