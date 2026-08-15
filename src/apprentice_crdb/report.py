"""Re-grade the published model artifacts and summarize their memory curve."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from typing import Any

from apprentice_crdb.paths import REPO_ROOT

EPOCHS = ("memory_zero", "filters", "revenue_and_fiscal", "join_path")
ARMS = ("nova-micro", "nova-lite")


def published_result() -> dict[str, Any]:
    eval_dir = REPO_ROOT / "eval"
    if str(eval_dir) not in sys.path:
        sys.path.insert(0, str(eval_dir))
    import run_exam  # type: ignore

    curves = {}
    for arm in ARMS:
        curve = []
        for epoch in EPOCHS:
            path = eval_dir / f"runs-{arm}" / f"agent_{epoch}_answers.json"
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                run_exam.cmd_grade(str(path))
            result = json.loads(capture.getvalue())
            curve.append({"epoch": epoch, "correct": result["correct"], "total": result["total"]})
        curves[arm] = curve

    questions = json.loads((eval_dir / "questions.json").read_text())
    rule_bearing = [question for question in questions if question["house_rules"]]
    retrieval = {}
    for arm in ARMS:
        audit_path = eval_dir / f"runs-{arm}" / "agent_join_path_audit.json"
        audit = {row["id"]: row for row in json.loads(audit_path.read_text())}
        covered = sum(
            set(question["house_rules"]).issubset(audit[question["id"]]["retrieved_rule_keys"])
            for question in rule_bearing
        )
        retrieval[arm] = {"covered": covered, "total": len(rule_bearing)}

    return {"epochs": list(EPOCHS), "curves": curves, "full_memory_retrieval": retrieval}


def format_published_result(result: dict[str, Any]) -> str:
    lines = [
        "FROZEN EXECUTION-GRADED RUN",
        "epoch                  nova-micro  nova-lite",
    ]
    for index, epoch in enumerate(result["epochs"]):
        micro = result["curves"]["nova-micro"][index]
        lite = result["curves"]["nova-lite"][index]
        lines.append(f"{epoch:<22} {micro['correct']:>2}/50       {lite['correct']:>2}/50")
    micro_retrieval = result["full_memory_retrieval"]["nova-micro"]
    lite_retrieval = result["full_memory_retrieval"]["nova-lite"]
    lines.append(
        "full-memory retrieval  "
        f"{micro_retrieval['covered']}/{micro_retrieval['total']}       "
        f"{lite_retrieval['covered']}/{lite_retrieval['total']}"
    )
    return "\n".join(lines)
