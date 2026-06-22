from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional

from .config import Settings, get_settings
from .models import (
    ReturnSummary,
    TaxpayerProfile,
    TaxpayerSummary,
    VerifyRequest,
    VerifyResponse,
)
from .upstream import fetch_returns_for_tin, fetch_taxpayer

router = APIRouter(prefix="/exchange", tags=["exchange"])


def _agency_header(
    settings: Settings = Depends(get_settings),
    x_requesting_agency: Optional[str] = Header(default=None, alias="X-Requesting-Agency"),
) -> Optional[str]:
    # The header name is configurable, but FastAPI resolves it from the alias;
    # we expose `settings` here so downstream code can record the configured
    # header name in the audit field rather than the literal alias.
    return x_requesting_agency


@router.get("/taxpayer-profile/{tin}", response_model=TaxpayerProfile)
async def taxpayer_profile(
    tin: str,
    settings: Settings = Depends(get_settings),
    requesting_agency: Optional[str] = Depends(_agency_header),
) -> TaxpayerProfile:
    taxpayer_data = await fetch_taxpayer(settings, tin)
    if taxpayer_data is None:
        raise HTTPException(status_code=404, detail=f"taxpayer {tin} not found")
    returns_data = await fetch_returns_for_tin(settings, tin)

    return TaxpayerProfile(
        taxpayer=TaxpayerSummary(
            tin=taxpayer_data["tin"],
            nid=taxpayer_data["nid"],
            name=taxpayer_data["name"],
            registered_on=date.fromisoformat(taxpayer_data["registered_on"]),
        ),
        returns=[
            ReturnSummary(
                id=r["id"],
                period=r["period"],
                status=r["status"],
                tax_payable=str(r["figures"]["tax_payable"]),
                currency=r["figures"]["currency"],
            )
            for r in returns_data
        ],
        served_to_agency=requesting_agency,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    payload: VerifyRequest,
    settings: Settings = Depends(get_settings),
    requesting_agency: Optional[str] = Depends(_agency_header),
) -> VerifyResponse:
    taxpayer_data = await fetch_taxpayer(settings, payload.tin)
    if taxpayer_data is None:
        raise HTTPException(status_code=404, detail=f"taxpayer {payload.tin} not found")

    returns_data = await fetch_returns_for_tin(settings, payload.tin)
    match = next((r for r in returns_data if r["period"] == payload.period), None)
    actual = match["status"] if match else None

    return VerifyResponse(
        tin=payload.tin,
        period=payload.period,
        verified=(actual is not None and actual == payload.claimed_status),
        actual_status=actual,
        served_to_agency=requesting_agency,
        checked_at=datetime.now(timezone.utc),
    )
