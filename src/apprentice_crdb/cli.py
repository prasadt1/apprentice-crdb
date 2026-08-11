from __future__ import annotations

import argparse
import json
import sys

from apprentice_crdb import __version__
from apprentice_crdb.distill import candidates_as_dicts
from apprentice_crdb.gold_sql import GOLD_REVENUE_BY_REGION, NAIVE_REVENUE_BY_REGION
from apprentice_crdb.grader import result_signature, signatures_match
from apprentice_crdb.warehouse_db import bootstrap, connect, execute_sql


def cmd_warehouse_demo(_: argparse.Namespace) -> int:
    conn = connect()
    bootstrap(conn)
    naive_cols, naive_rows = execute_sql(conn, NAIVE_REVENUE_BY_REGION)
    gold_cols, gold_rows = execute_sql(conn, GOLD_REVENUE_BY_REGION)
    naive_sig = result_signature(naive_cols, naive_rows)
    gold_sig = result_signature(gold_cols, gold_rows)
    print("naive (calendar Q3, no house rules):")
    print(json.dumps({"rows": [list(r) for r in naive_rows], "sig": naive_sig}, indent=2))
    print("gold (fiscal Q3, net revenue, live orders):")
    print(json.dumps({"rows": [list(r) for r in gold_rows], "sig": gold_sig}, indent=2))
    print("match:", signatures_match(gold_sig, naive_sig))
    return 0


def cmd_distill(_: argparse.Namespace) -> int:
    print(json.dumps(candidates_as_dicts(NAIVE_REVENUE_BY_REGION, GOLD_REVENUE_BY_REGION), indent=2))
    return 0


def _run_crdb(fn) -> int:
    from apprentice_crdb.memory import DsnError

    try:
        return fn()
    except DsnError as exc:
        print(exc, file=sys.stderr)
        return 2


def cmd_migrate(args: argparse.Namespace) -> int:
    def go() -> int:
        from apprentice_crdb import memory

        print(json.dumps(memory.migrate(try_vector_index=args.try_vector_index), indent=2))
        return 0

    return _run_crdb(go)


def cmd_gc(_: argparse.Namespace) -> int:
    def go() -> int:
        from apprentice_crdb import memory

        print(json.dumps(memory.show_gc_ttl(), indent=2, default=str))
        return 0

    return _run_crdb(go)


def cmd_recall(args: argparse.Namespace) -> int:
    def go() -> int:
        from apprentice_crdb import memory

        print(json.dumps(memory.recall_live(limit=args.limit, as_of=args.as_of), indent=2, default=str))
        return 0

    return _run_crdb(go)


def cmd_baseline(_: argparse.Namespace) -> int:
    from pathlib import Path

    from apprentice_crdb.paths import REPO_ROOT

    questions = json.loads((REPO_ROOT / "eval" / "questions.json").read_text())
    answers = {q["id"]: q["naive_sql"] for q in questions}
    out = REPO_ROOT / "eval" / "runs" / "answers_memory_zero.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(answers, indent=2) + "\n")
    print(f"wrote {out}", file=sys.stderr)
    sys.path.insert(0, str(REPO_ROOT / "eval"))
    import run_exam  # type: ignore

    return run_exam.cmd_grade(str(out))


def cmd_educate(_: argparse.Namespace) -> int:
    from pathlib import Path

    from apprentice_crdb.educate import run_education
    from apprentice_crdb.paths import REPO_ROOT

    def go() -> int:
        plan = run_education()
        sys.path.insert(0, str(REPO_ROOT / "eval"))
        import run_exam  # type: ignore

        curve = []
        import io
        from contextlib import redirect_stdout

        for ep in plan["epochs"]:
            buf = io.StringIO()
            with redirect_stdout(buf):
                run_exam.cmd_grade(str(REPO_ROOT / ep["answers_path"]))
            report = json.loads(buf.getvalue())
            ep["accuracy"] = report["accuracy"]
            ep["correct"] = report["correct"]
            ep["by_stratum"] = report["by_stratum"]
            ep["regression_bait"] = report["regression_bait"]
            curve.append(ep)
            print(
                f"{ep['name']}: {report['correct']}/{report['total']} "
                f"({report['accuracy']}) as_of={ep['as_of']} keys={ep['live_keys']}",
                file=sys.stderr,
            )
        (REPO_ROOT / "eval" / "curve.json").write_text(json.dumps({"epochs": curve}, indent=2, default=str) + "\n")
        print(json.dumps({"epochs": curve}, indent=2, default=str))
        return 0

    return _run_crdb(go)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="apprentice",
        description="Apprentice — ships its own learning curve (memory is the product).",
    )
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("warehouse-demo", help="Show naive vs gold result sets on the prop warehouse").set_defaults(
        func=cmd_warehouse_demo
    )
    sub.add_parser("distill", help="AST-diff the demo naive vs gold SQL").set_defaults(func=cmd_distill)

    m = sub.add_parser("migrate", help="Apply CockroachDB memory schema")
    m.add_argument("--try-vector-index", action="store_true")
    m.set_defaults(func=cmd_migrate)

    sub.add_parser("gc-ttl", help="Print live zone/GC config (VERIFY gate)").set_defaults(func=cmd_gc)

    r = sub.add_parser("recall", help="List live semantic rules (optional AOST)")
    r.add_argument("--as-of", dest="as_of", default=None, help="CRDB AS OF SYSTEM TIME literal")
    r.add_argument("--limit", type=int, default=20)
    r.set_defaults(func=cmd_recall)

    sub.add_parser(
        "baseline",
        help="Grade memory-zero (naive SQL fixtures) against the frozen exam",
    ).set_defaults(func=cmd_baseline)

    sub.add_parser(
        "educate",
        help="Write corrections into CockroachDB and score each AOST epoch",
    ).set_defaults(func=cmd_educate)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
