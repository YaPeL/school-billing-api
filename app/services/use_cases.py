from __future__ import annotations

from uuid import UUID

from app.api.constants import INVOICES, SCHOOLS, STUDENTS
from app.domain.dtos import PaymentDTO
from app.domain.errors import NotFoundError
from app.schemas.statement import SchoolStatement, StudentStatement
from app.services.ports import InvoiceRepo, PaymentRepo, SchoolRepo, StudentRepo
from app.services.statements import build_school_statement, build_student_statement


class GetStudentStatement:
    def __init__(self, student_repo: StudentRepo, invoice_repo: InvoiceRepo, payment_repo: PaymentRepo) -> None:
        self._student_repo = student_repo
        self._invoice_repo = invoice_repo
        self._payment_repo = payment_repo

    def __call__(self, student_id: UUID) -> StudentStatement:
        student = self._student_repo.get_by_id(student_id)
        if student is None:
            raise NotFoundError(STUDENTS, str(student_id))

        invoices = self._invoice_repo.list_by_student_id(student.id)
        invoice_ids = [invoice.id for invoice in invoices]
        payments = self._payment_repo.list_by_invoice_ids(invoice_ids)
        return build_student_statement(student, invoices, payments)


class GetSchoolStatement:
    def __init__(
        self,
        school_repo: SchoolRepo,
        student_repo: StudentRepo,
        invoice_repo: InvoiceRepo,
        payment_repo: PaymentRepo,
    ) -> None:
        self._school_repo = school_repo
        self._student_repo = student_repo
        self._invoice_repo = invoice_repo
        self._payment_repo = payment_repo

    def __call__(self, school_id: UUID) -> SchoolStatement:
        school = self._school_repo.get_by_id(school_id)
        if school is None:
            raise NotFoundError(SCHOOLS, str(school_id))

        students = self._student_repo.list_by_school_id(school.id)
        student_ids = [student.id for student in students]
        invoices = self._invoice_repo.list_by_student_ids(student_ids)
        invoice_ids = [invoice.id for invoice in invoices]
        payments = self._payment_repo.list_by_invoice_ids(invoice_ids)
        return build_school_statement(school, students, invoices, payments)


class ListInvoicePayments:
    def __init__(self, invoice_repo: InvoiceRepo, payment_repo: PaymentRepo) -> None:
        self._invoice_repo = invoice_repo
        self._payment_repo = payment_repo

    def __call__(self, invoice_id: UUID) -> list[PaymentDTO]:
        invoice = self._invoice_repo.get_by_id(invoice_id)
        if invoice is None:
            raise NotFoundError(INVOICES, str(invoice_id))
        return self._payment_repo.list_by_invoice_id(invoice_id)
