"""sqlglot AST-diff: wrong SQL vs correction → structured rule candidates.

Deterministic. No LLM in this path — the agent may later phrase a statement;
the *diff* is the evidence.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import sqlglot
from sqlglot import exp

_WAREHOUSE_TABLES = frozenset(
    {"orders", "order_lines", "customers", "regions", "products", "refunds"}
)
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_FISCAL_MONTH_DAY = frozenset({"-02-01", "-05-01", "-08-01", "-11-01"})


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


def _add_clause_preds(clause: exp.Expression | None, parts: set[str]) -> None:
    if clause is None:
        return
    if isinstance(clause, exp.And):
        for pred in clause.flatten():
            parts.add(_predicate_sql(pred))
    else:
        parts.add(_predicate_sql(clause))


def _walk_predicates(tree: exp.Expression) -> set[str]:
    parts: set[str] = set()
    for where in tree.find_all(exp.Where):
        _add_clause_preds(where.this, parts)
    for join in tree.find_all(exp.Join):
        _add_clause_preds(join.args.get("on"), parts)
    return parts


def _tables(tree: exp.Expression) -> set[str]:
    return {
        t.name.lower()
        for t in tree.find_all(exp.Table)
        if t.name and t.name.lower() in _WAREHOUSE_TABLES
    }


def _dates(sql: str) -> set[str]:
    return set(_DATE.findall(sql))


def _is_date_predicate(pred: str) -> bool:
    return bool(_DATE.search(pred))


def _region_joined_on_product(tree: exp.Expression) -> bool:
    for join in tree.find_all(exp.Join):
        table = join.this
        name = table.name.lower() if table is not None and table.name else ""
        if name != "regions":
            continue
        on = join.args.get("on")
        if on and "product_id" in on.sql(dialect="sqlite").lower():
            return True
    return False


def distill(attempt_sql: str, gold_sql: str) -> list[RuleCandidate]:
    attempt = _parse(attempt_sql)
    gold = _parse(gold_sql)
    out: list[RuleCandidate] = []

    added_filters = _walk_predicates(gold) - _walk_predicates(attempt)
    for pred in sorted(added_filters):
        if _is_date_predicate(pred):
            continue  # date-window diffs are the fiscal calendar, not a filter
        lowered = pred.lower()
        if "deleted_at" in lowered:
            key = "filter:orders_soft_delete"
        elif "cancelled" in lowered:
            key = "filter:orders_not_cancelled"
        else:
            continue
        out.append(
            RuleCandidate(
                rule_key=key,
                rule_type="filter_required",
                statement=f"Correction added predicate: {pred}",
                evidence={"predicate": pred},
            )
        )

    added_dates = _dates(gold_sql) - _dates(attempt_sql)
    if any(d[4:] in _FISCAL_MONTH_DAY for d in added_dates):
        out.append(
            RuleCandidate(
                rule_key="calendar:fiscal",
                rule_type="calendar",
                statement=(
                    "Correction shifted the date window onto the house fiscal calendar "
                    f"({', '.join(sorted(added_dates))})."
                ),
                evidence={"added_dates": sorted(added_dates)},
            )
        )

    gold_tables = _tables(gold)
    added_tables = gold_tables - _tables(attempt)
    if "customers" in gold_tables and (
        "customers" in added_tables or _region_joined_on_product(attempt)
    ):
        out.append(
            RuleCandidate(
                rule_key="join:orders_customers_regions",
                rule_type="join_path",
                statement=(
                    "Correction attributed region via customers, not product_id."
                ),
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
