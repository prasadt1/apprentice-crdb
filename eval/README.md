# Frozen exam

50 questions, execution-graded. Frozen 2026-08-11 — see `FREEZE.md`.

| File | Role |
|------|------|
| `questions.json` | Full items (gold / naive / bait). **Do not feed this to an agent.** |
| `labels.json` | Frozen result signatures |
| `PROTOCOL.md` | Strata, invariants, limitations |
| `run_exam.py` | `questions` / `verify` / `grade` |
| `RESULTS.md` | Published scores |

Agent-facing exam (id + question text only):

```bash
python eval/run_exam.py questions
python eval/run_exam.py verify
apprentice baseline
```
