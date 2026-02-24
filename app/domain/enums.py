from enum import StrEnum


class InvoiceStatus(StrEnum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"


class PaymentKind(StrEnum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
