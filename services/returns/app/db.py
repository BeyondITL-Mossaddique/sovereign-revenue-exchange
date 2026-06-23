from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("SRX_DB_PATH", "/tmp/returns.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tax_return (
    id              TEXT PRIMARY KEY,
    tin             TEXT NOT NULL,
    period          TEXT NOT NULL,
    gross_income    TEXT NOT NULL,
    deductions      TEXT NOT NULL,
    tax_payable     TEXT NOT NULL,
    currency        TEXT NOT NULL,
    status          TEXT NOT NULL,
    submitted_at    TEXT NOT NULL,
    filer_category  TEXT NOT NULL DEFAULT 'general',
    UNIQUE (tin, period)
);
CREATE INDEX IF NOT EXISTS idx_return_tin ON tax_return(tin);
"""

# Columns added after the first release. SQLite silently no-ops if the column
# already exists, so we guard with a check on the table schema.
_MIGRATIONS = [
    ("filer_category", "TEXT NOT NULL DEFAULT 'general'"),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r["name"] for r in rows}


def init_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        existing = _existing_columns(conn, "tax_return")
        for column, decl in _MIGRATIONS:
            if column not in existing:
                conn.execute(f"ALTER TABLE tax_return ADD COLUMN {column} {decl}")
        conn.commit()


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    conn = connect()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()
