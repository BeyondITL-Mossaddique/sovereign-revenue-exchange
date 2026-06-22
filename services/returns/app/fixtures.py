"""Synthetic seed returns for the reference. Values are obviously round."""
from __future__ import annotations

from .db import connect

SEED: list[tuple[str, str, str, str, str, str, str, str, str]] = [
    # id,    tin,         period,    gross,     ded,      tax,      ccy,   status,     submitted_at
    ("R001", "900000001", "2024",    "1200000.00", "150000.00", "120000.00", "BDT", "accepted", "2025-01-15T09:30:00Z"),
    ("R002", "900000001", "2023",    "1100000.00", "140000.00", "110000.00", "BDT", "accepted", "2024-01-12T10:05:00Z"),
    ("R003", "900000002", "2024",    "900000.00",  "80000.00",  "82000.00",  "BDT", "submitted","2025-02-10T14:20:00Z"),
    ("R004", "900000003", "2024",    "1500000.00", "200000.00", "150000.00", "BDT", "accepted", "2025-01-20T11:00:00Z"),
    ("R005", "900000010", "2024-Q1", "450000.00",  "50000.00",  "45000.00",  "BDT", "accepted", "2025-04-05T08:45:00Z"),
    ("R006", "900000010", "2024-Q2", "470000.00",  "55000.00",  "47000.00",  "BDT", "accepted", "2025-07-05T08:50:00Z"),
]


def seed_if_empty() -> int:
    with connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM tax_return").fetchone()
        if count > 0:
            return 0
        conn.executemany(
            "INSERT INTO tax_return (id, tin, period, gross_income, deductions, "
            "tax_payable, currency, status, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            SEED,
        )
        conn.commit()
        return len(SEED)
