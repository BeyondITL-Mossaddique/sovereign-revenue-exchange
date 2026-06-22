from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("SRX_DB_PATH", "/tmp/returns.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tax_return (
    id            TEXT PRIMARY KEY,
    tin           TEXT NOT NULL,
    period        TEXT NOT NULL,
    gross_income  TEXT NOT NULL,
    deductions    TEXT NOT NULL,
    tax_payable   TEXT NOT NULL,
    currency      TEXT NOT NULL,
    status        TEXT NOT NULL,
    submitted_at  TEXT NOT NULL,
    UNIQUE (tin, period)
);
CREATE INDEX IF NOT EXISTS idx_return_tin ON tax_return(tin);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    conn = connect()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()
