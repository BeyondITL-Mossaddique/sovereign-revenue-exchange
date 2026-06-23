"""Synthetic seed data. All values are obviously fake.

TINs are in the reserved test range 900000000001-999999999999 (12 digits).
NIDs are synthetic 10-digit strings.
Names follow the patterns "Test Taxpayer NNN" (individuals) and
"Test Entity NNN <suffix>" (companies).

Includes an intentional duplicate pair (900000000020 and 900000000021 share
NID 1000000020) so the deduplicate endpoint has something to demo against.
"""
from __future__ import annotations

from .db import connect

SEED: list[tuple[str, str, str, str | None, str | None, str]] = [
    # tin,             nid,          name,                      phone,             address,                       registered_on
    # Individuals.
    ("900000000001", "1000000001", "Test Taxpayer 001",       "+880-1700000001", "Test Address 1, Dhaka",       "2024-01-15"),
    ("900000000002", "1000000002", "Test Taxpayer 002",       "+880-1700000002", "Test Address 2, Dhaka",       "2024-02-04"),
    ("900000000003", "1000000003", "Test Taxpayer 003",       "+880-1700000003", "Test Address 3, Chattogram",  "2024-03-12"),
    ("900000000004", "1000000004", "Test Taxpayer 004",       None,              "Test Address 4, Sylhet",      "2024-04-22"),
    ("900000000005", "1000000005", "Test Taxpayer 005",       "+880-1700000005", None,                          "2024-05-30"),
    ("900000000007", "1000000007", "Test Taxpayer 007",       "+880-1700000007", "Test Address 7, Rajshahi",    "2024-06-18"),
    # Companies.
    ("900000000010", "1000000010", "Test Entity 010 Ltd",     "+880-1700000010", "Test Address 10, Dhaka",      "2023-11-09"),
    ("900000000011", "1000000011", "Test Entity 011 Pvt Ltd", "+880-1700000011", "Test Address 11, Dhaka",      "2024-02-28"),
    # Intentional duplicate pair: same NID, near-identical names, different TINs.
    # The /taxpayers/deduplicate endpoint groups them via the nid key.
    ("900000000020", "1000000020", "Test Taxpayer 020",       "+880-1700000020", "Test Address 20, Khulna",     "2024-08-14"),
    ("900000000021", "1000000020", "Test  Taxpayer 020",      "+880-1700000020", "Test Address 20, Khulna",     "2024-09-02"),
]


def seed_if_empty() -> int:
    """Insert seed rows only when the table is empty. Returns rows inserted."""
    with connect() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM taxpayer").fetchone()
        if count > 0:
            return 0
        conn.executemany(
            "INSERT INTO taxpayer (tin, nid, name, phone, address, registered_on) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            SEED,
        )
        conn.commit()
        return len(SEED)


# Sanity check for the reserved test range — fails fast at import time if a
# real-looking TIN sneaks in.
for _row in SEED:
    _tin = int(_row[0])
    assert 900_000_000_001 <= _tin <= 999_999_999_999, f"seed TIN {_row[0]} is outside the test range"
    # Allow extra whitespace in the name for the intentional duplicate pair —
    # collapse runs of whitespace before checking the test prefix.
    _name_normalised = " ".join(_row[2].split())
    assert _name_normalised.startswith(("Test Taxpayer", "Test Entity")), \
        f"seed name {_row[2]!r} does not start with the 'Test Taxpayer'/'Test Entity' prefix"
