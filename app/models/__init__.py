from app.db.base import Base

# Import models so SQLAlchemy registers them in Base.metadata
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.school import School
from app.models.student import Student

__all__ = [
    "Base",
    "School",
    "Student",
    "Invoice",
    "Payment",
]
