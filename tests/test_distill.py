from apprentice_crdb.distill import distill
from apprentice_crdb.gold_sql import GOLD_REVENUE_BY_REGION, NAIVE_REVENUE_BY_REGION


def test_distill_finds_soft_delete_and_refunds() -> None:
    rules = distill(NAIVE_REVENUE_BY_REGION, GOLD_REVENUE_BY_REGION)
    keys = {r.rule_key for r in rules}
    assert "filter:orders_soft_delete" in keys
    assert "metric:revenue" in keys
    assert "filter:orders_not_cancelled" in keys
    assert "calendar:fiscal" in keys
    assert "filter:generic" not in keys


def test_distill_maps_product_region_join_to_canonical_key() -> None:
    naive = """
    SELECT rg.name AS region, SUM(li.amount_cents) AS revenue_cents
    FROM order_lines li
    JOIN orders od ON od.order_id = li.order_id
    JOIN regions rg ON rg.region_id = li.product_id
    GROUP BY rg.name
    """
    gold = """
    SELECT rg.name AS region, SUM(li.amount_cents) AS revenue_cents
    FROM order_lines li
    JOIN orders od ON od.order_id = li.order_id
    JOIN customers cu ON cu.customer_id = od.customer_id
    JOIN regions rg ON rg.region_id = cu.region_id
    GROUP BY rg.name
    """
    keys = {r.rule_key for r in distill(naive, gold)}
    assert "join:orders_customers_regions" in keys
    assert "join:customers" not in keys
