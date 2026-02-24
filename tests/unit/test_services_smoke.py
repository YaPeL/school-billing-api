from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from uuid_extensions import uuid7

from app.domain.dtos import InvoiceDTO, PaymentDTO, SchoolDTO, StudentDTO
from app.domain.enums import InvoiceStatus, PaymentKind
from app.domain.errors import ConflictError, NotFoundError
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
        by_student: dict[UUID, list[InvoiceDTO]] | None = None,
        by_students: dict[tuple[UUID, ...], list[InvoiceDTO]] | None = None,
    ) -> None:
        self.invoices_by_id = invoices_by_id
        self.by_student = by_student or {}
        self.by_students = by_students or {}

    async def create(self, data: Mapping[str, object]) -> InvoiceDTO:
        invoice = InvoiceDTO(
            id=uuid7(),
            student_id=data["student_id"],  # type: ignore[arg-type]
            total_amount=data["total_amount"],  # type: ignore[arg-type]
            due_date=data["due_date"],  # type: ignore[arg-type]
            issued_at=datetime(2026, 1, 1),
            status=data["status"],  # type: ignore[arg-type]
            description=data.get("description"),  # type: ignore[arg-type]
        )
        self.invoices_by_id[invoice.id] = invoice
        return invoice

    async def get_by_id(self, invoice_id: UUID) -> InvoiceDTO | None:
        return self.invoices_by_id.get(invoice_id)

    async def update(self, invoice_id: UUID, data: Mapping[str, object]) -> InvoiceDTO | None:
        invoice = self.invoices_by_id.get(invoice_id)
        if invoice is None:
            return None
        updated = replace(
            invoice,
            student_id=data.get("student_id", invoice.student_id),  # type: ignore[arg-type]
            total_amount=data.get("total_amount", invoice.total_amount),  # type: ignore[arg-type]
            due_date=data.get("due_date", invoice.due_date),  # type: ignore[arg-type]
            status=data.get("status", invoice.status),  # type: ignore[arg-type]
            description=data.get("description", invoice.description),  # type: ignore[arg-type]
        )
        self.invoices_by_id[invoice_id] = updated
        return updated

    async def list_by_student_id(self, student_id: UUID) -> list[InvoiceDTO]:
        return self.by_student.get(student_id, [])

    async def list_by_student_ids(self, student_ids: Sequence[UUID]) -> list[InvoiceDTO]:
        return self.by_students.get(tuple(student_ids), [])


class FakePaymentRepo:
    def __init__(self, by_invoice: dict[UUID, list[PaymentDTO]]) -> None:
        self.by_invoice = by_invoice
        self.by_id: dict[UUID, PaymentDTO] = {}
        for invoice_payments in by_invoice.values():
            for payment in invoice_payments:
                self.by_id[payment.id] = payment

    async def create(self, data: Mapping[str, object]) -> PaymentDTO:
        payment = PaymentDTO(
            id=uuid7(),
            invoice_id=data["invoice_id"],  # type: ignore[arg-type]
            amount=data["amount"],  # type: ignore[arg-type]
            kind=data.get("kind", PaymentKind.PAYMENT),  # type: ignore[arg-type]
        )
        self.by_invoice.setdefault(payment.invoice_id, []).append(payment)
        self.by_id[payment.id] = payment
        return payment

    async def get_by_id(self, payment_id: UUID) -> PaymentDTO | None:
        return self.by_id.get(payment_id)

    async def update(self, payment_id: UUID, data: Mapping[str, object]) -> PaymentDTO | None:
        current = self.by_id.get(payment_id)
        if current is None:
            return None
        updated = replace(
            current,
            invoice_id=data.get("invoice_id", current.invoice_id),  # type: ignore[arg-type]
            amount=data.get("amount", current.amount),  # type: ignore[arg-type]
            kind=data.get("kind", current.kind),  # type: ignore[arg-type]
        )
        self.by_invoice[current.invoice_id] = [
            p for p in self.by_invoice.get(current.invoice_id, []) if p.id != payment_id
        ]
        self.by_invoice.setdefault(updated.invoice_id, []).append(updated)
        self.by_id[payment_id] = updated
        return updated

    async def delete(self, payment_id: UUID) -> bool:
        payment = self.by_id.pop(payment_id, None)
        if payment is None:
            return False
        self.by_invoice[payment.invoice_id] = [
            candidate for candidate in self.by_invoice.get(payment.invoice_id, []) if candidate.id != payment_id
        ]
        return True

    async def list_by_invoice_id(self, invoice_id: UUID) -> list[PaymentDTO]:
        return list(self.by_invoice.get(invoice_id, []))

    async def list_by_invoice_ids(self, invoice_ids: Sequence[UUID]) -> list[PaymentDTO]:
        payments: list[PaymentDTO] = []
        for invoice_id in invoice_ids:
            payments.extend(self.by_invoice.get(invoice_id, []))
        return payments


