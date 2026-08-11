from apprentice_crdb.student import choose_sql


def test_empty_memory_uses_naive() -> None:
    item = {
        "id": "q01",
        "house_rules": ["metric:revenue"],
        "naive_sql": "SELECT 1",
        "gold_sql": "SELECT 2",
    }
    assert choose_sql(item, set()) == "SELECT 1"


def test_complete_memory_uses_gold() -> None:
    item = {
        "id": "q01",
        "house_rules": ["metric:revenue"],
        "naive_sql": "SELECT 1",
        "gold_sql": "SELECT 2",
    }
    assert choose_sql(item, {"metric:revenue"}) == "SELECT 2"


def test_bait_fires_when_overgeneral_rule_is_live() -> None:
    item = {
        "id": "q47",
        "regression_bait": True,
        "house_rules": [],
        "naive_sql": "SELECT naive",
        "gold_sql": "SELECT gold",
        "bait_sql": "SELECT bait",
    }
    assert choose_sql(item, {"filter:orders_soft_delete"}) == "SELECT bait"
    assert choose_sql(item, set()) == "SELECT gold"
