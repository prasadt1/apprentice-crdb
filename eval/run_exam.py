"""Exam adapter: execute SQL against the seeded warehouse and grade via result signatures.

This file may evolve after the freeze. eval/questions.json and eval/labels.json may NOT.

Subcommands
-----------
questions            Print the agent-facing exam: id + question text ONLY.
                     (gold_sql / naive_sql / bait_sql never leave this file's other modes;
                     the agent harness must consume THIS output, not questions.json.)
verify               Post-freeze integrity: every gold_sql executes and reproduces
                     labels.json; divergence invariants hold; leakage check is clean.
grade ANSWERS.json   Grade agent answers ({"q01": "SELECT ...", ...} or a list of
                     {"id","sql"}) against labels.json. Prints a JSON report:
                     per-item outcome, per-stratum accuracy, overall accuracy,
                     regression-bait outcomes.
emit-labels          Regenerate labels.json from questions.json gold_sql.
                     REFUSES to run if FREEZE.md exists — after the freeze,
                     label mistakes are recorded as errata in eval/RESULTS.md.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO = EVAL_DIR.parent
sys.path.insert(0, str(REPO / "src"))

from apprentice_crdb.grader import result_signature, signatures_match  # noqa: E402
from apprentice_crdb.warehouse_db import bootstrap, connect, execute_sql  # noqa: E402

QUESTIONS = EVAL_DIR / "questions.json"
LABELS = EVAL_DIR / "labels.json"
FREEZE = EVAL_DIR / "FREEZE.md"


def load_questions() -> list[dict]:
    return json.loads(QUESTIONS.read_text())


def load_labels() -> dict[str, dict]:
    return {row["id"]: row for row in json.loads(LABELS.read_text())}


def fresh_conn():
    conn = connect()
    bootstrap(conn)
    return conn


def signature_of(conn, sql: str) -> dict:
    cols, rows = execute_sql(conn, sql)
    return result_signature(cols, rows)


def _norm_stmt(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _norm_lines(text: str) -> set[str]:
    return {re.sub(r"\s+", " ", ln.strip().lower()) for ln in text.splitlines()
            if len(re.sub(r"\s+", " ", ln.strip())) >= 30}


def cmd_questions() -> int:
    agent_view = [{"id": q["id"], "question": q["question"]} for q in load_questions()]
    print(json.dumps(agent_view, indent=2))
    return 0


def cmd_verify() -> int:
    questions, labels = load_questions(), load_labels()
    conn = fresh_conn()
    failures: list[str] = []

    for q in questions:
        qid = q["id"]
        try:
            gsig = signature_of(conn, q["gold_sql"])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{qid}: gold_sql failed: {exc}")
            continue
        if qid not in labels:
            failures.append(f"{qid}: missing from labels.json")
            continue
        lab = labels[qid]
        if not signatures_match(lab, gsig):
            failures.append(f"{qid}: gold signature does not reproduce labels.json "
                            f"(label {lab['sha256'][:12]}…, got {gsig['sha256'][:12]}…)")
        try:
            nsig = signature_of(conn, q["naive_sql"])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{qid}: naive_sql failed: {exc}")
            continue
        if q["stratum"] == "unaffected":
            if not signatures_match(gsig, nsig):
                failures.append(f"{qid}: unaffected item but naive != gold")
        elif signatures_match(gsig, nsig):
            failures.append(f"{qid}: naive == gold — divergence invariant broken")
        if q.get("regression_bait"):
            try:
                bsig = signature_of(conn, q["bait_sql"])
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{qid}: bait_sql failed: {exc}")
                continue
            if signatures_match(gsig, bsig):
                failures.append(f"{qid}: bait == gold — bait proves nothing")

    protected = (REPO / "src/apprentice_crdb/gold_sql.py").read_text()
    protected_stmts = set()
    for m in re.findall(r'"""(.*?)"""', protected, flags=re.S):
        if "select" in m.lower():
            protected_stmts.add(_norm_stmt(m))
    protected_lines = _norm_lines(protected)
    for t in (REPO / "tests").glob("*.py"):
        protected_lines |= _norm_lines(t.read_text())
    for q in questions:
        for field in ("gold_sql", "naive_sql", "bait_sql"):
            sql = q.get(field)
            if not sql:
                continue
            if _norm_stmt(sql) in protected_stmts:
                failures.append(f"{q['id']}: {field} equals a protected gold_sql.py statement")
            shared = _norm_lines(sql) & protected_lines
            if shared:
                failures.append(f"{q['id']}: {field} shares a line with protected files: {sorted(shared)[:2]}")

    n_labels = len(labels)
    if len(questions) != 50 or n_labels != 50:
        failures.append(f"expected 50 questions + 50 labels, found {len(questions)} + {n_labels}")

    if failures:
        print("VERIFY FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    strata = defaultdict(int)
    for q in questions:
        strata[q["stratum"]] += 1
    baits = [q["id"] for q in questions if q.get("regression_bait")]
    print(f"VERIFY OK: 50/50 gold reproduce labels; divergence + leakage invariants hold; "
          f"strata {dict(strata)}; baits {baits}")
    return 0


def cmd_grade(answers_path: str) -> int:
    raw = json.loads(Path(answers_path).read_text())
    answers: dict[str, str] = ({row["id"]: row["sql"] for row in raw}
                               if isinstance(raw, list) else dict(raw))
    questions, labels = load_questions(), load_labels()
    conn = fresh_conn()

    items = []
    per_stratum: dict[str, list[bool]] = defaultdict(list)
    for q in questions:
        qid = q["id"]
        lab = labels[qid]
        sql = answers.get(qid)
        if sql is None:
            outcome, correct = "missing", False
        else:
            try:
                asig = signature_of(conn, sql)
                correct = signatures_match(lab, asig)
                outcome = "correct" if correct else "wrong"
            except Exception as exc:  # noqa: BLE001
                outcome, correct = f"error: {exc}", False
        per_stratum[q["stratum"]].append(correct)
        row = {"id": qid, "stratum": q["stratum"], "outcome": outcome}
        if q.get("regression_bait"):
            row["regression_bait"] = True
        items.append(row)

    total = len(items)
    n_correct = sum(1 for it in items if it["outcome"] == "correct")
    report = {
        "total": total,
        "correct": n_correct,
        "accuracy": round(n_correct / total, 4),
        "by_stratum": {s: {"n": len(v), "correct": sum(v),
                           "accuracy": round(sum(v) / len(v), 4)}
                       for s, v in sorted(per_stratum.items())},
        "regression_bait": {it["id"]: it["outcome"] for it in items if it.get("regression_bait")},
        "items": items,
    }
    print(json.dumps(report, indent=2))
    return 0


def cmd_emit_labels() -> int:
    if FREEZE.exists():
        print("REFUSED: eval/FREEZE.md exists — labels.json is frozen. "
              "Record label errata in eval/RESULTS.md instead.")
        return 1
    conn = fresh_conn()
    labels = []
    for q in load_questions():
        sig = signature_of(conn, q["gold_sql"])
        labels.append({"id": q["id"], "columns": sig["columns"],
                       "row_count": sig["row_count"], "sha256": sig["sha256"]})
    LABELS.write_text(json.dumps(labels, indent=2) + "\n")
    print(f"wrote {LABELS} ({len(labels)} labels)")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "questions":
        return cmd_questions()
    if cmd == "verify":
        return cmd_verify()
    if cmd == "grade":
        if len(sys.argv) != 3:
            print("usage: run_exam.py grade ANSWERS.json")
            return 2
        return cmd_grade(sys.argv[2])
    if cmd == "emit-labels":
        return cmd_emit_labels()
    print(f"unknown subcommand: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
