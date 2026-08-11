"""Canonical house semantics for the demo warehouse.

These are the *truth* the frozen exam grades against. The naive agent does not
get this module injected into its prompt on day 0.
"""

from __future__ import annotations

# Fiscal year starts 1 February. Q1=Feb–Apr, Q2=May–Jul, Q3=Aug–Oct, Q4=Nov–Jan.
FISCAL_YEAR_START_MONTH = 2

HOUSE_RULES = (
    {
        "rule_key": "metric:revenue",
        "rule_type": "metric_definition",
        "statement": (
            "revenue is net of refunds: SUM(order_lines.amount_cents) for orders "
            "where deleted_at IS NULL AND status != 'cancelled', minus SUM(refunds.amount_cents) "
            "on those same orders."
        ),
    },
    {
        "rule_key": "filter:orders_soft_delete",
        "rule_type": "filter_required",
        "statement": "Always filter orders.deleted_at IS NULL. Soft-deleted orders are not live facts.",
    },
    {
        "rule_key": "filter:orders_not_cancelled",
        "rule_type": "filter_required",
        "statement": "Cancelled orders (status = 'cancelled') are not revenue.",
    },
    {
        "rule_key": "calendar:fiscal",
        "rule_type": "calendar",
        "statement": (
            "Fiscal year starts 1 February. Fiscal Q1=Feb–Apr, Q2=May–Jul, "
            "Q3=Aug–Oct, Q4=Nov–Jan. Do not use calendar quarters."
        ),
    },
    {
        "rule_key": "join:orders_customers_regions",
        "rule_type": "join_path",
        "statement": (
            "Region attribution: order_lines → orders → customers → regions. "
            "Do not attribute via product or a guessed region column on orders."
        ),
    },
)


def fiscal_quarter_predicate(column: str = "orders.ordered_at", year: int = 2026, quarter: int = 3) -> str:
    """SQL predicate (SQLite date strings) for a fiscal quarter."""
    # Q1 starts Feb 1 of `year`; Q2 May 1; Q3 Aug 1; Q4 Nov 1; Q4 ends Jan 31 of year+1.
    starts = {
        1: (year, 2, 1),
        2: (year, 5, 1),
        3: (year, 8, 1),
        4: (year, 11, 1),
    }
    y, m, d = starts[quarter]
    if quarter < 4:
        end_y, end_m = y, m + 3
    else:
        end_y, end_m = y + 1, 2
    start = f"{y:04d}-{m:02d}-{d:02d}"
    end = f"{end_y:04d}-{end_m:02d}-01"
    return f"{column} >= '{start}' AND {column} < '{end}'"
