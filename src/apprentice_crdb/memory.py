"""CockroachDB memory store. SERIALIZABLE writes. AOST reads for epoch replay."""

from __future__ import annotations

import os
import time
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from apprentice_crdb.embeddings import get_embedder
from apprentice_crdb.paths import MEMORY_SCHEMA


_PLACEHOLDER_MARKERS = (
    "://...",
    "@HOST",
    "@host:",
    "USER:PASSWORD",
    "USER:PASS@",
)


def dsn() -> str:
    return os.environ.get(
        "APPRENTICE_CRDB_DSN",
        os.environ.get("DATABASE_URL", ""),
    )


class DsnError(RuntimeError):
    pass


def require_dsn() -> str:
    url = dsn().strip()
    if not url:
        raise DsnError(
            "APPRENTICE_CRDB_DSN is not set.\n"
            "In CockroachDB Cloud: cluster → Connect → copy the PostgreSQL connection string "
            "(it looks like postgresql://app:secret@foo.jcloud.cockroachlabs.cloud:26257/"
            "defaultdb?sslmode=verify-full) and:\n"
            "  export APPRENTICE_CRDB_DSN='that-entire-string'"
        )
    lowered = url.lower()
    if any(m.lower() in lowered or m in url for m in _PLACEHOLDER_MARKERS):
        raise DsnError(
            "APPRENTICE_CRDB_DSN is still the example placeholder (HOST / USER / ...).\n"
            "Replace it with the real URL from the Cloud console Connect dialog — "
            "do not type HOST or PASSWORD yourself."
        )
    return url


def connect(*, autocommit: bool = False) -> psycopg.Connection:
    return psycopg.connect(
        require_dsn(),
        row_factory=dict_row,
        autocommit=autocommit,
        connect_timeout=15,
    )


def cluster_now() -> str:
    """HLC decimal string for BEGIN AS OF SYSTEM TIME (not wall-clock now())."""
    with connect(autocommit=True) as conn:
        row = conn.execute("SELECT cluster_logical_timestamp()::STRING AS ts").fetchone()
        assert row is not None
        return row["ts"]


def aost_literal(ts: str) -> str:
    """Strip quotes / logical counter. CRDB wants an unquoted HLC decimal."""
    raw = ts.replace("'", "").strip()
    if "," in raw:
        raw = raw.split(",", 1)[0].strip()
    return raw


def _hlc_seconds(ts: str) -> float:
    return float(aost_literal(ts))


def _wait_until_closed(ts: str, *, lag_s: float = 4.0, timeout_s: float = 25.0) -> None:
    """AOST to 'now' blocks until the closed timestamp advances. Wait first."""
    target = _hlc_seconds(ts) + lag_s
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _hlc_seconds(cluster_now()) >= target:
            return
        time.sleep(0.25)


def reset_memory() -> None:
    """Wipe agent memory so an education run starts empty. Does not touch the warehouse."""
    with connect() as conn:
        conn.execute("DELETE FROM semantic_rules")
        conn.execute("DELETE FROM episodic_events")
        conn.commit()


def migrate(try_vector_index: bool = False) -> dict[str, Any]:
    notes: list[str] = []
    with connect() as conn:
        conn.execute(MEMORY_SCHEMA.read_text())
        conn.commit()
        notes.append("applied sql/001_memory.sql")
        if try_vector_index:
            try:
                conn.execute(
                    "CREATE VECTOR INDEX IF NOT EXISTS semantic_embedding_idx "
                    "ON semantic_rules (embedding)"
                )
                conn.commit()
                notes.append("CREATE VECTOR INDEX ok")
            except Exception as exc:  # noqa: BLE001 — we must surface the real error
                conn.rollback()
                notes.append(f"CREATE VECTOR INDEX failed (documented, not faked): {exc}")
    return {"ok": True, "notes": notes}


