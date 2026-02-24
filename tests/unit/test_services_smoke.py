from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from uuid_extensions import uuid7

from app.domain.dtos import InvoiceDTO, PaymentDTO, SchoolDTO, StudentDTO
from app.domain.enums import InvoiceStatus, PaymentKind
from app.domain.errors import ConflictError, DomainValidationError, NotFoundError
from app.services import billing_rules
from app.services import invoices as invoice_service
from app.services import payments as payment_service
from app.services.use_cases import GetSchoolStatement, GetStudentStatement, ListInvoicePayments


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeSchoolRepo:
    def __init__(self, schools: dict[UUID, SchoolDTO]) -> None:
        self.schools = schools

    async def get_by_id(self, school_id: UUID) -> SchoolDTO | None:
        return self.schools.get(school_id)


class FakeStudentRepo:
    def __init__(self, students: dict[UUID, StudentDTO], by_school: dict[UUID, list[StudentDTO]]) -> None:
        self.students = students
        self.by_school = by_school

    async def get_by_id(self, student_id: UUID) -> StudentDTO | None:
        return self.students.get(student_id)

    async def list_by_school_id(self, school_id: UUID, *, offset: int = 0, limit: int = 100) -> list[StudentDTO]:
        return self.by_school.get(school_id, [])[offset : offset + limit]


class FakeInvoiceRepo:
    def __init__(
        self,
        invoices_by_id: dict[UUID, InvoiceDTO],
        by_student: dict[UUID, list[InvoiceDTO]],
        by_students: dict[tuple[UUID, ...], list[InvoiceDTO]],
    ) -> None:
        self.invoices_by_id = invoices_by_id
        self.by_student = by_student
        self.by_students = by_students

    async def get_by_id(self, invoice_id: UUID) -> InvoiceDTO | None:
        return self.invoices_by_id.get(invoice_id)

    async def list_by_student_id(self, student_id: UUID) -> list[InvoiceDTO]:
        return self.by_student.get(student_id, [])

    async def list_by_student_ids(self, student_ids: list[UUID]) -> list[InvoiceDTO]:
        return self.by_students.get(tuple(student_ids), [])

    async def create(self, data: dict[str, object]) -> InvoiceDTO:
        invoice = InvoiceDTO(
            id=uuid7(),
            student_id=data["student_id"],
            total_amount=data["total_amount"],
            due_date=data["due_date"],
            issued_at=datetime(2026, 2, 1),
            description=data.get("description"),
            status=data["status"],
        )
        self.invoices_by_id[invoice.id] = invoice
        return invoice

    async def update(self, invoice_id: UUID, data: dict[str, object]) -> InvoiceDTO | None:
        current = self.invoices_by_id.get(invoice_id)
        if current is None:
            return None

        updated = InvoiceDTO(
            id=current.id,
            student_id=data.get("student_id", current.student_id),
            total_amount=data.get("total_amount", current.total_amount),
            due_date=data.get("due_date", current.due_date),
            issued_at=data.get("issued_at", current.issued_at),
            description=data.get("description", current.description),
            status=data.get("status", current.status),
        )
        self.invoices_by_id[invoice_id] = updated
        return updated


class FakePaymentRepo:
    def __init__(self, by_invoice: dict[UUID, list[PaymentDTO]]) -> None:
        self.by_invoice = by_invoice
        self.by_id: dict[UUID, PaymentDTO] = {}
        for payments in by_invoice.values():
            for payment in payments:
                self.by_id[payment.id] = payment

    async def list_by_invoice_id(self, invoice_id: UUID) -> list[PaymentDTO]:
        return list(self.by_invoice.get(invoice_id, []))

    async def list_by_invoice_ids(self, invoice_ids: list[UUID]) -> list[PaymentDTO]:
        payments: list[PaymentDTO] = []
        for invoice_id in invoice_ids:
            payments.extend(self.by_invoice.get(invoice_id, []))
        return payments

    async def create(self, data: dict[str, object]) -> PaymentDTO:
        payment = PaymentDTO(
            id=uuid7(),
            invoice_id=data["invoice_id"],
            amount=data["amount"],
            kind=data["kind"],
            paid_at=data.get("paid_at"),
            method=data.get("method"),
            reference=data.get("reference"),
        )
        self.by_invoice.setdefault(payment.invoice_id, []).append(payment)
        self.by_id[payment.id] = payment
        return payment

    async def get_by_id(self, payment_id: UUID) -> PaymentDTO | None:
        return self.by_id.get(payment_id)

    async def update(self, payment_id: UUID, data: dict[str, object]) -> PaymentDTO | None:
        current = self.by_id.get(payment_id)
        if current is None:
            return None

        old_list = self.by_invoice.get(current.invoice_id, [])
        self.by_invoice[current.invoice_id] = [item for item in old_list if item.id != payment_id]

        updated = PaymentDTO(
            id=current.id,
            invoice_id=data.get("invoice_id", current.invoice_id),
            amount=data.get("amount", current.amount),
            kind=data.get("kind", current.kind),
            paid_at=data.get("paid_at", current.paid_at),
            method=data.get("method", current.method),
            reference=data.get("reference", current.reference),
        )
        self.by_invoice.setdefault(updated.invoice_id, []).append(updated)
        self.by_id[payment_id] = updated
        return updated

    async def delete(self, payment_id: UUID) -> bool:
        current = self.by_id.pop(payment_id, None)
        if current is None:
            return False

        old_list = self.by_invoice.get(current.invoice_id, [])
        self.by_invoice[current.invoice_id] = [item for item in old_list if item.id != payment_id]
        return True


