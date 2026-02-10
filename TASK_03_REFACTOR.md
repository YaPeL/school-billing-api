Refactor to align with DECISIONS.md:

1) Primary keys must use UUIDv7 (not int autoincrement) for:
- School, Student, Invoice, Payment
Update all foreign keys and relationships accordingly.

2) DAL create functions must not take many positional params.
Refactor create_* signatures to accept a single structured object:
- Use TypedDict (app/dal/_types.py) for create/update inputs for now.
- Keep DAL as the only layer touching Session.
- Do not introduce FastAPI schemas yet.

3) Update/adjust existing smoke tests:
- Ensure metadata tables still registered
- Ensure FK columns still indexed
- Ensure relationships exist
If any tests are low-signal, keep them minimal but passing.

Constraints:
- Keep ruff + mypy + pytest -m smoke passing.
- Do not add endpoints.
- Update PLAN.md and STATUS.md accordingly.
