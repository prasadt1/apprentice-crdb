"""CockroachDB memory store. SERIALIZABLE writes. AOST reads for epoch replay."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from apprentice_crdb.embeddings import get_embedder
from apprentice_crdb.paths import MEMORY_SCHEMA


def dsn() -> str:
    return os.environ.get(
        "APPRENTICE_CRDB_DSN",
        os.environ.get("DATABASE_URL", ""),
    )


def connect() -> psycopg.Connection:
    url = dsn()
    if not url:
        raise RuntimeError("Set APPRENTICE_CRDB_DSN or DATABASE_URL to your CockroachDB URL")
    return psycopg.connect(url, row_factory=dict_row, autocommit=False)


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
    """Live rules, or the snapshot of live-as-of a timestamp (AOST)."""
    where = "superseded_by IS NULL"
    sql = f"""
        SELECT id, created_at, rule_key, rule_type, statement, evidence_episode_id, superseded_by
        FROM semantic_rules
        AS OF SYSTEM TIME %s
        WHERE {where}
        ORDER BY created_at
        LIMIT %s
    """
    # AOST cannot be parameterized as a data value in all CRDB versions the same way;
    # we use the documented literal form when as_of is set.
    with connect() as conn:
        if as_of:
            # Expect RFC3339 / CRDB timestamp string from the caller.
            q = (
                "SELECT id, created_at, rule_key, rule_type, statement, "
                "evidence_episode_id, superseded_by "
                "FROM semantic_rules AS OF SYSTEM TIME '"
                + as_of.replace("'", "")
                + "' WHERE superseded_by IS NULL ORDER BY created_at LIMIT %s"
            )
            rows = conn.execute(q, (limit,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, created_at, rule_key, rule_type, statement, "
                "evidence_episode_id, superseded_by "
                "FROM semantic_rules WHERE superseded_by IS NULL "
                "ORDER BY created_at LIMIT %s",
                (limit,),
            ).fetchall()
        conn.rollback()
        return [dict(r) for r in rows]


def show_gc_ttl() -> str:
    with connect() as conn:
        try:
            row = conn.execute("SHOW ZONE CONFIGURATION FROM DATABASE defaultdb").fetchone()
        except Exception:
            row = conn.execute("SHOW ZONE CONFIGURATION FROM RANGE default").fetchone()
        conn.rollback()
        return str(row)
