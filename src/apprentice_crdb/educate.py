"""Teach house rules into CockroachDB, then score the exam at each memory epoch."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apprentice_crdb.distill import distill
from apprentice_crdb.embeddings import get_embedder
from apprentice_crdb.memory import cluster_now, record_episode, recall_live, reset_memory, upsert_rule
from apprentice_crdb.paths import REPO_ROOT
from apprentice_crdb.student import choose_sql

QUESTIONS = REPO_ROOT / "eval" / "questions.json"
RUNS = REPO_ROOT / "eval" / "runs"

CURRICULUM = (
    ("filters", ("q08", "q11")),
    ("revenue_and_fiscal", ("q01", "q02")),
    ("join_path", ("q06",)),
)


def load_items() -> dict[str, dict]:
    return {q["id"]: q for q in json.loads(QUESTIONS.read_text())}


def _keys_from_recall(rows: list[dict]) -> set[str]:
    return {r["rule_key"] for r in rows}


def answers_oracle(items: list[dict], live_keys: set[str]) -> dict[str, str]:
    return {q["id"]: choose_sql(q, live_keys) for q in items}


def teach_correction(question: str, attempt_sql: str, correction_sql: str) -> dict[str, Any]:
    """Persist one correction and the reusable rules distilled from its SQL diff."""
    candidates = distill(attempt_sql, correction_sql)
    episode_id = record_episode(
        question,
        attempt_sql,
        gold_sql=correction_sql,
        result_ok=False,
    )
    rules = []
    for cand in candidates:
        rule_id = upsert_rule(
            cand.rule_key,
            cand.rule_type,
            cand.statement,
            evidence_episode_id=episode_id,
        )
        rules.append(
            {
                "id": str(rule_id),
                "rule_key": cand.rule_key,
                "rule_type": cand.rule_type,
                "statement": cand.statement,
            }
        )
    return {"episode_id": str(episode_id), "rules": rules}


def teach_item(item: dict) -> list[str]:
    report = teach_correction(
        item["question"],
        item["naive_sql"],
        item["gold_sql"],
    )
    return [rule["rule_key"] for rule in report["rules"]]


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _write_manifest(policy: str, epochs: list[dict], extra: dict[str, Any]) -> Path:
    path = RUNS / f"{policy}_manifest.json"
    payload = {
        "policy": policy,
        "embedder": get_embedder().provider,
        "region": os.environ.get("AWS_REGION", "us-east-1"),
        "gen_model": os.environ.get("APPRENTICE_GEN_MODEL", "amazon.nova-micro-v1:0"),
        "recall_k": int(os.environ.get("APPRENTICE_RECALL_K", "5")),
        "temperature": 0,
        "git": _git_head(),
        "utc_end": datetime.now(timezone.utc).isoformat(),
        "epochs": [{"name": e["name"], "as_of": e["as_of"]} for e in epochs],
        **extra,
    }
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path


def run_education(policy: str = "oracle") -> dict:
    if policy not in {"oracle", "agent", "both"}:
        raise ValueError(f"policy must be oracle|agent|both, got {policy!r}")

    items_by_id = load_items()
    items = list(items_by_id.values())
    RUNS.mkdir(parents=True, exist_ok=True)
    reset_memory()

    started = datetime.now(timezone.utc).isoformat()
    epochs = []
    t0 = cluster_now()
    epochs.append(
        {
            "name": "memory_zero",
            "as_of": t0,
            "taught": [],
            "live_keys": sorted(_keys_from_recall(recall_live(limit=50, as_of=t0))),
        }
    )

    for name, qids in CURRICULUM:
        taught: list[str] = []
        for qid in qids:
            taught.extend(teach_item(items_by_id[qid]))
        time.sleep(1.0)
        ts = cluster_now()
        keys = sorted(_keys_from_recall(recall_live(limit=50, as_of=ts)))
        epochs.append({"name": name, "as_of": ts, "taught": taught, "live_keys": keys})

    policies = ["oracle", "agent"] if policy == "both" else [policy]
    for pol in policies:
        for ep in epochs:
            if pol == "oracle":
                answers = answers_oracle(items, set(ep["live_keys"]))
                records = [{"id": qid, "sql": sql} for qid, sql in answers.items()]
            else:
                from apprentice_crdb.agent import answer_exam

                answers, records = answer_exam(as_of=ep["as_of"])
            ans_path = RUNS / f"{pol}_{ep['name']}_answers.json"
            ans_path.write_text(json.dumps(answers, indent=2) + "\n")
            audit_path = RUNS / f"{pol}_{ep['name']}_audit.json"
            audit_path.write_text(json.dumps(records, indent=2, default=str) + "\n")
            ep[f"{pol}_answers_path"] = str(ans_path.relative_to(REPO_ROOT))
            ep[f"{pol}_audit_path"] = str(audit_path.relative_to(REPO_ROOT))
        _write_manifest(pol, epochs, {"utc_start": started})

    # Back-compat path names for the existing oracle CLI grader loop.
    for ep in epochs:
        if "oracle_answers_path" in ep:
            ep["answers_path"] = ep["oracle_answers_path"]
        elif "agent_answers_path" in ep:
            ep["answers_path"] = ep["agent_answers_path"]

    return {"epochs": epochs, "gc_ttlseconds": 4500, "policy": policy}
