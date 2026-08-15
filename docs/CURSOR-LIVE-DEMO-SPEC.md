# Build spec — live judge demo

**Author:** Claude (seam/spec lane) · **Date:** 2026-08-16 · **For:** Cursor
**Deadline:** submission Tue 18 Aug 17:00 EDT. Judging runs 19 Aug – 15 Sep, so whatever
we deploy must survive **a month unattended**.

## Why

The demo URL today is a static page whose content is already in the Devpost article. A
judge reads the article, clicks the URL, sees the same numbers, and leaves. The required
field is being spent on a duplicate.

Replace it with something a judge can actually operate: **ask the agent a question, with
and without its memory, and watch the answer change — live, against the real cluster and
real Bedrock.**

---

## The constraint that dictates the design — read this first

`gc.ttlseconds = 4500` (75 minutes). The published epochs are **~4 days old**, so their
MVCC history is long gone:

```
memory_zero  age 6060 min -> GARBAGE COLLECTED
filters      age 6060 min -> GARBAGE COLLECTED
revenue…     age 6059 min -> GARBAGE COLLECTED
join_path    age 6059 min -> GARBAGE COLLECTED
```

**Do not build live AOST replay of the published run. It cannot work** — `AS OF SYSTEM
TIME` at those timestamps returns `batch timestamp must be after replica GC threshold`.
Any design that "slides through t0…t3 live" is dead on arrival, and would fail in front of
a judge rather than in front of us.

So the split is:

| Surface | What it is | Where |
|---|---|---|
| **Live** | Ask any frozen question **with memory / without memory** → real CockroachDB recall, real Bedrock generation, real execution, real grading | Lambda |
| **Recorded** | The four-epoch curve and the AOST rewind story | existing static page + `eval/runs-*` JSON, labelled *recorded* |

The live half proves the memory layer works **now**. The recorded half carries the
time-travel finding, honestly labelled. Never blur the two.

---

## Architecture

```
GitHub Pages (unchanged URL)  ──fetch──>  Lambda Function URL  ──> CockroachDB Cloud (recall)
prasadt1.github.io/apprentice-crdb/                            ──> Amazon Bedrock (Titan + Nova)
                                                               ──> SQLite prop warehouse (in-Lambda, execute + grade)
```

- **The demo URL does not change.** Nothing in the Devpost form needs editing. If the
  Lambda is unreachable, the page still works (see *Degradation*).
- **AWS Lambda becomes a second AWS service** — currently the submission claims Bedrock
  only. This is real judging upside on "which AWS services and how", and it is honest:
  Lambda is running the agent.
- Credentials live only in Lambda env vars. **Nothing secret reaches the browser.**

---

## Lambda contract

Runtime Python 3.11. One function, one route, JSON in / JSON out.

**Request**
```json
{ "question_id": "q02", "mode": "with_memory" }     // mode: "with_memory" | "no_memory"
```

**Response**
```json
{
  "question": "What was total net revenue for fiscal Q2 2026? Return columns: revenue_cents.",
  "mode": "with_memory",
  "retrieved": [{"rule_key": "calendar:fiscal", "statement": "..."}],
  "sql": "WITH ...",
  "columns": ["revenue_cents"],
  "rows": [[95000]],
  "verdict": "correct",
  "expected_row_count": 1,
  "model_id": "amazon.nova-lite-v1:0",
  "elapsed_ms": 2400,
  "source": "live"
}
```

`verdict` ∈ `correct | wrong | rejected | error`. On rejection/error still return 200 with
the reason — the page must render a failure as a result, never as a broken widget.

**Handler steps**

1. Validate `question_id` against the 50 frozen ids. Reject anything else. **No free-text
   questions in v1** — that is the entire prompt-injection and cost surface, and we do not
   need it to be interactive.
2. Load `{id, question}` via the same accessor the agent uses. **Never** read `gold_sql`,
   `naive_sql`, `bait_sql`, `house_rules` or `notes` into the generation path — the
   existing leakage rule applies unchanged.
3. `with_memory` → `recall_similar(question, as_of=<now>, k=5)` against the live cluster.
   `no_memory` → skip retrieval entirely, empty memory block. *Do not* fake it by filtering
   in Python; just don't query.
4. Generate with Bedrock Converse, `temperature=0`, existing prompt contract.
5. `sql_guard` → execute against a freshly bootstrapped in-memory SQLite warehouse.
6. Grade with `result_signature` / `signatures_match` against `eval/labels.json`. Same
   grader as the published run — do not write a second one.

