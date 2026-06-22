from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("SRX_DB_PATH", "/tmp/taxpayer-registry.sqlite"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS taxpayer (
    tin           TEXT PRIMARY KEY,
    nid           TEXT NOT NULL,
    name          TEXT NOT NULL,
    phone         TEXT,
    address       TEXT,
    registered_on TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_taxpayer_nid ON taxpayer(nid);
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
