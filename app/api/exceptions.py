from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NotFoundError(Exception):
    resource: str
    identifier: str | None = None

    def message(self) -> str:
        if self.identifier:
            return f"{self.resource} {self.identifier} not found"
        return f"{self.resource} not found"
