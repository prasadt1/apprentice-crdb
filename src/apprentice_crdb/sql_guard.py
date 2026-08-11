"""Reject anything that is not a single read-only SELECT/WITH."""

from __future__ import annotations

import re

_FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_USED = re.compile(r"--\s*used_rules:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|REPLACE|"
    r"TRUNCATE|GRANT|REVOKE|COPY|EXECUTE|CALL)\b",
    re.IGNORECASE,
)


def extract_sql(raw: str) -> str:
    fenced = _FENCE.findall(raw)
    body = fenced[-1] if fenced else raw
    lines = [ln for ln in body.splitlines() if not _USED.match(ln.strip())]
    return "\n".join(lines).strip().rstrip(";")


def extract_used_rules(raw: str) -> list[str]:
    m = _USED.search(raw)
    if not m:
        return []
    token = m.group(1).strip()
    if token.lower() in {"none", "", "-"}:
        return []
    return [p.strip() for p in token.split(",") if p.strip()]


def reject_reason(sql: str) -> str | None:
    if not sql:
        return "empty"
    compact = " ".join(sql.split())
    if ";" in sql.strip().rstrip(";"):
        return "multiple statements"
    head = compact.split(None, 1)[0].upper() if compact else ""
    if head not in {"SELECT", "WITH"}:
        return "must begin SELECT or WITH"
    if _FORBIDDEN.search(sql):
        return "ddl/dml keyword"
    return None
