from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Protocol

from app.domain.enums import InvoiceStatus

ZERO = Decimal("0.00")


class SupportsAmount(Protocol):
    amount: Decimal


def paid_total(payments: Iterable[SupportsAmount]) -> Decimal:
    return sum((payment.amount for payment in payments), start=ZERO)


def balance_due(invoice_total: Decimal, payments: Iterable[SupportsAmount]) -> Decimal:
    return invoice_total - paid_total(payments)


def credit_amount(invoice_total: Decimal, payments: Iterable[SupportsAmount]) -> Decimal:
    credit = paid_total(payments) - invoice_total
    return max(credit, ZERO)


def invoice_status(invoice_total: Decimal, payments: Iterable[SupportsAmount]) -> InvoiceStatus:
    paid = paid_total(payments)
    if paid == ZERO:
        return InvoiceStatus.PENDING
    if paid < invoice_total:
        return InvoiceStatus.PARTIAL
    if paid == invoice_total:
        return InvoiceStatus.PAID
    return InvoiceStatus.CREDIT
