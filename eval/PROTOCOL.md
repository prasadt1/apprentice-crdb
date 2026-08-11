# Frozen exam protocol

I froze this exam before the agent existed in any tunable form. The learning curve
Apprentice publishes is scored against these 50 questions, and after `FREEZE.md` the
questions and labels do not change — if a label turns out to be wrong, the mistake is
recorded as an erratum in `eval/RESULTS.md`, never edited away. This is the same
discipline as Premortem: the benchmark is committed before the system it grades.

Authored 2026-08-11 by Claude per `docs/LABOR.md` (exam protocol + labels are Claude's
lane; Cursor implements the agent only after the freeze exists).

## What is graded, exactly

Every question is graded by **execution result signature** — `result_signature` in
`src/apprentice_crdb/grader.py`, reused unchanged. An answer is correct iff its
executed result matches the frozen label: same column names in the same order, same
row count, same canonicalized rows (row *order* is ignored; floats rounded to 6
decimal places). There is no LLM judge anywhere in the loop.

Because column names are part of the signature, **every question text states its
output contract explicitly** ("Return columns: region, revenue_cents"). An agent is
never marked wrong for column-name guessing; the contract is in the question it reads.

## The warehouse

The fixed SQLite prop warehouse (`src/apprentice_crdb/warehouse/schema.sql` +
`seed.sql`), bootstrapped fresh for every run. The house semantics being examined are
the five canonical rules in `src/apprentice_crdb/house_rules.py`:

1. `metric:revenue` — revenue is net of refunds, on live non-cancelled orders
2. `filter:orders_soft_delete` — soft-deleted orders are not live facts
3. `filter:orders_not_cancelled` — cancelled orders are not revenue
4. `calendar:fiscal` — FY starts 1 Feb; FQ1 Feb–Apr, FQ2 May–Jul, FQ3 Aug–Oct, FQ4 Nov–Jan
5. `join:orders_customers_regions` — region attribution goes through the customer

Window glossary used in the questions: "fiscal 2026" = 2026-02-01 to 2027-02-01;
"fiscal Q3 2026" = 2026-08-01 to 2026-11-01; "calendar 2026" = the calendar year.

## Item anatomy

Each item in `questions.json` carries:

- `question` — natural-language ask including the output contract. **This is the only
  field an agent may see.** The agent-facing exam is emitted by
  `run_exam.py questions`; harness code must consume that, not the raw file.
- `gold_sql` — the house-correct query the label was computed from.
- `naive_sql` — a plausible day-0 attempt with zero house knowledge: competent SQL,
  no soft-delete filter, no cancellation filter, gross instead of net, calendar
  windows for quarter/FY language, and (on join items) region misattributed via the
  product. It is a **diagnostic fixture** used to prove each item discriminates; it is
  not graded, not shown to the agent, and not a claim about how any particular model
  fails.
- `bait_sql` — on the six `regression_bait` items only: what a plausibly
  over-generalized rule produces (see below).
- `stratum`, `house_rules`, `notes` — taxonomy and the divergence rationale.

## Strata (n = 50)

| Stratum | n | Intent |
|---|---|---|
| `metric_revenue` | 10 | Net-of-refunds / cancelled-excluded semantics at total, customer, product, region, average, and ranking grain |
| `soft_delete` | 8 | `deleted_at IS NULL` changes the number, the count, or the top-1 |
| `fiscal_calendar` | 8 | 1-Feb fiscal year vs calendar windows, including a zero-revenue quarter and a refunds-table window |
| `join_path` | 6 | Region resolved through the customer; misattribution via product is the divergent counterfactual |
| `composition` | 8 | Unseen questions needing ≥2 rules at once (quarter comparisons, category rankings, ratios, ordinal ranks) |
| `unaffected` | 6 | Gold **is** the naive answer; memory must not over-apply rules |
| `trap` | 4 | Decoy phrasing ("Q3" without "fiscal", "amount", "order value", "FY so far") that still wants house semantics |

Interleaving: item order is a fixed-seed shuffle (seed 20260813) with no three
consecutive items sharing a stratum; the flagship regional-revenue question is pinned
at `q01`. Ids are `q01`–`q50` and carry no stratum information.

