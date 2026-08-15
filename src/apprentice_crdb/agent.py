"""Answering path: question + retrieved rules → SQL.

Consumes only {id, question}. Exam fixture columns never enter this module.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from typing import Any

from apprentice_crdb.generate import Completion, Generator, get_generator
from apprentice_crdb.memory import recall_similar
from apprentice_crdb.paths import REPO_ROOT, WAREHOUSE_SCHEMA
from apprentice_crdb.sql_guard import extract_sql, extract_used_rules, reject_reason
from apprentice_crdb.warehouse_db import bootstrap, connect, execute_sql

RECALL_K = int(os.environ.get("APPRENTICE_RECALL_K", "5"))


def agent_facing_items() -> list[dict[str, str]]:
    """id + question only, via the exam adapter — never questions.json here."""
    eval_dir = REPO_ROOT / "eval"
    if str(eval_dir) not in sys.path:
        sys.path.insert(0, str(eval_dir))
    import run_exam  # type: ignore

    return run_exam.agent_facing_items()


def _system_prompt() -> str:
    ddl = WAREHOUSE_SCHEMA.read_text()
    return (
        "You write one read-only SQLite query for a tiny sales warehouse.\n"
        "Use only the schema below. Do not invent tables or columns.\n"
        "Return a single statement that begins with SELECT or WITH, inside one "
        "```sql fence. On the final line emit `-- used_rules: <id,...>` or "
        "`-- used_rules: none`.\n\n"
        "Schema:\n"
        f"{ddl}\n"
    )


def _memory_block(rules: list[dict[str, Any]]) -> str:
    if not rules:
        return ""
    lines = ["Retrieved house rules from memory:"]
    for r in rules:
        lines.append(f"{r['id']} · {r['rule_key']} · {r['statement']}")
    return "\n".join(lines)


def answer_one(
    question: str,
    *,
    as_of: str,
    generator: Generator | None = None,
    k: int = RECALL_K,
    recall: bool = True,
) -> dict[str, Any]:
    """Answer one question. Set recall=False for a cold (no-memory) ask — skip CRDB."""
    gen = generator or get_generator()
    retrieved = recall_similar(question, as_of=as_of, k=k) if recall else []
    user = question
    mem = _memory_block(retrieved)
    if mem:
        user = mem + "\n\nQuestion:\n" + question
    completion: Completion = gen.complete(_system_prompt(), user)
    raw = completion.text
    sql = extract_sql(raw)
    reason = reject_reason(sql)
    return {
        "sql": None if reason else sql,
        "raw": raw,
        "used_rules": extract_used_rules(raw),
        "retrieved_rule_ids": [str(r["id"]) for r in retrieved],
        "retrieved_rule_keys": [r["rule_key"] for r in retrieved],
        "retrieved_rules": [
            {
                "id": str(r["id"]),
                "rule_key": r["rule_key"],
                "statement": r["statement"],
            }
            for r in retrieved
        ],
        "rejected": reason,
        "model_id": completion.model_id,
    }


def answer_with_receipt(
    question: str,
    *,
    as_of: str,
    generator: Generator | None = None,
    k: int = RECALL_K,
    recall: bool = True,
) -> dict[str, Any]:
    """Answer one question and execute accepted SQL on the prop warehouse."""
    row = answer_one(question, as_of=as_of, generator=generator, k=k, recall=recall)
    receipt: dict[str, Any] = {
        "question": question,
        "as_of": as_of,
        "recall_k": k,
        **row,
    }
    if row["rejected"]:
        receipt["execution"] = {"ok": False, "error": f"rejected: {row['rejected']}"}
        return receipt

    conn = connect()
    bootstrap(conn)
    try:
        columns, rows = execute_sql(conn, row["sql"])
    except sqlite3.Error as exc:  # SQLite is the execution grader; failures stay visible.
        receipt["execution"] = {"ok": False, "error": str(exc)}
    else:
        receipt["execution"] = {
            "ok": True,
            "columns": columns,
            "rows": [list(result_row) for result_row in rows],
        }
    finally:
        conn.close()
    return receipt


def answer_exam(
    *,
    as_of: str,
    generator: Generator | None = None,
    k: int = RECALL_K,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Returns (id→sql for the grader, per-item audit rows). Rejected items get empty SQL."""
    records = []
    answers: dict[str, str] = {}
    for item in agent_facing_items():
        row = answer_one(item["question"], as_of=as_of, generator=generator, k=k)
        row["id"] = item["id"]
        answers[item["id"]] = row["sql"] or f"-- REJECTED: {row['rejected']}"
        records.append(row)
    return answers, records
