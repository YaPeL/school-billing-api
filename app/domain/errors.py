from __future__ import annotations


class DomainError(Exception):
    def message(self) -> str:
        return str(self)


class NotFoundError(DomainError):
    def __init__(self, entity: str, key: str) -> None:
        self.entity = entity
        self.key = key
        super().__init__(f"{entity} {key} not found")


class ConflictError(DomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)