## Regression baits (published markers)

Six items are marked `regression_bait` — places where a plausible over-generalization
of a correct lesson makes the agent *worse*. These become the red markers on the
published learning curve:

| Item | Over-generalization it catches | Wrong answer it produces |
|---|---|---|
| q31 (calendar Q3 revenue) | "quarters are always fiscal" | 290000 instead of 115000 |
| q36 (orders placed) | "always exclude cancelled" applied to a placed-count | 4 instead of 5 |
| q50 (gross billings FQ2) | "revenue always nets refunds" applied to an explicit gross | 95000 instead of 120000 |
| q03 (soft-deleted count) | "always filter deleted_at IS NULL" | 0 instead of 1 |
| q07 (cancelled count) | "always exclude cancelled" | 0 instead of 1 |
| q47 (audit of deleted billings) | "always filter deleted_at IS NULL" | 0 instead of 500000 |

Each `bait_sql` was executed and verified to disagree with the gold label.

## Invariants verified before freezing

Run `python eval/run_exam.py verify` to re-check all of these at any time:

1. All 50 `gold_sql` execute on a fresh bootstrap and reproduce `labels.json` exactly.
2. Every `gold_sql` result was first asserted against **hand-computed expected rows**
   derived from the seed by hand, then the label was generated from the execution.
3. For every stratum except `unaffected`: `naive_sql` executes and its signature
   **differs** from gold. For `unaffected`: it **equals** gold.
4. Every `bait_sql` executes and differs from gold.
5. Strata counts match the table above; ids unique; 50 questions, 50 labels.
6. Leakage: no exam statement (normalized) equals a statement in
   `src/apprentice_crdb/gold_sql.py`, and no normalized line of ≥30 characters is
   shared with `gold_sql.py` or `tests/*.py`. The exam was authored independently of
   the demo-beat SQL (different aliases, different query structure).

   **Checker correction, 2026-08-11 (post-freeze, no frozen artifact touched).** As
   first written, this check re-read `tests/` from the working tree, so tests added
   *after* the freeze could fail a claim about authorship *before* it. Cursor
   subsequently added `test_distill.py` cases using the exam's join patterns — correct
   work, but it tripped the check. Leakage is now evaluated against `gold_sql.py` and
   `tests/*.py` **as of the freeze commit `b043aea`** (plus `gold_sql.py` at HEAD, since
   "demo SQL stays distinct from exam SQL" is a live invariant). `verify` prints which
   scope it used and warns if git is unavailable. `questions.json` and `labels.json`
   were not modified: their sha256 still match `FREEZE.md` exactly.

Baseline smoke test: grading the `naive_sql` set as if it were an agent scores
**6/50 = 12%** — exactly the unaffected stratum. That is the exam's zero-knowledge
floor for a competent SQL writer; the memory-zero baseline agent is expected to land
near it, and the education run is measured from there.

## Limitations, stated plainly

- The seed is deliberately tiny (6 orders). Items are semantically distinct — different
  grains, windows, metrics, and entities — but the arithmetic is small enough to check
  by hand, which is the point of a frozen label set. Statistical power comes from the
  50-item breadth, not data volume.
- Every order in the seed has exactly one line, so order-level refunds attribute to a
  line's product/category without a proration policy. Category-grain revenue questions
  are valid under this seed and say nothing about multi-line proration.
- `naive_sql` is an authored counterfactual. The divergence invariant proves each item
  *can* discriminate; it does not predict any specific model's failure mode.
- Three-labeler blind verification (the Premortem-grade option in the brief) was not
  done — solo timeline. The compensating control is invariant #2: every label was
  double-derived (hand-computed expectation first, execution second, and the two had
  to agree before anything was written).

## Freeze and errata

`FREEZE.md` records the sha256 of `questions.json` and `labels.json` and the freeze
date. After that commit: no edits to either file, ever. Wrong label? Erratum in
`eval/RESULTS.md` with the item id, what was wrong, and the corrected value —
scored runs keep the frozen label so the published curve is computed against exactly
what was committed. `run_exam.py emit-labels` refuses to run once `FREEZE.md` exists.