def _payment(payment_id: UUID, amount: str, invoice_id: UUID, kind: PaymentKind = PaymentKind.PAYMENT) -> PaymentDTO:
    return PaymentDTO(id=payment_id, invoice_id=invoice_id, amount=Decimal(amount), kind=kind, paid_at=None)


def _invoice(invoice_id: UUID, student_id: UUID, total_amount: str, status: InvoiceStatus) -> InvoiceDTO:
    return InvoiceDTO(
        id=invoice_id,
        student_id=student_id,
        total_amount=Decimal(total_amount),
        due_date=date(2026, 3, 1),
        issued_at=datetime(2026, 2, 1),
        description="Invoice",
        status=status,
    )


@pytest.mark.smoke
def test_business_rule_helpers_support_net_paid_and_three_statuses() -> None:
    invoice_id = uuid7()
    movements = [
        _payment(uuid7(), "40.00", invoice_id, PaymentKind.PAYMENT),
        _payment(uuid7(), "10.00", invoice_id, PaymentKind.REFUND),
    ]

    assert billing_rules.payments_total(movements) == Decimal("40.00")
    assert billing_rules.refunds_total(movements) == Decimal("10.00")
    net_paid = billing_rules.net_paid_total(movements)
    assert net_paid == Decimal("30.00")
    assert billing_rules.balance_due(Decimal("100.00"), net_paid) == Decimal("70.00")
    assert billing_rules.derive_invoice_status(Decimal("100.00"), net_paid) == InvoiceStatus.PARTIAL
    assert billing_rules.derive_invoice_status(Decimal("30.00"), net_paid) == InvoiceStatus.PAID
    assert billing_rules.derive_invoice_status(Decimal("20.00"), net_paid) == InvoiceStatus.PAID


@pytest.mark.smoke
@pytest.mark.anyio
async def test_invoice_create_defaults_status_pending() -> None:
    student_id = uuid7()
    invoice_repo = FakeInvoiceRepo(invoices_by_id={})

    invoice = await invoice_service.create_invoice(
        invoice_repo,
        data={"student_id": student_id, "total_amount": Decimal("100.00"), "due_date": date(2026, 3, 1)},
    )

    assert invoice.status == InvoiceStatus.PENDING


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_transitions_status_pending_to_partial_to_paid() -> None:
    student_id = uuid7()
    invoice_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={invoice_id: _invoice(invoice_id, student_id, "100.00", InvoiceStatus.PENDING)}
    )
    payment_repo = FakePaymentRepo(by_invoice={})

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("30.00"), "kind": PaymentKind.PAYMENT},
    )
    assert (await invoice_repo.get_by_id(invoice_id)).status == InvoiceStatus.PARTIAL  # type: ignore[union-attr]

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("70.00"), "kind": PaymentKind.PAYMENT},
    )
    assert (await invoice_repo.get_by_id(invoice_id)).status == InvoiceStatus.PAID  # type: ignore[union-attr]


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_refund_transitions_status_paid_to_partial_to_pending() -> None:
    student_id = uuid7()
    invoice_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={invoice_id: _invoice(invoice_id, student_id, "100.00", InvoiceStatus.PAID)}
    )
    payment_repo = FakePaymentRepo(
        by_invoice={invoice_id: [_payment(uuid7(), "100.00", invoice_id, PaymentKind.PAYMENT)]}
    )

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("40.00"), "kind": PaymentKind.REFUND},
    )
    assert (await invoice_repo.get_by_id(invoice_id)).status == InvoiceStatus.PARTIAL  # type: ignore[union-attr]

    await payment_service.create_payment(
        payment_repo,
        invoice_repo,
        data={"invoice_id": invoice_id, "amount": Decimal("60.00"), "kind": PaymentKind.REFUND},
    )
    assert (await invoice_repo.get_by_id(invoice_id)).status == InvoiceStatus.PENDING  # type: ignore[union-attr]


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_rejects_overpayment() -> None:
    student_id = uuid7()
    invoice_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={invoice_id: _invoice(invoice_id, student_id, "100.00", InvoiceStatus.PENDING)}
    )
    payment_repo = FakePaymentRepo(by_invoice={})

    with pytest.raises(ConflictError, match="payment amount exceeds remaining balance"):
        await payment_service.create_payment(
            payment_repo,
            invoice_repo,
            data={"invoice_id": invoice_id, "amount": Decimal("101.00"), "kind": PaymentKind.PAYMENT},
        )


