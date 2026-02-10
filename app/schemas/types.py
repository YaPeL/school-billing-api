from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import Field

PositiveAmount = Annotated[Decimal, Field(gt=0)]
