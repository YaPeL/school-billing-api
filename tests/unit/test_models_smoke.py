import pytest
from sqlalchemy import inspect as sa_inspect

from app.db.base import Base
from app.models import Invoice, Payment, School, Student


@pytest.mark.smoke
def test_tables_registered_in_metadata() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert {"schools", "students", "invoices", "payments"}.issubset(table_names)


@pytest.mark.smoke
def test_foreign_keys_have_indexes() -> None:
    assert Student.__table__.c.school_id.index is True
    assert Invoice.__table__.c.student_id.index is True
    assert Payment.__table__.c.invoice_id.index is True


@pytest.mark.smoke
def test_required_relationships_exist() -> None:
    assert "students" in sa_inspect(School).relationships
    assert "invoices" in sa_inspect(Student).relationships
    assert "payments" in sa_inspect(Invoice).relationships
