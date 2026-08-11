"""Rule-gated exam answers.

Isolates *memory contents* from LLM variance. SQL bodies stay in the frozen exam
fixtures (naive / gold / bait). The student only chooses which body to run based
on which rule_keys are live in CockroachDB (including AS OF a timestamp).

This is the ablation the curve measures. A Bedrock generator is a later demo skin.
"""

from __future__ import annotations

# Over-generalization the bait items catch, once that rule is in memory.
BAIT_TRIGGER = {
    "q03": "filter:orders_not_cancelled",
    "q07": "filter:orders_not_cancelled",
    "q31": "metric:revenue",
    "q36": "calendar:fiscal",
    "q47": "filter:orders_soft_delete",
    "q50": "filter:orders_not_cancelled",
}


def choose_sql(item: dict, live_rule_keys: set[str]) -> str:
    qid = item["id"]
    trigger = BAIT_TRIGGER.get(qid)
    if item.get("regression_bait") and trigger and trigger in live_rule_keys:
        bait = item.get("bait_sql")
        if bait:
            return bait
    needed = set(item.get("house_rules") or [])
    if needed <= live_rule_keys:
        return item["gold_sql"]
    return item["naive_sql"]
