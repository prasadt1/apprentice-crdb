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


def cmd_migrate(args: argparse.Namespace) -> int:
    from apprentice_crdb import memory

    result = memory.migrate(try_vector_index=args.try_vector_index)
    print(json.dumps(result, indent=2))
    return 0


def cmd_gc(_: argparse.Namespace) -> int:
    from apprentice_crdb import memory

    print(memory.show_gc_ttl())
    return 0


def cmd_recall(args: argparse.Namespace) -> int:
    from apprentice_crdb import memory

    rows = memory.recall_live(limit=args.limit, as_of=args.as_of)
    print(json.dumps(rows, indent=2, default=str))
    return 0


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
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
