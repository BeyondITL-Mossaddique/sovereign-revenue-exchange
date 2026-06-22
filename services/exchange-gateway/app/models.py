from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaxpayerSummary(BaseModel):
    tin: str
    nid: str
    name: str
    registered_on: date


class ReturnSummary(BaseModel):
    id: str
    period: str
    status: str
    tax_payable: str  # kept as string to avoid decimal precision drift in JSON
    currency: str


class TaxpayerProfile(BaseModel):
    taxpayer: TaxpayerSummary
    returns: List[ReturnSummary]
    served_to_agency: Optional[str] = Field(
        default=None,
        description="Echo of the requesting agency header, recorded in the audit trail",
    )


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tin: str
    period: str
    claimed_status: str = Field(description="Status the requester claims, e.g. 'accepted'")


class VerifyResponse(BaseModel):
    tin: str
    period: str
    verified: bool
    actual_status: Optional[str]
    served_to_agency: Optional[str]
    checked_at: datetime
