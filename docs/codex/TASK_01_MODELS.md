Implement PLAN item: "ORM models: School, Student, Invoice, Payment + relationships + constraints".

Requirements:
- SQLAlchemy 2.0 typed ORM (Mapped, mapped_column)
- Create app/db/base.py with declarative Base
- Create models:
  - School
  - Student (FK school_id)
  - Invoice (FK student_id, total_amount as Numeric(12,2), issued_at, due_date, description optional)
  - Payment (FK invoice_id, amount Numeric(12,2), paid_at, method optional, reference optional)
- Add indexes on foreign keys.
- Relationships:
  - School.students
  - Student.invoices
  - Invoice.payments
- Do NOT add endpoints yet.
- Keep code passing ruff + mypy.
- Update PLAN.md and STATUS.md accordingly.
