from apprentice_crdb.gold_sql import GOLD_REVENUE_BY_REGION, NAIVE_REVENUE_BY_REGION
from apprentice_crdb.grader import result_signature, signatures_match
from apprentice_crdb.warehouse_db import bootstrap, connect, execute_sql


def test_house_rules_change_the_answer() -> None:
    conn = connect()
    bootstrap(conn)
    n_cols, n_rows = execute_sql(conn, NAIVE_REVENUE_BY_REGION)
    g_cols, g_rows = execute_sql(conn, GOLD_REVENUE_BY_REGION)
    assert not signatures_match(result_signature(n_cols, n_rows), result_signature(g_cols, g_rows))


def test_gold_fiscal_q3_net_live_only() -> None:
    conn = connect()
    bootstrap(conn)
    _, rows = execute_sql(conn, GOLD_REVENUE_BY_REGION)
    by_region = {r[0]: r[1] for r in rows}
    assert by_region["AMER"] == 250000
    assert by_region["EMEA"] == 40000
    assert "APAC" not in by_region  # only the soft-deleted Sept order


def test_naive_includes_deleted_and_cancelled_and_calendar_july() -> None:
    conn = connect()
    bootstrap(conn)
    _, rows = execute_sql(conn, NAIVE_REVENUE_BY_REGION)
    by_region = {r[0]: r[1] for r in rows}
    assert by_region["APAC"] == 500000
    assert by_region["AMER"] == 100000
    assert by_region["EMEA"] == 120000