Reuse `agent.py`, `generate.py`, `memory.py`, `sql_guard.py`, `grader.py` as-is. **This
Lambda is a thin adapter over the shipped library, not a reimplementation.** If it needs a
behaviour the CLI doesn't have, that is a signal to stop and ask.

**Timestamp note:** call recall at *now*, not at a historical HLC. `_wait_until_closed`
adds up to ~4s for a now-read; either accept it or pass `now - 10s`, which is well inside
the GC window and needs no wait. Do not exceed a 20s function timeout.

---

## Safety and cost — non-negotiable

| Control | Value |
|---|---|
| Question set | fixed 50 frozen ids only |
| Model | `amazon.nova-lite-v1:0` (cheapest sane; Micro's invalid-SQL rate is worse on camera) |
| Per-IP rate limit | 20 requests / 10 min, in-memory in the function |
| Global daily cap | 500 generations; beyond that return recorded data with `"source":"recorded"` |
| `maxTokens` | 1024 |
| Secrets | Lambda env vars: `APPRENTICE_CRDB_DSN`, `APPRENTICE_GEN_MODEL`, `AWS_REGION`. Never in the repo, never in the response |
| IAM | execution role limited to `bedrock:InvokeModel` on the two model ARNs. Nothing else |
| CORS | allow only `https://prasadt1.github.io` |
| DB user | create a **read-only** SQL user for the Lambda. It must not be able to write `semantic_rules` |

At 500 Nova Lite calls/day the spend is cents. The cap exists so a scraper cannot turn it
into dollars, not because we expect the traffic.

---

## Frontend — add to `docs/index.html`, above the curves

Keep it plain; it must match the page, not fight it.

- A `<select>` of the 50 questions (group by stratum, label with the id).
- Two buttons: **Ask without memory** · **Ask with memory**.
- Result panel showing, in this order: **retrieved rules** (or "no rules retrieved"),
  the **generated SQL** in a `<pre>`, the **returned rows**, and a verdict chip
  (green `correct` / red `wrong`).
- A line under the panel: *"Live: CockroachDB recall + Amazon Bedrock generation +
  execution against the prop warehouse, graded against labels frozen at `b043aea`."*
- Suggested first pick: **q02** — cold it assumes the calendar quarter and answers 20,000;
  with memory it shifts to May–July, nets refunds, and answers 95,000. That is the video's
  beat, reproducible by the judge.

**Degradation (this is what protects the month of judging):** if the fetch fails, times out
after 25s, or returns `source: recorded`, render the recorded answer for that question from
`eval/runs-nova-lite/` with a visible note — *"Live endpoint unavailable; showing the
recorded run from 2026-08-14."* The page must never show a spinner that never resolves or
a raw error. Ship this path **first** and test it by pointing the endpoint at a dead URL.

---

## Deploy

1. Read-only CRDB SQL user; DSN into Lambda env.
2. Package with `psycopg[binary]`, `boto3`, `sqlglot`; bundle `eval/questions.json`,
   `eval/labels.json`, the warehouse `schema.sql` + `seed.sql`, and `src/apprentice_crdb/`.
3. Lambda Function URL, auth `NONE`, CORS locked to the Pages origin.
4. Timeout 25s, memory 512 MB.
5. Put the URL in one `const API =` at the top of the page script — one line to change, and
   one line to disable.

---

## Acceptance — verify before pointing the page at it

- [ ] `no_memory` on q02 returns **0 retrieved rules** and a wrong verdict
- [ ] `with_memory` on q02 returns rules and `verdict: correct`
- [ ] Grep proves the Lambda path never touches `gold_sql` / `naive_sql` / `bait_sql` / `house_rules`
- [ ] An invalid `question_id` is rejected, not passed to Bedrock
- [ ] Rate limit and daily cap both trip in testing
- [ ] Dead-endpoint test renders the recorded fallback, not an error
- [ ] Lambda's DB user cannot write (`INSERT` into `semantic_rules` fails)
- [ ] `python eval/run_exam.py verify` still green; frozen files untouched
- [ ] Response contains no DSN, ARN, account id, or hostname

## Do not

- Build AOST epoch sliding — the history is GC'd, it will fail live.
- Accept free-text questions in v1.
- Let the browser hold any credential.
- Re-implement the grader, the guard, or the prompt contract.
- Touch `eval/questions.json` or `eval/labels.json`.
- Claim "live agent" anywhere the data shown is recorded.