def _payment(payment_id: UUID, amount: str, invoice_id: UUID, kind: PaymentKind = PaymentKind.PAYMENT) -> PaymentDTO:
    return PaymentDTO(id=payment_id, invoice_id=invoice_id, amount=Decimal(amount), kind=kind, paid_at=None)


@pytest.mark.smoke
def test_business_rule_helpers_support_net_paid_and_three_statuses() -> None:
    invoice_id = uuid7()
    movements = [
        _payment(uuid7(), "80.00", invoice_id, PaymentKind.PAYMENT),
        _payment(uuid7(), "20.00", invoice_id, PaymentKind.REFUND),
    ]

    net_paid = billing_rules.paid_total(movements)
    assert net_paid == Decimal("60.00")
    assert billing_rules.balance_due(Decimal("100.00"), movements) == Decimal("40.00")
    assert billing_rules.invoice_status(Decimal("100.00"), Decimal("0.00")) == InvoiceStatus.PENDING
    assert billing_rules.invoice_status(Decimal("100.00"), Decimal("60.00")) == InvoiceStatus.PARTIAL
    assert billing_rules.invoice_status(Decimal("100.00"), Decimal("100.00")) == InvoiceStatus.PAID


@pytest.mark.smoke
@pytest.mark.anyio
async def test_get_student_statement_use_case_aggregates_net_totals() -> None:
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
            status=InvoiceStatus.PARTIAL,
        ),
        InvoiceDTO(
            id=invoice_2_id,
            student_id=student_id,
            total_amount=Decimal("50.00"),
            due_date=date(2026, 4, 1),
            issued_at=datetime(2026, 3, 1),
            description="Materials",
            status=InvoiceStatus.PAID,
        ),
    ]
    payment_repo = FakePaymentRepo(
        by_invoice={
            invoice_1_id: [
                _payment(uuid7(), "60.00", invoice_1_id),
                _payment(uuid7(), "10.00", invoice_1_id, PaymentKind.REFUND),
            ],
            invoice_2_id: [_payment(uuid7(), "50.00", invoice_2_id)],
        }
    )
    use_case = GetStudentStatement(
        student_repo=FakeStudentRepo(students={student_id: student}, by_school={}),
        invoice_repo=FakeInvoiceRepo(invoices_by_id={}, by_student={student_id: invoices}, by_students={}),
        payment_repo=payment_repo,
    )

    statement = await use_case(student_id)

    assert statement.student_id == student_id
    assert statement.school_id == school_id
    assert statement.totals.invoiced_total == Decimal("150.00")
    assert statement.totals.paid_total == Decimal("100.00")
    assert statement.totals.balance_due_total == Decimal("50.00")
    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PARTIAL, InvoiceStatus.PAID]


@pytest.mark.smoke
@pytest.mark.anyio
async def test_get_school_statement_use_case_aggregates_across_students() -> None:
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
            status=InvoiceStatus.PARTIAL,
        ),
        InvoiceDTO(
            id=invoice_2_id,
            student_id=student_2_id,
            total_amount=Decimal("120.00"),
            due_date=date(2026, 3, 15),
            issued_at=datetime(2026, 2, 15),
            status=InvoiceStatus.PAID,
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

    statement = await use_case(school_id)

    assert statement.school_id == school_id
    assert statement.students_count == 2
    assert statement.totals.invoiced_total == Decimal("200.00")
    assert statement.totals.paid_total == Decimal("140.00")
    assert statement.totals.balance_due_total == Decimal("60.00")
    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PARTIAL, InvoiceStatus.PAID]


