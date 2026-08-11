from __future__ import annotations

import sqlite3
from pathlib import Path

from apprentice_crdb.paths import WAREHOUSE_SCHEMA, WAREHOUSE_SEED


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    conn.executescript(WAREHOUSE_SCHEMA.read_text())
    conn.executescript(WAREHOUSE_SEED.read_text())
    conn.commit()


def execute_sql(conn: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description] if cur.description else []
    rows = [tuple(r) for r in cur.fetchall()]
    return columns, rows
