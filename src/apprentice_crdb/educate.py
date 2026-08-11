"""Teach house rules into CockroachDB, then score the exam at each memory epoch."""

from __future__ import annotations

import json
import time
from pathlib import Path

from apprentice_crdb.distill import distill
from apprentice_crdb.memory import cluster_now, record_episode, recall_live, reset_memory, upsert_rule
from apprentice_crdb.paths import REPO_ROOT
from apprentice_crdb.student import choose_sql

QUESTIONS = REPO_ROOT / "eval" / "questions.json"
RUNS = REPO_ROOT / "eval" / "runs"

# Corrections applied in order. Each epoch is one AOST tick (GC window is 75 min).
CURRICULUM = (
    ("filters", ("q08", "q11")),
    ("revenue_and_fiscal", ("q01", "q02")),
    ("join_path", ("q06",)),
)


def load_items() -> dict[str, dict]:
    return {q["id"]: q for q in json.loads(QUESTIONS.read_text())}


def _keys_from_recall(rows: list[dict]) -> set[str]:
    return {r["rule_key"] for r in rows}


def answers_for(items: list[dict], live_keys: set[str]) -> dict[str, str]:
    return {q["id"]: choose_sql(q, live_keys) for q in items}


def teach_item(item: dict) -> list[str]:
    written: list[str] = []
    episode_id = record_episode(
        item["question"],
        item["naive_sql"],
        gold_sql=item["gold_sql"],
        result_ok=False,
    )
    for cand in distill(item["naive_sql"], item["gold_sql"]):
        upsert_rule(
            cand.rule_key,
            cand.rule_type,
            cand.statement,
            evidence_episode_id=episode_id,
        )
        written.append(cand.rule_key)
    return written


def run_education() -> dict:
    items_by_id = load_items()
    items = list(items_by_id.values())
    RUNS.mkdir(parents=True, exist_ok=True)
    reset_memory()

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

    reports = []
    for ep in epochs:
        keys = set(ep["live_keys"])
        answers = answers_for(items, keys)
        path = RUNS / f"answers_{ep['name']}.json"
        path.write_text(json.dumps(answers, indent=2) + "\n")
        ep["answers_path"] = str(path.relative_to(REPO_ROOT))
        reports.append(ep)

    return {"epochs": reports, "gc_ttlseconds": 4500}
