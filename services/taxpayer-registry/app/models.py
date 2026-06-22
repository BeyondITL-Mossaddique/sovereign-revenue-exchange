from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# TINs in this reference are 9-digit numeric strings in a reserved test range.
# Real-world TINs are not in this range and will be rejected.
TIN_MIN = 900_000_001
TIN_MAX = 999_999_999

# NIDs are synthetic 10-digit numeric strings.
NID_PATTERN = r"^\d{10}$"


def is_test_tin(tin: str) -> bool:
    if not tin.isdigit() or len(tin) != 9:
        return False
    n = int(tin)
    return TIN_MIN <= n <= TIN_MAX


class Taxpayer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tin: str = Field(description="9-digit TIN in the reserved test range 900000001–999999999")
    nid: str = Field(pattern=NID_PATTERN, description="10-digit synthetic National ID")
    name: str = Field(min_length=1, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=200)
    registered_on: date

    @field_validator("tin")
    @classmethod
    def _tin_in_test_range(cls, v: str) -> str:
        if not is_test_tin(v):
            raise ValueError(
                "TIN must be a 9-digit numeric string in the reserved test range "
                f"{TIN_MIN}-{TIN_MAX}"
            )
        return v


class CandidateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tin: Optional[str] = None
    nid: Optional[str] = None
    name: str
    phone: Optional[str] = None


class DuplicateGroup(BaseModel):
    key: str = Field(description="Stable group key derived from nid or normalised name+phone")
    members: List[CandidateRecord]


class DeduplicateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: List[CandidateRecord]


class DeduplicateResponse(BaseModel):
    groups: List[DuplicateGroup]
    unique_count: int
    duplicate_count: int
