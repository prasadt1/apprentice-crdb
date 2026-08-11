"""Execution-graded signatures. Not an LLM judge."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize_cell(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def result_signature(columns: list[str], rows: list[tuple]) -> dict[str, Any]:
    normalized_rows = sorted(
        [tuple(canonicalize_cell(c) for c in row) for row in rows],
        key=lambda r: json.dumps(r, default=str),
    )
    payload = {
        "columns": list(columns),
        "row_count": len(rows),
        "rows": normalized_rows,
    }
    blob = json.dumps(payload, default=str, separators=(",", ":"), sort_keys=True).encode()
    return {
        "columns": list(columns),
        "row_count": len(rows),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def signatures_match(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    return (
        expected.get("sha256") == actual.get("sha256")
        and expected.get("row_count") == actual.get("row_count")
        and list(expected.get("columns") or []) == list(actual.get("columns") or [])
    )
