from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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

        report = memory.migrate(try_vector_index=args.try_vector_index)
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1

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


def cmd_reset_memory(args: argparse.Namespace) -> int:
    if not args.yes:
        print("Refused: memory-reset requires --yes.", file=sys.stderr)
        return 2

    def go() -> int:
        from apprentice_crdb.memory import cluster_now, reset_memory

        reset_memory()
        print(json.dumps({"memory_zero_as_of": cluster_now()}, indent=2))
        return 0

    return _run_crdb(go)


def cmd_teach(args: argparse.Namespace) -> int:
    def go() -> int:
        from apprentice_crdb.educate import teach_correction
        from apprentice_crdb.memory import cluster_now

        report = teach_correction(
            args.question,
            Path(args.attempt).read_text(),
            Path(args.correction).read_text(),
        )
        report["as_of"] = cluster_now()
        print(json.dumps(report, indent=2))
        return 0 if report["rules"] else 1

    return _run_crdb(go)


def _print_answer_receipt(receipt: dict) -> None:
    print("APPRENTICE MEMORY RECEIPT")
    print(f"question: {receipt['question']}")
    print(f"as_of: {receipt['as_of']}")
    print(f"model: {receipt['model_id']}")
    print(f"recall_k: {receipt['recall_k']}")
    rules = receipt["retrieved_rules"]
    print(f"retrieved: {len(rules)} rule(s)")
    for rule in rules:
        print(f"  - {rule['rule_key']}: {rule['statement']}")
    print("sql:")
    print(receipt["sql"] or f"  REJECTED: {receipt['rejected']}")
    execution = receipt["execution"]
    if execution["ok"]:
        print("result:")
        print(json.dumps({"columns": execution["columns"], "rows": execution["rows"]}, indent=2))
    else:
        print(f"result: ERROR — {execution['error']}")
    if "exam" in receipt:
        print(f"frozen_exam: {receipt['exam']['id']} — {receipt['exam']['outcome'].upper()}")


def cmd_answer(args: argparse.Namespace) -> int:
    def go() -> int:
        from apprentice_crdb.agent import answer_with_receipt
        from apprentice_crdb.memory import cluster_now

        as_of = args.as_of or cluster_now()
        receipt = answer_with_receipt(args.question, as_of=as_of, k=args.k)
        if args.json:
            print(json.dumps(receipt, indent=2, default=str))
        else:
            _print_answer_receipt(receipt)
        return 0 if receipt["execution"]["ok"] else 1

    return _run_crdb(go)


def cmd_probe(args: argparse.Namespace) -> int:
    def go() -> int:
        from apprentice_crdb.agent import agent_facing_items, answer_with_receipt
        from apprentice_crdb.paths import REPO_ROOT

        items = {item["id"]: item for item in agent_facing_items()}
        if args.exam_id not in items:
            print(f"Unknown frozen exam id: {args.exam_id}", file=sys.stderr)
            return 2
        receipt = answer_with_receipt(
            items[args.exam_id]["question"],
            as_of=args.as_of,
            k=args.k,
        )

        sys.path.insert(0, str(REPO_ROOT / "eval"))
        import run_exam  # type: ignore

        if receipt["execution"]["ok"]:
            execution = receipt["execution"]
            actual = result_signature(
                execution["columns"],
                [tuple(row) for row in execution["rows"]],
            )
            expected = run_exam.load_labels()[args.exam_id]
            outcome = "correct" if signatures_match(expected, actual) else "wrong"
        else:
            outcome = "wrong"
        receipt["exam"] = {"id": args.exam_id, "outcome": outcome}

        if args.json:
            print(json.dumps(receipt, indent=2, default=str))
        else:
            _print_answer_receipt(receipt)
        return 0

    return _run_crdb(go)


def cmd_baseline(_: argparse.Namespace) -> int:
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


def cmd_report(args: argparse.Namespace) -> int:
    from apprentice_crdb.report import format_published_result, published_result

    result = published_result()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_published_result(result))
    return 0


