from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Protocol

from app.domain.enums import InvoiceStatus, PaymentKind

ZERO = Decimal("0.00")


class SupportsMovement(Protocol):
    @property
    def amount(self) -> Decimal: ...

    @property
    def kind(self) -> PaymentKind: ...


def _signed_amount(amount: Decimal, kind: PaymentKind) -> Decimal:
    return amount if kind == PaymentKind.PAYMENT else -amount


def paid_total(payments: Iterable[SupportsMovement]) -> Decimal:
    return sum((_signed_amount(payment.amount, payment.kind) for payment in payments), start=ZERO)


def balance_due(invoice_total: Decimal, payments: Iterable[SupportsMovement]) -> Decimal:
    return invoice_total - paid_total(payments)


def invoice_status(invoice_total: Decimal, net_paid: Decimal) -> InvoiceStatus:
    if net_paid == ZERO:
        return InvoiceStatus.PENDING
    if net_paid < invoice_total:
        return InvoiceStatus.PARTIAL
    return InvoiceStatus.PAID
