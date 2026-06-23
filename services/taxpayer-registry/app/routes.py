from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from . import db
from .models import (
    CandidateRecord,
    DeduplicateRequest,
    DeduplicateResponse,
    DuplicateGroup,
    Taxpayer,
)

router = APIRouter()


def _row_to_taxpayer(row) -> Taxpayer:
    fields = {
        "tin": row["tin"],
        "nid": row["nid"],
        "name": row["name"],
        "phone": row["phone"],
        "address": row["address"],
        "registered_on": row["registered_on"],
    }
    return Taxpayer(
        tin=row["tin"],
        nid=row["nid"],
        name=row["name"],
        phone=row["phone"],
        address=row["address"],
        registered_on=date.fromisoformat(row["registered_on"]),
        data_classification=Taxpayer.classify(fields),
    )


@router.get("/taxpayers/{tin}", response_model=Taxpayer, tags=["taxpayers"])
def get_taxpayer(tin: str) -> Taxpayer:
    with db.cursor() as cur:
        row = cur.execute("SELECT * FROM taxpayer WHERE tin = ?", (tin,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"taxpayer {tin} not found")
    return _row_to_taxpayer(row)


@router.get("/taxpayers", response_model=List[Taxpayer], tags=["taxpayers"])
def list_by_nid(
    nid: str = Query(..., pattern=r"^\d{10}$", description="10-digit synthetic NID"),
) -> List[Taxpayer]:
    with db.cursor() as cur:
        rows = cur.execute("SELECT * FROM taxpayer WHERE nid = ?", (nid,)).fetchall()
    return [_row_to_taxpayer(r) for r in rows]


_NAME_NORMALIZE = re.compile(r"[^a-z0-9]+")


def _name_key(name: str) -> str:
    return _NAME_NORMALIZE.sub("", name.lower())


def _phone_key(phone: str) -> str:
    """Normalise a phone string to its last 9 digits.

    Bangladesh mobile numbers are commonly written as +880-1XXXXXXXXX or
    01XXXXXXXXX. Both forms share the same trailing 9 digits, so taking the
    suffix matches local and international forms without parsing the country
    code.
    """
    digits = re.sub(r"\D", "", phone)
    return digits[-9:]


def _candidate_key(c: CandidateRecord) -> Optional[str]:
    """Group key for a candidate record.

    Priority:
      1. nid (strongest identity signal in this reference)
      2. normalised name + last-9-digits of phone

    Returns None if neither is available, in which case the record is treated
    as unique.
    """
    if c.nid:
        return f"nid:{c.nid}"
    if c.phone:
        return f"np:{_name_key(c.name)}:{_phone_key(c.phone)}"
    return None


@router.post(
    "/taxpayers/deduplicate",
    response_model=DeduplicateResponse,
    tags=["taxpayers"],
)
def deduplicate(req: DeduplicateRequest) -> DeduplicateResponse:
    groups: dict[str, list[CandidateRecord]] = defaultdict(list)
    singletons: list[CandidateRecord] = []
    for c in req.candidates:
        key = _candidate_key(c)
        if key is None:
            singletons.append(c)
        else:
            groups[key].append(c)

    duplicate_groups = [
        DuplicateGroup(key=k, members=members)
        for k, members in groups.items()
        if len(members) > 1
    ]
    unique_count = sum(1 for v in groups.values() if len(v) == 1) + len(singletons)
    duplicate_count = sum(len(g.members) for g in duplicate_groups)
    return DeduplicateResponse(
        groups=duplicate_groups,
        unique_count=unique_count,
        duplicate_count=duplicate_count,
    )
