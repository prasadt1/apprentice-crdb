from pathlib import Path

from apprentice_crdb.generate import Completion
from apprentice_crdb.paths import PACKAGE_DIR


BANNED = ("gold_sql", "naive_sql", "bait_sql", "house_rules")


def test_answering_modules_do_not_name_exam_fixtures() -> None:
    for name in ("agent.py", "generate.py", "sql_guard.py"):
        text = (PACKAGE_DIR / name).read_text()
        for token in BANNED:
            assert token not in text, f"{name} contains {token}"


def test_agent_facing_items_are_id_and_question_only() -> None:
    import sys

    from apprentice_crdb.paths import REPO_ROOT

    sys.path.insert(0, str(REPO_ROOT / "eval"))
    import run_exam  # type: ignore

    items = run_exam.agent_facing_items()
    assert len(items) == 50
    assert set(items[0]) == {"id", "question"}


def test_answer_one_with_empty_memory_and_fake_generator(monkeypatch) -> None:
    from apprentice_crdb import agent

    monkeypatch.setattr(agent, "recall_similar", lambda *a, **k: [])

    class Fake:
        model_id = "fake"

        def complete(self, system: str, user: str) -> Completion:
            assert "regions" in system
            assert user == "How many regions exist?"
            return Completion(
                "```sql\nSELECT COUNT(*) AS n FROM regions\n```\n-- used_rules: none",
                "fake",
            )

    row = agent.answer_one("How many regions exist?", as_of="1.0", generator=Fake())
    assert row["rejected"] is None
    assert row["sql"] == "SELECT COUNT(*) AS n FROM regions"
    assert row["retrieved_rule_ids"] == []
