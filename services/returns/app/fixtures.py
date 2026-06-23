"""Synthetic seed returns for the reference. Values are obviously round.

Covers a mix of individuals (yearly periods) and companies (quarterly periods),
multiple statuses (accepted, submitted, rejected), and at least one taxpayer
with two filings across years so the dashboard's history view has something to
render.
"""
from __future__ import annotations

from .db import connect

SEED: list[tuple[str, str, str, str, str, str, str, str, str]] = [
    # id,    tin,             period,    gross,        ded,         tax,         ccy,   status,     submitted_at
    # Two filings for TIN 001 — drives the multi-period history demo.
    ("R001", "900000000001", "2024",    "1200000.00", "150000.00", "120000.00", "BDT", "accepted", "2025-01-15T09:30:00Z"),
    ("R002", "900000000001", "2023",    "1100000.00", "140000.00", "110000.00", "BDT", "accepted", "2024-01-12T10:05:00Z"),
    # Single submitted filing pending review.
    ("R003", "900000000002", "2024",    "900000.00",  "80000.00",  "82000.00",  "BDT", "submitted","2025-02-10T14:20:00Z"),
    ("R004", "900000000003", "2024",    "1500000.00", "200000.00", "150000.00", "BDT", "accepted", "2025-01-20T11:00:00Z"),
    # Entity 010 — quarterly filings.
    ("R005", "900000000010", "2024-Q1", "450000.00",  "50000.00",  "45000.00",  "BDT", "accepted", "2025-04-05T08:45:00Z"),
    ("R006", "900000000010", "2024-Q2", "470000.00",  "55000.00",  "47000.00",  "BDT", "accepted", "2025-07-05T08:50:00Z"),
    # TIN 007 — two filings across years.
    ("R007", "900000000007", "2024",    "800000.00",  "70000.00",  "73000.00",  "BDT", "accepted", "2025-01-22T13:10:00Z"),
    ("R008", "900000000007", "2023",    "750000.00",  "65000.00",  "68500.00",  "BDT", "accepted", "2024-02-01T09:15:00Z"),
    # Entity 011 — larger filing, pending review.
    ("R009", "900000000011", "2024",    "8500000.00", "650000.00", "1175000.00","BDT", "submitted","2025-03-04T17:25:00Z"),
    # TIN 020 — rejected filing (status variety).
    ("R010", "900000000020", "2024",    "650000.00",  "40000.00",  "61000.00",  "BDT", "rejected", "2025-02-18T16:00:00Z"),
    # TIN 021 — duplicate-pair partner has its own accepted filing.
    ("R011", "900000000021", "2024",    "640000.00",  "42000.00",  "59800.00",  "BDT", "accepted", "2025-03-01T10:30:00Z"),
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
