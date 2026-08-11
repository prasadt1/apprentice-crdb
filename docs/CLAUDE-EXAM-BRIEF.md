# Claude — frozen 50-question exam (do this first)

Paste this into a **fresh Claude session** with `/Users/prasadt1/Apprentice` as context. This is your job. Cursor will not author `eval/labels.json`.

Deadline context: **2026-08-18**. Today is **2026-08-11**. Exam must exist before any graded learning run.

---

## What you are building

A **frozen, execution-graded 50-question exam** for Apprentice.

Product (do not drift): *an analyst agent that ships its own learning curve*. Chat Q&A is the vehicle. You are building the **receipt** — the exam the curve is scored on.

Same discipline as Premortem: labels committed **before** the system that will be graded exists in a tunable form. Cursor already has warehouse + grader + distill + memory schema. **Do not wait for the agent.** Freeze against the warehouse + gold SQL.

## What already exists (read these, do not rewrite)

| Path | Why |
|------|-----|
| `docs/superpowers/specs/2026-08-09-apprentice-design.md` | Locked design |
| `src/apprentice_crdb/warehouse/schema.sql` + `seed.sql` | Prop warehouse + data |
| `src/apprentice_crdb/house_rules.py` | Canonical house semantics |
| `src/apprentice_crdb/grader.py` | `result_signature` — this is the grader, reuse it |
| `src/apprentice_crdb/gold_sql.py` | Demo beat SQL **only** — **do not copy these into the exam** |
| `eval/README.md` | Empty freeze slot |

## Deliverables (write these files)

```
eval/PROTOCOL.md          # how labels were made; strata; leakage rules
eval/questions.json       # 50 items: id, question (NL), gold_sql, stratum, house_rules[]
eval/labels.json          # gold signatures + metadata (frozen)
eval/FREEZE.md            # sha256 of questions.json + labels.json + date + “no more edits”
eval/run_exam.py          # adapter: execute gold_sql (and later agent sql) via grader
```

`run_exam.py` may evolve. **`questions.json` and `labels.json` may not** after FREEZE.md.

### `questions.json` item shape

```json
{
  "id": "q01",
  "question": "What was fiscal Q3 2026 net revenue by region?",
  "gold_sql": "SELECT ...",
  "stratum": "metric_revenue",
  "house_rules": ["metric:revenue", "filter:orders_soft_delete", "calendar:fiscal"],
  "notes": "Must disagree with calendar-Q3 naive SUM"
}
```

Ids: `q01`…`q50`. Neutral order — **interleave strata**. Do not name files by rule.

### `labels.json` item shape

Compute with the **existing** `result_signature` against a freshly bootstrapped warehouse (same seed).

```json
{
  "id": "q01",
  "columns": ["region", "revenue_cents"],
  "row_count": 2,
  "sha256": "..."
}
```

If gold SQL does not execute, **fix the SQL** — do not invent a signature.

## Strata (n=50)

Cover the four house rules plus traps. Suggested split (adjust if you have a better taxonomy, but **write it in PROTOCOL.md**):

| Stratum | n | Intent |
|---------|---|--------|
| `metric_revenue` | 10 | Net of refunds; cancelled excluded |
| `soft_delete` | 8 | `deleted_at IS NULL` changes the answer |
| `fiscal_calendar` | 8 | FY starts 1 Feb; Q3 = Aug–Oct 2026 ≠ calendar Q3 |
| `join_path` | 6 | region via customers, not a guessed path |
| `composition` | 8 | Unseen questions needing **≥2 rules** (the “day-5” demo beat) |
| `unaffected` | 6 | Gold = naive; memory must **not** over-apply rules (over-erasure analog) |
| `trap` | 4 | Decoys: calendar language that still wants fiscal; “amount” vs revenue |

Gold SQL must make **naive-vs-gold disagree** on every item except `unaffected`.

## Hard rules

1. **Do not copy** `gold_sql.py` / demo questions into the exam. Leakage check: no shared SQL text with `src/apprentice_crdb/gold_sql.py` or `tests/`.
2. Grade by **execution signature**, never LLM-as-judge.
3. Every `gold_sql` must run on the seeded SQLite warehouse (`apprentice warehouse-demo` path).
4. Seed is small — questions must still be **semantically distinct** (different grain, filters, time windows, joins), not 50 paraphrases of revenue-by-region.
5. Include at least **3 items where a plausible over-general rule would make the agent worse** (these become the published regression markers). Mark them `"regression_bait": true` in questions.json.
6. First person in PROTOCOL.md if you write narrative. No “GDPR”, no copilot framing.
7. After freeze: if a label is wrong, **erratum in `eval/RESULTS.md`** — do not edit labels.json.

## Verification you must run before FREEZE.md

- [ ] 50/50 gold_sql execute
- [ ] sha256 recorded
- [ ] Leakage grep vs `gold_sql.py` and `tests/` is clean
- [ ] Naive-vs-gold disagree except `unaffected`
- [ ] Stratum counts match PROTOCOL.md

Optional (Premortem-grade, if time): three blind labelers given warehouse schema+seed+taxonomy only, not your labels — report agreement in PROTOCOL.md.

## What you are not doing

- Not implementing the Bedrock agent
- Not tuning distill.py against the exam
- Not writing the learning-curve UI
- Not renaming the product or reopening Expunction/GASLIGHT/KinKeeper

When FREEZE.md exists, tell Prasad/Cursor the commit hash. Then Cursor may run memory-zero baseline and education.