def cmd_educate(args: argparse.Namespace) -> int:
    from apprentice_crdb.educate import run_education
    from apprentice_crdb.paths import REPO_ROOT

    def go() -> int:
        plan = run_education(policy=args.policy)
        sys.path.insert(0, str(REPO_ROOT / "eval"))
        import run_exam  # type: ignore

        import io
        from contextlib import redirect_stdout

        policies = ["oracle", "agent"] if args.policy == "both" else [args.policy]
        out: dict = {"policy": args.policy, "curves": {}}
        for pol in policies:
            curve = []
            for ep in plan["epochs"]:
                ans = ep.get(f"{pol}_answers_path")
                if not ans:
                    continue
                row = {
                    "name": ep["name"],
                    "as_of": ep["as_of"],
                    "taught": ep["taught"],
                    "live_keys": ep["live_keys"],
                    "answers_path": ans,
                }
                buf = io.StringIO()
                with redirect_stdout(buf):
                    run_exam.cmd_grade(str(REPO_ROOT / ans))
                report = json.loads(buf.getvalue())
                row["accuracy"] = report["accuracy"]
                row["correct"] = report["correct"]
                row["by_stratum"] = report["by_stratum"]
                row["regression_bait"] = report["regression_bait"]
                curve.append(row)
                print(
                    f"{pol}/{ep['name']}: {report['correct']}/{report['total']} "
                    f"({report['accuracy']}) as_of={ep['as_of']}",
                    file=sys.stderr,
                )
            out["curves"][pol] = curve
        (REPO_ROOT / "eval" / "curve.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
        print(json.dumps(out, indent=2, default=str))
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

    reset = sub.add_parser(
        "memory-reset",
        help="Delete memory rows for a fresh experiment (requires --yes)",
    )
    reset.add_argument("--yes", action="store_true")
    reset.set_defaults(func=cmd_reset_memory)

    teach = sub.add_parser(
        "teach",
        help="Distill one SQL correction into CockroachDB memory",
    )
    teach.add_argument("question", help="The user question that produced the attempted SQL")
    teach.add_argument("--attempt", required=True, help="Path to the attempted SQL")
    teach.add_argument("--correction", required=True, help="Path to the corrected SQL")
    teach.set_defaults(func=cmd_teach)

    answer = sub.add_parser(
        "answer",
        help="Answer one question with AOST memory and print its memory receipt",
    )
    answer.add_argument("question")
    answer.add_argument("--as-of", dest="as_of", default=None, help="CRDB AS OF SYSTEM TIME literal")
    answer.add_argument("--k", type=int, default=5)
    answer.add_argument("--json", action="store_true", help="Emit the full receipt as JSON")
    answer.set_defaults(func=cmd_answer)

    probe = sub.add_parser(
        "probe",
        help="Run one frozen exam item at an AOST snapshot and grade it",
    )
    probe.add_argument("exam_id", help="Frozen item id, for example q31")
    probe.add_argument("--as-of", dest="as_of", required=True, help="CRDB AS OF SYSTEM TIME literal")
    probe.add_argument("--k", type=int, default=5)
    probe.add_argument("--json", action="store_true", help="Emit the full receipt as JSON")
    probe.set_defaults(func=cmd_probe)

    report = sub.add_parser(
        "report",
        help="Re-grade the published model artifacts and print their memory curves",
    )
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    sub.add_parser(
        "baseline",
        help="Grade memory-zero (naive SQL fixtures) against the frozen exam",
    ).set_defaults(func=cmd_baseline)

    edu = sub.add_parser(
        "educate",
        help="Write corrections into CockroachDB and score each AOST epoch",
    )
    edu.add_argument(
        "--policy",
        choices=("oracle", "agent", "both"),
        default="oracle",
        help="oracle = selector ceiling; agent = Bedrock generation; both = publish the gap",
    )
    edu.set_defaults(func=cmd_educate)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
