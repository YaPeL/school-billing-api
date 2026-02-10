from enum import StrEnum


class InvoiceStatus(StrEnum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    CREDIT = "CREDIT"
