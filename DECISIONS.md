# DECISIONS

- Payments are first-class: invoices can have multiple payments (partial payments supported).
- Invoice status is derived from payments (PENDING/PARTIAL/PAID).
- DAL is the only layer touching SQLAlchemy Session; services mock DAL in smoke tests.
- Auth is demo-basic JWT with a role claim (admin). No user table unless needed.
- Observability is free and simple: structured logs, /health, /health/db, /metrics.