def record_episode(
    question: str,
    generated_sql: str,
    *,
    gold_sql: str | None = None,
    result_ok: bool | None = None,
    cited: list[UUID] | None = None,
    created_at: str | None = None,
) -> UUID:
    sql = """
        INSERT INTO episodic_events
            (question, generated_sql, gold_sql, result_ok, cited_memory_ids, created_at)
        VALUES (%s, %s, %s, %s, %s, COALESCE(%s::timestamptz, now()))
        RETURNING id
    """
    with connect() as conn:
        row = conn.execute(
            sql,
            (question, generated_sql, gold_sql, result_ok, cited or [], created_at),
        ).fetchone()
        conn.commit()
        assert row is not None
        return row["id"]


def upsert_rule(
    rule_key: str,
    rule_type: str,
    statement: str,
    *,
    evidence_episode_id: UUID | None = None,
    created_at: str | None = None,
) -> UUID:
    """One live rule per key. Concurrent writers serialize; old row is superseded."""
    embedder = get_embedder()
    vector = embedder.embed(statement)
    vector_literal = "[" + ",".join(f"{x:.8f}" for x in vector) + "]"
    with connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        live = conn.execute(
            "SELECT id FROM semantic_rules WHERE rule_key = %s AND superseded_by IS NULL",
            (rule_key,),
        ).fetchone()
        new_id = conn.execute(
            """
            INSERT INTO semantic_rules
                (rule_key, rule_type, statement, evidence_episode_id, embedding, created_at)
            VALUES (%s, %s, %s, %s, %s::VECTOR(384), COALESCE(%s::timestamptz, now()))
            RETURNING id
            """,
            (rule_key, rule_type, statement, evidence_episode_id, vector_literal, created_at),
        ).fetchone()
        assert new_id is not None
        if live and live["id"] != new_id["id"]:
            conn.execute(
                "UPDATE semantic_rules SET superseded_by = %s WHERE id = %s",
                (new_id["id"], live["id"]),
            )
        conn.commit()
        return new_id["id"]


def recall_live(limit: int = 20, as_of: str | None = None) -> list[dict[str, Any]]:
    """Live rules, or the snapshot of live-as-of an HLC (AOST)."""
    select = """
        SELECT id, created_at, rule_key, rule_type, statement, evidence_episode_id, superseded_by
        FROM semantic_rules
        WHERE superseded_by IS NULL
        ORDER BY created_at
        LIMIT %s
    """
    if not as_of:
        with connect() as conn:
            rows = conn.execute(select, (limit,)).fetchall()
            conn.rollback()
            return [dict(r) for r in rows]

    # psycopg BEGIN-then-SET TRANSACTION AS OF races the gateway HLC
    # ("inconsistent AS OF SYSTEM TIME timestamp"). Start the txn at the HLC.
    _wait_until_closed(as_of)
    ts = aost_literal(as_of)
    with connect(autocommit=True) as conn:
        conn.execute("SET statement_timeout = '20s'")
        conn.execute(f"BEGIN AS OF SYSTEM TIME {ts}")
        try:
            rows = conn.execute(select, (limit,)).fetchall()
        finally:
            conn.execute("ROLLBACK")
        return [dict(r) for r in rows]


def show_gc_ttl() -> dict[str, Any]:
    """Measure live GC / zone config. Basic/serverless may refuse ALTER; we still record what we see."""
    probes = (
        "SELECT target, raw_config_sql FROM crdb_internal.zones LIMIT 20",
        "SHOW ZONE CONFIGURATION FROM RANGE default",
        "SHOW ZONE CONFIGURATION FROM DATABASE defaultdb",
    )
    out: dict[str, Any] = {"probes": []}
    with connect() as conn:
        for sql in probes:
            try:
                rows = conn.execute(sql).fetchall()
                out["probes"].append({"sql": sql, "ok": True, "rows": [dict(r) for r in rows]})
            except Exception as exc:  # noqa: BLE001 — VERIFY needs the real error
                conn.rollback()
                out["probes"].append({"sql": sql, "ok": False, "error": str(exc)})
        conn.rollback()
    return out
