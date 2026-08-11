from apprentice_crdb.sql_guard import extract_sql, extract_used_rules, reject_reason


def test_extracts_fenced_select_and_used_rules() -> None:
    raw = """here you go
```sql
SELECT name FROM regions
```
-- used_rules: aaa, bbb
"""
    assert extract_sql(raw) == "SELECT name FROM regions"
    assert extract_used_rules(raw) == ["aaa", "bbb"]
    assert reject_reason(extract_sql(raw)) is None


def test_rejects_dml_and_empty() -> None:
    assert reject_reason("") == "empty"
    assert reject_reason("DELETE FROM orders") == "must begin SELECT or WITH"
    assert reject_reason("SELECT 1; SELECT 2") == "multiple statements"
    assert reject_reason("SELECT 1 FROM orders; DROP TABLE orders") == "multiple statements"


def test_used_rules_none() -> None:
    assert extract_used_rules("SELECT 1\n-- used_rules: none") == []
