from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


TIN_MIN = 900_000_001
TIN_MAX = 999_999_999

# Period in the form YYYY-Q1..Q4 (quarterly) or YYYY (annual). Synthetic only.
PERIOD_PATTERN = re.compile(r"^\d{4}(-Q[1-4])?$")


class ReturnStatus(str, Enum):
    submitted = "submitted"
    accepted = "accepted"
    rejected = "rejected"


class ReturnFigures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gross_income: Decimal = Field(ge=0, decimal_places=2)
    deductions: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tax_payable: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(default="BDT", min_length=3, max_length=3)


class ReturnSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tin: str = Field(description="9-digit TIN in the reserved test range")
    period: str = Field(description="YYYY or YYYY-Q1..Q4")
    figures: ReturnFigures

    @field_validator("tin")
    @classmethod
    def _tin_in_test_range(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 9:
            raise ValueError("TIN must be a 9-digit numeric string")
        n = int(v)
        if not (TIN_MIN <= n <= TIN_MAX):
            raise ValueError(
                f"TIN must be in the reserved test range {TIN_MIN}-{TIN_MAX}"
            )
        return v

    @field_validator("period")
    @classmethod
    def _period_shape(cls, v: str) -> str:
        if not PERIOD_PATTERN.match(v):
            raise ValueError("period must be YYYY or YYYY-Q1..Q4")
        return v


class TaxReturn(ReturnSubmission):
    id: str
    status: ReturnStatus
    submitted_at: datetime
