from apprentice_crdb.distill import distill
from apprentice_crdb.gold_sql import GOLD_REVENUE_BY_REGION, NAIVE_REVENUE_BY_REGION


def test_distill_finds_soft_delete_and_refunds() -> None:
    rules = distill(NAIVE_REVENUE_BY_REGION, GOLD_REVENUE_BY_REGION)
    keys = {r.rule_key for r in rules}
    assert "filter:orders_soft_delete" in keys
    assert "metric:revenue" in keys
    assert "filter:orders_not_cancelled" in keys