@pytest.mark.smoke
@pytest.mark.anyio
async def test_use_cases_raise_not_found_for_missing_entities() -> None:
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
        await student_statement_uc(missing_id)

    with pytest.raises(NotFoundError):
        await school_statement_uc(missing_id)

    with pytest.raises(NotFoundError):
        await invoice_payments_uc(missing_id)


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_and_refund_updates_persisted_invoice_status() -> None:
    invoice_id = uuid7()
    student_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={
            invoice_id: InvoiceDTO(
                id=invoice_id,
                student_id=student_id,
                total_amount=Decimal("100.00"),
                due_date=date(2026, 3, 1),
                issued_at=datetime(2026, 2, 1),
                status=InvoiceStatus.PENDING,
            )
        },
        by_student={},
        by_students={},
    )
    payment_repo = FakePaymentRepo(by_invoice={})

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("40.00"), "kind": PaymentKind.PAYMENT},
    )
    assert invoice_repo.invoices_by_id[invoice_id].status == InvoiceStatus.PARTIAL

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("60.00"), "kind": PaymentKind.PAYMENT},
    )
    assert invoice_repo.invoices_by_id[invoice_id].status == InvoiceStatus.PAID

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("25.00"), "kind": PaymentKind.REFUND},
    )
    assert invoice_repo.invoices_by_id[invoice_id].status == InvoiceStatus.PARTIAL


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_rejects_overpayment() -> None:
    invoice_id = uuid7()
    student_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={
            invoice_id: InvoiceDTO(
                id=invoice_id,
                student_id=student_id,
                total_amount=Decimal("50.00"),
                due_date=date(2026, 3, 1),
                issued_at=datetime(2026, 2, 1),
                status=InvoiceStatus.PENDING,
            )
        },
        by_student={},
        by_students={},
    )
    payment_repo = FakePaymentRepo(by_invoice={})

    with pytest.raises(ConflictError, match="exceeds invoice total"):
        await payment_service.create_payment(
            payment_repo,
            invoice_repo,
            data={"invoice_id": invoice_id, "amount": Decimal("60.00"), "kind": PaymentKind.PAYMENT},
        )


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_rejects_over_refund() -> None:
    invoice_id = uuid7()
    student_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={
            invoice_id: InvoiceDTO(
                id=invoice_id,
                student_id=student_id,
                total_amount=Decimal("50.00"),
                due_date=date(2026, 3, 1),
                issued_at=datetime(2026, 2, 1),
                status=InvoiceStatus.PENDING,
            )
        },
        by_student={},
        by_students={},
    )
    payment_repo = FakePaymentRepo(
        by_invoice={invoice_id: [_payment(uuid7(), "20.00", invoice_id, PaymentKind.PAYMENT)]}
    )

    with pytest.raises(ConflictError, match="Refund exceeds"):
        await payment_service.create_payment(
            payment_repo,
            invoice_repo,
            data={"invoice_id": invoice_id, "amount": Decimal("25.00"), "kind": PaymentKind.REFUND},
        )


@pytest.mark.smoke
@pytest.mark.anyio
async def test_invoice_create_defaults_to_pending_status() -> None:
    invoice_repo = FakeInvoiceRepo(invoices_by_id={}, by_student={}, by_students={})

    created = await invoice_service.create_invoice(
        invoice_repo,
        data={
            "student_id": uuid7(),
            "total_amount": Decimal("100.00"),
            "due_date": date(2026, 3, 1),
        },
    )

    assert created.status == InvoiceStatus.PENDING


@pytest.mark.smoke
@pytest.mark.anyio
async def test_invoice_total_update_recomputes_status_and_rejects_invalid_total() -> None:
    invoice_id = uuid7()
    student_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={
            invoice_id: InvoiceDTO(
                id=invoice_id,
                student_id=student_id,
                total_amount=Decimal("100.00"),
                due_date=date(2026, 3, 1),
                issued_at=datetime(2026, 2, 1),
                status=InvoiceStatus.PAID,
            )
        },
        by_student={},
        by_students={},
    )
    payment_repo = FakePaymentRepo(
        by_invoice={invoice_id: [_payment(uuid7(), "60.00", invoice_id), _payment(uuid7(), "40.00", invoice_id)]}
    )

    updated = await invoice_service.update_invoice(
        invoice_repo,
        payment_repo,
        invoice_id,
        {"total_amount": Decimal("120.00")},
    )
    assert updated.status == InvoiceStatus.PARTIAL

    with pytest.raises(ConflictError, match="cannot be below net paid"):
        await invoice_service.update_invoice(
            invoice_repo,
            payment_repo,
            invoice_id,
            {"total_amount": Decimal("90.00")},
        )


@pytest.mark.smoke
@pytest.mark.anyio
async def test_update_payment_rejects_null_kind() -> None:
    invoice_id = uuid7()
    payment_id = uuid7()
    student_id = uuid7()
    payment_repo = FakePaymentRepo(
        by_invoice={invoice_id: [_payment(payment_id, "10.00", invoice_id, PaymentKind.PAYMENT)]}
    )
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={
            invoice_id: InvoiceDTO(
                id=invoice_id,
                student_id=student_id,
                total_amount=Decimal("50.00"),
                due_date=date(2026, 3, 1),
                issued_at=datetime(2026, 2, 1),
                status=InvoiceStatus.PARTIAL,
            )
        },
        by_student={},
        by_students={},
    )

    with pytest.raises(DomainValidationError, match="cannot be null"):
        await payment_service.update_payment(payment_repo, invoice_repo, payment_id=payment_id, data={"kind": None})
