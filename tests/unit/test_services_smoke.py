from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from uuid_extensions import uuid7

from app.domain.dtos import InvoiceDTO, PaymentDTO, SchoolDTO, StudentDTO
from app.domain.enums import InvoiceStatus
from app.domain.errors import NotFoundError
from app.services import billing_rules
from app.services.use_cases import GetSchoolStatement, GetStudentStatement, ListInvoicePayments


class FakeSchoolRepo:
    def __init__(self, schools: dict[object, SchoolDTO]) -> None:
        self.schools = schools

    def get_by_id(self, school_id: object) -> SchoolDTO | None:
        return self.schools.get(school_id)


class FakeStudentRepo:
    def __init__(self, students: dict[object, StudentDTO], by_school: dict[object, list[StudentDTO]]) -> None:
        self.students = students
        self.by_school = by_school

    def get_by_id(self, student_id: object) -> StudentDTO | None:
        return self.students.get(student_id)

    def list_by_school_id(self, school_id: object, *, offset: int = 0, limit: int = 100) -> list[StudentDTO]:
        return self.by_school.get(school_id, [])[offset : offset + limit]


class FakeInvoiceRepo:
    def __init__(
        self,
        invoices_by_id: dict[object, InvoiceDTO],
        by_student: dict[object, list[InvoiceDTO]],
        by_students: dict[tuple[object, ...], list[InvoiceDTO]],
    ) -> None:
        self.invoices_by_id = invoices_by_id
        self.by_student = by_student
        self.by_students = by_students

    def get_by_id(self, invoice_id: object) -> InvoiceDTO | None:
        return self.invoices_by_id.get(invoice_id)

    def list_by_student_id(self, student_id: object) -> list[InvoiceDTO]:
        return self.by_student.get(student_id, [])

    def list_by_student_ids(self, student_ids: list[object]) -> list[InvoiceDTO]:
        return self.by_students.get(tuple(student_ids), [])


class FakePaymentRepo:
    def __init__(self, by_invoice: dict[object, list[PaymentDTO]]) -> None:
        self.by_invoice = by_invoice

    def list_by_invoice_id(self, invoice_id: object) -> list[PaymentDTO]:
        return self.by_invoice.get(invoice_id, [])

    def list_by_invoice_ids(self, invoice_ids: list[object]) -> list[PaymentDTO]:
        payments: list[PaymentDTO] = []
        for invoice_id in invoice_ids:
            payments.extend(self.by_invoice.get(invoice_id, []))
        return payments


def _payment(payment_id: object, amount: str, invoice_id: object) -> PaymentDTO:
    return PaymentDTO(id=payment_id, invoice_id=invoice_id, amount=Decimal(amount), paid_at=None)


@pytest.mark.smoke
def test_business_rule_helpers_support_partial_paid_and_credit() -> None:
    invoice_id = uuid7()
    payments = [_payment(uuid7(), "40.00", invoice_id), _payment(uuid7(), "30.00", invoice_id)]

    assert billing_rules.paid_total(payments) == Decimal("70.00")
    assert billing_rules.balance_due(Decimal("100.00"), payments) == Decimal("30.00")
    assert billing_rules.credit_amount(Decimal("50.00"), payments) == Decimal("20.00")
    assert billing_rules.invoice_status(Decimal("100.00"), payments) == InvoiceStatus.PARTIAL
    assert billing_rules.invoice_status(Decimal("70.00"), payments) == InvoiceStatus.PAID
    assert billing_rules.invoice_status(Decimal("50.00"), payments) == InvoiceStatus.CREDIT
    assert billing_rules.invoice_status(Decimal("100.00"), []) == InvoiceStatus.PENDING


