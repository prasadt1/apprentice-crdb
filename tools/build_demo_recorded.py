#!/usr/bin/env python3.11
"""Build docs/demo/{questions,recorded}.json for the Pages live-demo widget.

Recorded answers come from eval/runs-nova-lite (memory_zero = no_memory,
join_path = with_memory). Same grader as the published curve. Never write gold/naive.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

from apprentice_crdb.grader import result_signature, signatures_match  # noqa: E402
from apprentice_crdb.sql_guard import reject_reason  # noqa: E402
from apprentice_crdb.warehouse_db import bootstrap, connect, execute_sql  # noqa: E402
import run_exam  # type: ignore  # noqa: E402

OUT = ROOT / "docs" / "demo"
RUNS = ROOT / "eval" / "runs-nova-lite"
QUESTIONS = ROOT / "eval" / "questions.json"

MODE_EPOCH = {
    "no_memory": "memory_zero",
    "with_memory": "join_path",
}


def _grade(qid: str, sql: str | None, labels: dict) -> dict:
    if not sql or sql.startswith("-- REJECTED"):
        return {
            "columns": [],
            "rows": [],
            "verdict": "rejected",
            "expected_row_count": labels[qid]["row_count"],
        }
    reason = reject_reason(sql)
    if reason:
        return {
            "columns": [],
            "rows": [],
            "verdict": "rejected",
            "expected_row_count": labels[qid]["row_count"],
            "error": reason,
        }
    conn = connect()
    bootstrap(conn)
    try:
        columns, rows = execute_sql(conn, sql)
    except sqlite3.Error as exc:
        return {
            "columns": [],
            "rows": [],
            "verdict": "error",
            "expected_row_count": labels[qid]["row_count"],
            "error": str(exc),
        }
    finally:
        conn.close()
    actual = result_signature(columns, rows)
    ok = signatures_match(labels[qid], actual)
    return {
        "columns": columns,
        "rows": [list(r) for r in rows],
        "verdict": "correct" if ok else "wrong",
        "expected_row_count": labels[qid]["row_count"],
    }


def main() -> None:
    labels = run_exam.load_labels()
    questions_raw = json.loads(QUESTIONS.read_text())
    facing = [{"id": q["id"], "question": q["question"], "stratum": q["stratum"]} for q in questions_raw]

    recorded: dict[str, dict] = {}
    for mode, epoch in MODE_EPOCH.items():
        audit = json.loads((RUNS / f"agent_{epoch}_audit.json").read_text())
        by_id = {row["id"]: row for row in audit}
        answers = json.loads((RUNS / f"agent_{epoch}_answers.json").read_text())
        for item in facing:
            qid = item["id"]
            row = by_id.get(qid, {})
            sql = answers.get(qid) or row.get("sql")
            graded = _grade(qid, sql, labels)
            retrieved = []
            for key in row.get("retrieved_rule_keys") or []:
                retrieved.append({"rule_key": key, "statement": "(recorded run — statement not archived)"})
            # Prefer statements if present in newer audits
            if row.get("retrieved_rules"):
                retrieved = [
                    {"rule_key": r["rule_key"], "statement": r.get("statement", "")}
                    for r in row["retrieved_rules"]
                ]
            recorded.setdefault(qid, {})[mode] = {
                "question": item["question"],
                "mode": mode,
                "retrieved": retrieved if mode == "with_memory" else [],
                "sql": None if graded["verdict"] == "rejected" and not sql else sql,
                "columns": graded["columns"],
                "rows": graded["rows"],
                "verdict": graded["verdict"],
                "expected_row_count": graded["expected_row_count"],
                "model_id": row.get("model_id") or "amazon.nova-lite-v1:0",
                "elapsed_ms": 0,
                "source": "recorded",
                "error": graded.get("error"),
            }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "questions.json").write_text(json.dumps(facing, indent=2) + "\n")
    (OUT / "recorded.json").write_text(json.dumps(recorded, indent=2) + "\n")
    q02 = recorded["q02"]
    print(f"wrote {OUT}/questions.json ({len(facing)} items)")
    print(f"wrote {OUT}/recorded.json")
    print(f"q02 no_memory  → {q02['no_memory']['verdict']} rows={q02['no_memory']['rows']}")
    print(f"q02 with_memory → {q02['with_memory']['verdict']} rows={q02['with_memory']['rows']}")


if __name__ == "__main__":
    main()
