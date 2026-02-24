Implement PLAN item: "DAL functions (only layer touching Session)".

Requirements:
- Create app/dal modules:
  - school.py, student.py, invoice.py, payment.py
- Provide minimal CRUD functions:
  - create_*, get_*_by_id, list_* (with pagination params optional), update_*, delete_*
- DAL functions must accept a SQLAlchemy Session as argument.
- No business logic in DAL (no statement totals, no status derivation).
- Do NOT add endpoints yet.
- Keep code passing ruff + mypy.
- Update PLAN.md and STATUS.md accordingly.