@pytest.mark.smoke
def test_get_student_statement_use_case_aggregates_totals() -> None:
    school_id = uuid7()
    student_id = uuid7()
    invoice_1_id = uuid7()
    invoice_2_id = uuid7()

    student = StudentDTO(id=student_id, school_id=school_id, full_name="Ada Lovelace")
    invoices = [
        InvoiceDTO(
            id=invoice_1_id,
            student_id=student_id,
            total_amount=Decimal("100.00"),
            due_date=date(2026, 3, 1),
            issued_at=datetime(2026, 2, 1),
            description="March tuition",
        ),
        InvoiceDTO(
            id=invoice_2_id,
            student_id=student_id,
            total_amount=Decimal("50.00"),
            due_date=date(2026, 4, 1),
            issued_at=datetime(2026, 3, 1),
            description="Materials",
        ),
    ]
    payment_repo = FakePaymentRepo(
        by_invoice={
            invoice_1_id: [_payment(uuid7(), "60.00", invoice_1_id), _payment(uuid7(), "40.00", invoice_1_id)],
            invoice_2_id: [_payment(uuid7(), "70.00", invoice_2_id)],
        }
    )
    use_case = GetStudentStatement(
        student_repo=FakeStudentRepo(students={student_id: student}, by_school={}),
        invoice_repo=FakeInvoiceRepo(invoices_by_id={}, by_student={student_id: invoices}, by_students={}),
        payment_repo=payment_repo,
    )

    statement = use_case(student_id)

    assert statement.student_id == student_id
    assert statement.school_id == school_id
    assert statement.totals.invoiced_total == Decimal("150.00")
    assert statement.totals.paid_total == Decimal("170.00")
    assert statement.totals.balance_due_total == Decimal("-20.00")
    assert statement.totals.credit_total == Decimal("20.00")
    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PAID, InvoiceStatus.CREDIT]


@pytest.mark.smoke
def test_get_school_statement_use_case_aggregates_across_students() -> None:
    school_id = uuid7()
    student_1_id = uuid7()
    student_2_id = uuid7()
    invoice_1_id = uuid7()
    invoice_2_id = uuid7()

    school = SchoolDTO(id=school_id, name="STEM Academy")
    students = [
        StudentDTO(id=student_1_id, school_id=school_id, full_name="Grace Hopper"),
        StudentDTO(id=student_2_id, school_id=school_id, full_name="Alan Turing"),
    ]
    invoices = [
        InvoiceDTO(
            id=invoice_1_id,
            student_id=student_1_id,
            total_amount=Decimal("80.00"),
            due_date=date(2026, 3, 10),
            issued_at=datetime(2026, 2, 10),
        ),
        InvoiceDTO(
            id=invoice_2_id,
            student_id=student_2_id,
            total_amount=Decimal("120.00"),
            due_date=date(2026, 3, 15),
            issued_at=datetime(2026, 2, 15),
        ),
    ]
    payment_repo = FakePaymentRepo(
        by_invoice={
            invoice_1_id: [_payment(uuid7(), "20.00", invoice_1_id)],
            invoice_2_id: [_payment(uuid7(), "120.00", invoice_2_id)],
        }
    )

    use_case = GetSchoolStatement(
        school_repo=FakeSchoolRepo(schools={school_id: school}),
        student_repo=FakeStudentRepo(students={}, by_school={school_id: students}),
        invoice_repo=FakeInvoiceRepo(
            invoices_by_id={}, by_student={}, by_students={(student_1_id, student_2_id): invoices}
        ),
        payment_repo=payment_repo,
    )

    statement = use_case(school_id)

    assert statement.school_id == school_id
    assert statement.students_count == 2
    assert statement.totals.invoiced_total == Decimal("200.00")
    assert statement.totals.paid_total == Decimal("140.00")
    assert statement.totals.balance_due_total == Decimal("60.00")
    assert statement.totals.credit_total == Decimal("0.00")
    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PARTIAL, InvoiceStatus.PAID]


@pytest.mark.smoke
def test_use_cases_raise_not_found_for_missing_entities() -> None:
    missing_id = uuid7()

    student_statement_uc = GetStudentStatement(
        student_repo=FakeStudentRepo(students={}, by_school={}),
        invoice_repo=FakeInvoiceRepo(invoices_by_id={}, by_student={}, by_students={}),
        payment_repo=FakePaymentRepo(by_invoice={}),
    )

    school_statement_uc = GetSchoolStatement(
        school_repo=FakeSchoolRepo(schools={}),
        student_repo=FakeStudentRepo(students={}, by_school={}),
        invoice_repo=FakeInvoiceRepo(invoices_by_id={}, by_student={}, by_students={}),
        payment_repo=FakePaymentRepo(by_invoice={}),
    )

    invoice_payments_uc = ListInvoicePayments(
        invoice_repo=FakeInvoiceRepo(invoices_by_id={}, by_student={}, by_students={}),
        payment_repo=FakePaymentRepo(by_invoice={}),
    )

    with pytest.raises(NotFoundError):
        student_statement_uc(missing_id)

    with pytest.raises(NotFoundError):
        school_statement_uc(missing_id)

    with pytest.raises(NotFoundError):
        invoice_payments_uc(missing_id)