@pytest.mark.smoke
@pytest.mark.anyio
async def test_create_payment_rejects_over_refund() -> None:
    student_id = uuid7()
    invoice_id = uuid7()
    invoice_repo = FakeInvoiceRepo(
        invoices_by_id={invoice_id: _invoice(invoice_id, student_id, "100.00", InvoiceStatus.PARTIAL)}
    )
    payment_repo = FakePaymentRepo(
        by_invoice={invoice_id: [_payment(uuid7(), "50.00", invoice_id, PaymentKind.PAYMENT)]}
    )

    with pytest.raises(ConflictError, match="refund amount exceeds net paid amount"):
        await payment_service.create_payment(
            payment_repo,
            invoice_repo,
            data={"invoice_id": invoice_id, "amount": Decimal("60.00"), "kind": PaymentKind.REFUND},
        )


@pytest.mark.smoke
@pytest.mark.anyio
async def test_get_student_statement_use_case_aggregates_net_paid_totals() -> None:
    school_id = uuid7()
    student_id = uuid7()
    invoice_1_id = uuid7()
    invoice_2_id = uuid7()

    student = StudentDTO(id=student_id, school_id=school_id, full_name="Ada Lovelace")
    invoices = [
        _invoice(invoice_1_id, student_id, "100.00", InvoiceStatus.PAID),
        _invoice(invoice_2_id, student_id, "50.00", InvoiceStatus.PARTIAL),
    ]
    payment_repo = FakePaymentRepo(
        by_invoice={
            invoice_1_id: [_payment(uuid7(), "100.00", invoice_1_id, PaymentKind.PAYMENT)],
            invoice_2_id: [
                _payment(uuid7(), "40.00", invoice_2_id, PaymentKind.PAYMENT),
                _payment(uuid7(), "10.00", invoice_2_id, PaymentKind.REFUND),
            ],
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
    assert statement.totals.payments_total == Decimal("140.00")
    assert statement.totals.refunds_total == Decimal("10.00")
    assert statement.totals.paid_total == Decimal("130.00")
    assert statement.totals.balance_due_total == Decimal("20.00")
    assert statement.invoices[1].payments_total == Decimal("40.00")
    assert statement.invoices[1].refunds_total == Decimal("10.00")
    assert [inv.status for inv in statement.invoices] == [InvoiceStatus.PAID, InvoiceStatus.PARTIAL]


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
        _invoice(invoice_1_id, student_1_id, "80.00", InvoiceStatus.PARTIAL),
        _invoice(invoice_2_id, student_2_id, "120.00", InvoiceStatus.PAID),
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
    assert statement.totals.payments_total == Decimal("140.00")
    assert statement.totals.refunds_total == Decimal("0.00")
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
