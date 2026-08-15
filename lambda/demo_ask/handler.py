"""AWS Lambda Function URL handler — live ask (with / without memory).

Thin adapter over apprentice_crdb. See docs/CURSOR-LIVE-DEMO-SPEC.md.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any

# Bundled next to this file in the deployment zip.
os.environ.setdefault("APPRENTICE_GEN_MODEL", "amazon.nova-lite-v1:0")
os.environ.setdefault("APPRENTICE_GENERATOR", "bedrock")

from apprentice_crdb.agent import agent_facing_items, answer_with_receipt  # noqa: E402
from apprentice_crdb.grader import result_signature, signatures_match  # noqa: E402
from apprentice_crdb.memory import cluster_now  # noqa: E402
from apprentice_crdb.paths import REPO_ROOT  # noqa: E402

DAILY_CAP = 500
RATE_WINDOW_S = 600
RATE_MAX = 20

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}
_day_key = ""
_day_count = 0

_ITEMS: dict[str, str] | None = None
_LABELS: dict[str, Any] | None = None


def _respond(status: int, body: dict[str, Any]) -> dict[str, Any]:
    # CORS is configured on the Function URL only. Do not re-emit
    # Access-Control-* here — duplicate Allow-Origin makes browsers fail the fetch.
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def _client_ip(event: dict[str, Any]) -> str:
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    xff = headers.get("x-forwarded-for") or ""
    if xff:
        return xff.split(",")[0].strip()
    return (event.get("requestContext") or {}).get("http", {}).get("sourceIp") or "unknown"


def _rate_ok(ip: str) -> bool:
    now = time.time()
    with _lock:
        bucket = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW_S]
        if len(bucket) >= RATE_MAX:
            _hits[ip] = bucket
            return False
        bucket.append(now)
        _hits[ip] = bucket
        return True


def _daily_ok() -> bool:
    global _day_key, _day_count
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        if _day_key != today:
            _day_key = today
            _day_count = 0
        if _day_count >= DAILY_CAP:
            return False
        _day_count += 1
        return True


def _load_exam() -> tuple[dict[str, str], dict[str, Any]]:
    global _ITEMS, _LABELS
    if _ITEMS is None:
        _ITEMS = {i["id"]: i["question"] for i in agent_facing_items()}
    if _LABELS is None:
        import sys

        eval_dir = REPO_ROOT / "eval"
        if str(eval_dir) not in sys.path:
            sys.path.insert(0, str(eval_dir))
        import run_exam  # type: ignore

        _LABELS = run_exam.load_labels()
    return _ITEMS, _LABELS


def _as_of_now() -> str:
    """Live HLC minus ~10s — inside GC window, skips closed-timestamp wait."""
    raw = cluster_now()
    try:
        # HLC is decimal string; subtract ~10 logical seconds worth (1e10 ns scale ≈ 10s).
        val = float(raw.split(".")[0] if "." in raw else raw)
        return str(int(val - 10_000_000_000))
    except ValueError:
        return raw


def _ask(question_id: str, mode: str) -> dict[str, Any]:
    items, labels = _load_exam()
    if question_id not in items:
        return {
            "question": "",
            "mode": mode,
            "retrieved": [],
            "sql": None,
            "columns": [],
            "rows": [],
            "verdict": "rejected",
            "expected_row_count": 0,
            "model_id": os.environ.get("APPRENTICE_GEN_MODEL"),
            "elapsed_ms": 0,
            "source": "live",
            "error": f"unknown question_id: {question_id}",
        }
    if mode not in ("with_memory", "no_memory"):
        return {
            "question": items[question_id],
            "mode": mode,
            "retrieved": [],
            "sql": None,
            "columns": [],
            "rows": [],
            "verdict": "rejected",
            "expected_row_count": labels[question_id]["row_count"],
            "model_id": os.environ.get("APPRENTICE_GEN_MODEL"),
            "elapsed_ms": 0,
            "source": "live",
            "error": "mode must be with_memory or no_memory",
        }

    t0 = time.time()
    question = items[question_id]
    recall = mode == "with_memory"

    if recall and not os.environ.get("APPRENTICE_CRDB_DSN", "").strip():
        return {
            "question": question,
            "mode": mode,
            "retrieved": [],
            "sql": None,
            "columns": [],
            "rows": [],
            "verdict": "error",
            "expected_row_count": labels[question_id]["row_count"],
            "model_id": os.environ.get("APPRENTICE_GEN_MODEL"),
            "elapsed_ms": 0,
            "source": "recorded",
            "error": "APPRENTICE_CRDB_DSN not set on Lambda",
        }

    try:
        receipt = answer_with_receipt(
            question,
            as_of=_as_of_now() if recall else "0",
            recall=recall,
        )
    except Exception as exc:  # surface as result, not 500 — page must render it
        return {
            "question": question,
            "mode": mode,
            "retrieved": [],
            "sql": None,
            "columns": [],
            "rows": [],
            "verdict": "error",
            "expected_row_count": labels[question_id]["row_count"],
            "model_id": os.environ.get("APPRENTICE_GEN_MODEL"),
            "elapsed_ms": int((time.time() - t0) * 1000),
            "source": "live",
            "error": str(exc),
        }

    retrieved = [
        {"rule_key": r["rule_key"], "statement": r["statement"]}
        for r in (receipt.get("retrieved_rules") or [])
    ]
    model_id = receipt.get("model_id") or os.environ.get("APPRENTICE_GEN_MODEL")
    elapsed = int((time.time() - t0) * 1000)

    if receipt.get("rejected") or not receipt.get("execution", {}).get("ok"):
        err = receipt.get("rejected") or (receipt.get("execution") or {}).get("error")
        return {
            "question": question,
            "mode": mode,
            "retrieved": retrieved,
            "sql": receipt.get("sql"),
            "columns": [],
            "rows": [],
            "verdict": "rejected" if receipt.get("rejected") else "error",
            "expected_row_count": labels[question_id]["row_count"],
            "model_id": model_id,
            "elapsed_ms": elapsed,
            "source": "live",
            "error": err,
        }

    execution = receipt["execution"]
    columns = execution["columns"]
    rows = execution["rows"]
    actual = result_signature(columns, [tuple(r) for r in rows])
    ok = signatures_match(labels[question_id], actual)
    return {
        "question": question,
        "mode": mode,
        "retrieved": retrieved,
        "sql": receipt.get("sql"),
        "columns": columns,
        "rows": rows,
        "verdict": "correct" if ok else "wrong",
        "expected_row_count": labels[question_id]["row_count"],
        "model_id": model_id,
        "elapsed_ms": elapsed,
        "source": "live",
    }


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    method = (
        (event.get("requestContext") or {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "POST"
    ).upper()
    if method == "OPTIONS":
        # Preflight CORS is answered by the Function URL config.
        return {"statusCode": 204, "headers": {}, "body": ""}

    if method != "POST":
        return _respond(405, {"verdict": "error", "error": "POST only", "source": "live"})

    ip = _client_ip(event)
    if not _rate_ok(ip):
        return _respond(
            200,
            {
                "verdict": "error",
                "error": "rate limit: 20 requests / 10 min per IP",
                "source": "live",
                "retrieved": [],
                "sql": None,
                "columns": [],
                "rows": [],
                "mode": "",
                "question": "",
                "expected_row_count": 0,
                "model_id": os.environ.get("APPRENTICE_GEN_MODEL"),
                "elapsed_ms": 0,
            },
        )

    if not _daily_ok():
        # Cap tripped — page should fall back to recorded; signal with source.
        return _respond(
            200,
            {
                "verdict": "error",
                "error": "daily generation cap reached",
                "source": "recorded",
                "retrieved": [],
                "sql": None,
                "columns": [],
                "rows": [],
                "mode": "",
                "question": "",
                "expected_row_count": 0,
                "model_id": os.environ.get("APPRENTICE_GEN_MODEL"),
                "elapsed_ms": 0,
            },
        )

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _respond(200, {"verdict": "error", "error": "invalid JSON", "source": "live"})

    question_id = str(body.get("question_id") or "").strip()
    mode = str(body.get("mode") or "").strip()
    return _respond(200, _ask(question_id, mode))
