# DECISIONS

- Payments are first-class: invoices can have multiple payments (partial payments supported).
- Invoice status is derived from payments; overpaid invoices use `CREDIT` status (PENDING/PARTIAL/PAID/CREDIT).
- DAL is the only layer touching SQLAlchemy Session; services mock DAL in smoke tests.
- Primary keys for School/Student/Invoice/Payment use UUIDv7; all related foreign keys are UUID.
- DAL create/update inputs use TypedDict payloads instead of multiple positional/keyword parameters.
- Auth is demo-basic JWT with a role claim (admin). No user table unless needed.
- Observability is free and simple: structured logs, /health, /health/db, /metrics.
- API smoke tests for HTTP routes use `TestClient`; on Python 3.13 they are skip-guarded because the current FastAPI/Starlette/AnyIO stack hangs in this environment.
