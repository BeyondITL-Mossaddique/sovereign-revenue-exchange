from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaxpayerSummary(BaseModel):
    tin: str
    nid: str
    name: str
    registered_on: date
    data_classification: str = "Restricted"


class TaxComputationSummary(BaseModel):
    taxable_income: str
    threshold: str
    computed_tax: str
    no_tax_due: bool
    minimum_tax_applied: bool
    filer_category: str


class ReturnSummary(BaseModel):
    id: str
    period: str
    status: str
    tax_payable: str  # kept as string to avoid decimal precision drift in JSON
    currency: str
    late_filing: bool = False
    computed: Optional[TaxComputationSummary] = None


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


class AccessLogEntry(BaseModel):
    """One audited gateway call.

    Identifies what was requested, by which agency, and when. No payload is
    stored — this is an access trail, not a copy of the data.
    """

    at: datetime
    agency: Optional[str]
    method: str
    path: str
    target_tin: Optional[str] = None
    status_code: int
