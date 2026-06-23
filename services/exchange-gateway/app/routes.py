from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from . import rules
from .config import Settings, get_settings
from .models import (
    AccessLogEntry,
    ReturnSummary,
    TaxComputationSummary,
    TaxpayerProfile,
    TaxpayerSummary,
    VerifyRequest,
    VerifyResponse,
)
from .upstream import (
    fetch_returns_for_tin,
    fetch_taxpayer,
    fetch_taxpayers_by_nid,
)

router = APIRouter(prefix="/exchange", tags=["exchange"])


def _agency_header(
    settings: Settings = Depends(get_settings),
    x_requesting_agency: Optional[str] = Header(default=None, alias="X-Requesting-Agency"),
) -> Optional[str]:
    # The header name is configurable, but FastAPI resolves it from the alias;
    # we expose `settings` here so downstream code can record the configured
    # header name in the audit field rather than the literal alias.
    return x_requesting_agency


def _computation_from_upstream(raw: Optional[dict]) -> Optional[TaxComputationSummary]:
    if not raw:
        return None
    return TaxComputationSummary(
        taxable_income=str(raw["taxable_income"]),
        threshold=str(raw["threshold"]),
        computed_tax=str(raw["computed_tax"]),
        no_tax_due=bool(raw["no_tax_due"]),
        minimum_tax_applied=bool(raw["minimum_tax_applied"]),
        filer_category=str(raw["filer_category"]),
    )


@router.get("/taxpayer-profile/{tin}", response_model=TaxpayerProfile)
async def taxpayer_profile(
    tin: str,
    settings: Settings = Depends(get_settings),
    requesting_agency: Optional[str] = Depends(_agency_header),
) -> TaxpayerProfile:
    taxpayer_data = await fetch_taxpayer(settings, tin)
    if taxpayer_data is None:
        rules.record_access(
            agency=requesting_agency,
            method="GET",
            path=f"/exchange/taxpayer-profile/{tin}",
            status_code=404,
            target_tin=tin,
        )
        raise HTTPException(status_code=404, detail=f"taxpayer {tin} not found")
    returns_data = await fetch_returns_for_tin(settings, tin)

    profile = TaxpayerProfile(
        taxpayer=TaxpayerSummary(
            tin=taxpayer_data["tin"],
            nid=taxpayer_data["nid"],
            name=taxpayer_data["name"],
            registered_on=date.fromisoformat(taxpayer_data["registered_on"]),
            data_classification=taxpayer_data.get("data_classification", "Restricted"),
        ),
        returns=[
            ReturnSummary(
                id=r["id"],
                period=r["period"],
                status=r["status"],
                tax_payable=str(r["figures"]["tax_payable"]),
                currency=r["figures"]["currency"],
                late_filing=bool(r.get("late_filing", False)),
                computed=_computation_from_upstream(r.get("computed")),
            )
            for r in returns_data
        ],
        served_to_agency=requesting_agency,
    )
    rules.record_access(
        agency=requesting_agency,
        method="GET",
        path=f"/exchange/taxpayer-profile/{tin}",
        status_code=200,
        target_tin=tin,
    )
    return profile


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    payload: VerifyRequest,
    settings: Settings = Depends(get_settings),
    requesting_agency: Optional[str] = Depends(_agency_header),
) -> VerifyResponse:
    taxpayer_data = await fetch_taxpayer(settings, payload.tin)
    if taxpayer_data is None:
        rules.record_access(
            agency=requesting_agency,
            method="POST",
            path="/exchange/verify",
            status_code=404,
            target_tin=payload.tin,
        )
        raise HTTPException(status_code=404, detail=f"taxpayer {payload.tin} not found")

    returns_data = await fetch_returns_for_tin(settings, payload.tin)
    match = next((r for r in returns_data if r["period"] == payload.period), None)
    actual = match["status"] if match else None

    response = VerifyResponse(
        tin=payload.tin,
        period=payload.period,
        verified=(actual is not None and actual == payload.claimed_status),
        actual_status=actual,
        served_to_agency=requesting_agency,
        checked_at=datetime.now(timezone.utc),
    )
    rules.record_access(
        agency=requesting_agency,
        method="POST",
        path="/exchange/verify",
        status_code=200,
        target_tin=payload.tin,
    )
    return response


@router.get("/access-log", response_model=List[AccessLogEntry])
def access_log(
    limit: int = Query(default=50, ge=1, le=200),
) -> List[AccessLogEntry]:
    """Most-recent-first slice of the gateway audit trail."""
    return rules.recent(limit=limit)


@router.get("/duplicates/by-nid/{nid}", response_model=List[TaxpayerSummary])
async def duplicates_by_nid(
    nid: str,
    settings: Settings = Depends(get_settings),
    requesting_agency: Optional[str] = Depends(_agency_header),
) -> List[TaxpayerSummary]:
    """Taxpayer records sharing the given NID.

    A list of length > 1 is the seeded duplicate pair (or whatever the
    registry now reports). The dashboard renders the collapse from this list.
    """
    rows = await fetch_taxpayers_by_nid(settings, nid)
    rules.record_access(
        agency=requesting_agency,
        method="GET",
        path=f"/exchange/duplicates/by-nid/{nid}",
        status_code=200,
    )
    return [
        TaxpayerSummary(
            tin=row["tin"],
            nid=row["nid"],
            name=row["name"],
            registered_on=date.fromisoformat(row["registered_on"]),
            data_classification=row.get("data_classification", "Restricted"),
        )
        for row in rows
    ]
