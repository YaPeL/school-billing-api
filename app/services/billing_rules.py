from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Protocol

from app.domain.enums import InvoiceStatus, PaymentKind
from app.domain.errors import ConflictError

ZERO = Decimal("0.00")


class SupportsMovement(Protocol):
    @property
    def amount(self) -> Decimal: ...

    @property
    def kind(self) -> PaymentKind: ...


def net_paid_total(movements: Iterable[SupportsMovement]) -> Decimal:
    total = ZERO
    for movement in movements:
        if movement.kind == PaymentKind.REFUND:
            total -= movement.amount
            continue
        total += movement.amount
    return total


def movement_delta(kind: PaymentKind, amount: Decimal) -> Decimal:
    if kind == PaymentKind.REFUND:
        return -amount
    return amount


def balance_due(invoice_total: Decimal, net_paid: Decimal) -> Decimal:
    return invoice_total - net_paid


def derive_invoice_status(invoice_total: Decimal, net_paid: Decimal) -> InvoiceStatus:
    if net_paid == ZERO:
        return InvoiceStatus.PENDING
    if net_paid < invoice_total:
        return InvoiceStatus.PARTIAL
    return InvoiceStatus.PAID


def validate_net_paid_bounds(invoice_total: Decimal, net_paid: Decimal) -> None:
    if net_paid < ZERO:
        raise ConflictError("Refund exceeds collected amount for this invoice")
    if net_paid > invoice_total:
        raise ConflictError("Payment exceeds invoice total amount")
