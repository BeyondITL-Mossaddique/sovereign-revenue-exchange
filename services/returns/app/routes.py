from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, HTTPException, Query

from . import db
from .models import ReturnFigures, ReturnStatus, ReturnSubmission, TaxReturn

router = APIRouter()


def _row_to_return(row) -> TaxReturn:
    return TaxReturn(
        id=row["id"],
        tin=row["tin"],
        period=row["period"],
        figures=ReturnFigures(
            gross_income=Decimal(row["gross_income"]),
            deductions=Decimal(row["deductions"]),
            tax_payable=Decimal(row["tax_payable"]),
            currency=row["currency"],
        ),
        status=ReturnStatus(row["status"]),
        submitted_at=datetime.fromisoformat(row["submitted_at"].replace("Z", "+00:00")),
    )


@router.post("/returns", response_model=TaxReturn, status_code=201, tags=["returns"])
def submit_return(payload: ReturnSubmission) -> TaxReturn:
    rec = TaxReturn(
        id=f"R-{uuid.uuid4().hex[:8].upper()}",
        tin=payload.tin,
        period=payload.period,
        figures=payload.figures,
        status=ReturnStatus.submitted,
        submitted_at=datetime.now(timezone.utc),
    )
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO tax_return (id, tin, period, gross_income, deductions, "
                "tax_payable, currency, status, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    rec.id,
                    rec.tin,
                    rec.period,
                    str(rec.figures.gross_income),
                    str(rec.figures.deductions),
                    str(rec.figures.tax_payable),
                    rec.figures.currency,
                    rec.status.value,
                    rec.submitted_at.isoformat().replace("+00:00", "Z"),
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"a return for tin {rec.tin} period {rec.period} already exists",
        ) from exc
    return rec


@router.get("/returns/{return_id}", response_model=TaxReturn, tags=["returns"])
def get_return(return_id: str) -> TaxReturn:
    with db.cursor() as cur:
        row = cur.execute("SELECT * FROM tax_return WHERE id = ?", (return_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"return {return_id} not found")
    return _row_to_return(row)


@router.get("/returns", response_model=List[TaxReturn], tags=["returns"])
def list_returns_for_tin(
    tin: str = Query(..., description="9-digit TIN in the reserved test range"),
) -> List[TaxReturn]:
    with db.cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM tax_return WHERE tin = ? ORDER BY period DESC, submitted_at DESC",
            (tin,),
        ).fetchall()
    return [_row_to_return(r) for r in rows]
