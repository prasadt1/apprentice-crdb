"""sqlglot AST-diff: wrong SQL vs correction → structured rule candidates.

Deterministic. No LLM in this path — the agent may later phrase a statement;
the *diff* is the evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import sqlglot
from sqlglot import exp


@dataclass(frozen=True)
class RuleCandidate:
    rule_key: str
    rule_type: str
    statement: str
    evidence: dict


def _parse(sql: str) -> exp.Expression:
    return sqlglot.parse_one(sql, read="sqlite")


def _predicate_sql(node: exp.Expression) -> str:
    return node.sql(dialect="sqlite")


def _walk_predicates(tree: exp.Expression) -> set[str]:
    parts: set[str] = set()
    for where in tree.find_all(exp.Where):
        clause = where.this
        if isinstance(clause, exp.And):
            for pred in clause.flatten():
                parts.add(_predicate_sql(pred))
        else:
            parts.add(_predicate_sql(clause))
    return parts


def _tables(tree: exp.Expression) -> set[str]:
    return {t.name.lower() for t in tree.find_all(exp.Table) if t.name}


def distill(attempt_sql: str, gold_sql: str) -> list[RuleCandidate]:
    attempt = _parse(attempt_sql)
    gold = _parse(gold_sql)
    out: list[RuleCandidate] = []

    added_filters = _walk_predicates(gold) - _walk_predicates(attempt)
    for pred in sorted(added_filters):
        key = "filter:generic"
        if "deleted_at" in pred.lower():
            key = "filter:orders_soft_delete"
        elif "cancelled" in pred.lower() or "status" in pred.lower():
            key = "filter:orders_not_cancelled"
        out.append(
            RuleCandidate(
                rule_key=key,
                rule_type="filter_required",
                statement=f"Correction added predicate: {pred}",
                evidence={"predicate": pred},
            )
        )

    added_tables = _tables(gold) - _tables(attempt)
    if added_tables:
        out.append(
            RuleCandidate(
                rule_key="join:" + "_".join(sorted(added_tables)),
                rule_type="join_path",
                statement=f"Correction joined additional tables: {', '.join(sorted(added_tables))}",
                evidence={"tables": sorted(added_tables)},
            )
        )

    if "refund" in gold_sql.lower() and "refund" not in attempt_sql.lower():
        out.append(
            RuleCandidate(
                rule_key="metric:revenue",
                rule_type="metric_definition",
                statement="Correction subtracted refunds — revenue is net of refunds.",
                evidence={"gold_mentions_refunds": True},
            )
        )

    return out


def candidates_as_dicts(attempt_sql: str, gold_sql: str) -> list[dict]:
    return [asdict(c) for c in distill(attempt_sql, gold_sql)]
