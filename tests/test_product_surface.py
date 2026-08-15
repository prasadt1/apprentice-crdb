from uuid import UUID

from apprentice_crdb.generate import Completion


def test_teach_correction_persists_distilled_rules(monkeypatch) -> None:
    from apprentice_crdb import educate

    episode_id = UUID("00000000-0000-0000-0000-000000000001")
    written = []
    monkeypatch.setattr(educate, "record_episode", lambda *a, **k: episode_id)

    def fake_upsert(rule_key, rule_type, statement, **kwargs):
        written.append((rule_key, rule_type, statement, kwargs["evidence_episode_id"]))
        return UUID(int=len(written) + 1)

    monkeypatch.setattr(educate, "upsert_rule", fake_upsert)
    report = educate.teach_correction(
        "What were live hardware billings?",
        "SELECT SUM(amount_cents) FROM orders",
        (
            "SELECT SUM(amount_cents) FROM orders "
            "WHERE deleted_at IS NULL AND status <> 'cancelled'"
        ),
    )

    assert [rule["rule_key"] for rule in report["rules"]] == [
        "filter:orders_soft_delete",
        "filter:orders_not_cancelled",
    ]
    assert all(row[3] == episode_id for row in written)


def test_answer_with_receipt_executes_sql(monkeypatch) -> None:
    from apprentice_crdb import agent

    monkeypatch.setattr(
        agent,
        "recall_similar",
        lambda *a, **k: [
            {
                "id": "00000000-0000-0000-0000-000000000010",
                "rule_key": "filter:orders_soft_delete",
                "statement": "Ignore soft-deleted orders.",
            }
        ],
    )

    class Fake:
        model_id = "fake"

        def complete(self, system: str, user: str) -> Completion:
            return Completion(
                "```sql\nSELECT COUNT(*) AS n FROM regions\n```\n-- used_rules: none",
                "fake",
            )

    receipt = agent.answer_with_receipt(
        "How many regions exist?",
        as_of="1.0",
        generator=Fake(),
        k=1,
    )

    assert receipt["retrieved_rule_keys"] == ["filter:orders_soft_delete"]
    assert receipt["execution"] == {
        "ok": True,
        "columns": ["n"],
        "rows": [[3]],
    }


def test_cli_exposes_teach_answer_and_probe() -> None:
    from apprentice_crdb.cli import build_parser

    teach = build_parser().parse_args(
        ["teach", "question", "--attempt", "attempt.sql", "--correction", "correction.sql"]
    )
    answer = build_parser().parse_args(["answer", "question", "--as-of", "1.0", "--k", "3"])
    probe = build_parser().parse_args(["probe", "q31", "--as-of", "1.0"])

    assert teach.cmd == "teach"
    assert answer.cmd == "answer"
    assert answer.k == 3
    assert probe.cmd == "probe"
    assert probe.exam_id == "q31"


def test_published_report_regrades_archived_runs() -> None:
    from apprentice_crdb.report import format_published_result, published_result

    result = published_result()
    text = format_published_result(result)

    assert [row["correct"] for row in result["curves"]["nova-micro"]] == [8, 21, 18, 13]
    assert [row["correct"] for row in result["curves"]["nova-lite"]] == [14, 19, 19, 16]
    assert result["full_memory_retrieval"]["nova-micro"] == {"covered": 44, "total": 44}
    assert "full-memory retrieval  44/44       44/44" in text
