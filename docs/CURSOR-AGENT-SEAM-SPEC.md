# Seam spec — replace the selector with a real generator

**Author:** Claude (seam review lane, `docs/LABOR.md`) · **Date:** 2026-08-11 · **For:** Cursor

## Why this exists

`student.choose_sql()` does not write SQL. It picks among three bodies I authored inside
the frozen exam (`gold_sql` / `naive_sql` / `bait_sql`) by testing whether an item's
`house_rules` metadata is a subset of the live rule keys. Accuracy at each epoch is
therefore a deterministic function of static metadata and the teaching schedule — the
curve **cannot fail**, and the six misses are the six I hand-wired in `BAIT_TRIGGER`.

Two consequences: the published number was implied, not measured; and the demo path is
not the path the numbers came from. Both are the exact defects this project's
methodology exists to catch.

Fix: **Amazon Bedrock generates the SQL from the question plus rules retrieved from
CockroachDB by vector similarity.** Same frozen exam, same grader, same AOST epochs.
This also converts AWS from zero to load-bearing and makes the vector index real.

**Do not change:** `eval/questions.json`, `eval/labels.json`, `grader.py`, the freeze.

---

## 1. Embeddings — make the vectors real

`APPRENTICE_EMBEDDER=bedrock` (already implemented in `embeddings.py`). Titan
`amazon.titan-embed-text-v2:0`, 384 dims, matching the existing column. Re-embed every
rule on write. Record `provider` in the run artifact so a mock run can never be confused
with a Titan run.

## 2. Retrieval — semantic, tenant-safe, AOST-aware

Replace the bulk `recall_live(limit=50)` fetch on the answering path with similarity
search:

```
BEGIN AS OF SYSTEM TIME '<hlc>';
  SELECT rule_id, rule_key, rule_type, statement
  FROM semantic_rules
  WHERE superseded_by IS NULL
  ORDER BY embedding <-> $1        -- $1 = Titan embedding of the question
  LIMIT $2;                        -- APPRENTICE_RECALL_K, default 5
COMMIT;
```

The `AS OF SYSTEM TIME` wrapper is what makes epoch replay honest: replaying
`memory_zero` must return zero rules because none existed at that timestamp — not
because we filtered them out in Python. Keep `recall_live()` for the CLI/inspection
view; the answering path gets its own function.

## 3. Generation — Bedrock Converse, model-agnostic

Use `bedrock-runtime.converse()`, **not** a model-specific invoke body. Model access is
still unconfirmed, and Converse means whichever model lands (Anthropic, Nova, DeepSeek,
Llama) the code does not change. Model id from `APPRENTICE_GEN_MODEL`; record the
resolved id in every artifact.

`temperature=0`, `topP=1`, fixed `maxTokens`. Every generated string is persisted — see §5.

### Prompt contract

**System:** the analyst role, the warehouse DDL, and the output contract.

- Inject `src/apprentice_crdb/warehouse/schema.sql` verbatim. A real analyst sees the schema.
- **Never inject** `house_rules.py` (that is the truth being learned), `seed.sql` (that is
  the data being queried), or anything from `eval/`.
- Instruct: single read-only statement, must begin `SELECT` or `WITH`; return the SQL in
  one ```sql fence; on the final line emit `-- used_rules: <rule_id,...>` or
  `-- used_rules: none`.

**Memory block:** the retrieved rules, delimited, each as `rule_id · rule_key ·
statement`. At `memory_zero` this block is literally empty — do not substitute a
placeholder that hints rules exist.

**User:** the `question` text from `run_exam.py questions`, nothing else.

### Hard leakage rule

The generator consumes **only** `{id, question}`. If any code path can reach
`gold_sql`, `naive_sql`, `bait_sql`, `house_rules`, or `notes`, the run is void. Load the
agent-facing exam through `run_exam.py questions`; do not read `questions.json` in the
agent path.

### Execution guard

Reject anything not starting with `SELECT`/`WITH`, containing more than one statement, or
containing DDL/DML keywords. Execute against a freshly bootstrapped in-memory warehouse
per item. Any rejection, exception, or timeout grades as **wrong** — never as skipped.

## 4. Two curves — the honest artifact

Run both policies over the same epochs and publish both.

| Curve | Policy | Meaning |
|---|---|---|
| **A — oracle** | existing `choose_sql` | Ceiling: what perfect use of retrieved rules would score |
| **B — agent** | Bedrock generation | What actually happens |

Keep A. It is not embarrassing once labelled correctly — it is the upper bound, and the
**A−B gap is a real finding**: it separates *did memory contain the rule* from *could the
model use it*. Nobody else in this field will publish that decomposition.

`educate.py` takes `--policy {oracle,agent,both}`, default `both`.

## 5. Artifacts (every run, no exceptions)

`eval/runs/<policy>_<epoch>_answers.json` — per item: `id`, `sql`, `used_rules`,
`retrieved_rule_ids`, `outcome`, plus any rejection reason.
`eval/runs/<policy>_manifest.json` — model id, embedder provider, region, `recall_k`,
temperature, UTC start/end, epoch HLCs, `git rev-parse HEAD`.

An unaudited number does not go in RESULTS.md.

## 6. RESULTS.md format

Replace the single table with: both curves per epoch (correct/50 + accuracy),
per-stratum accuracy for curve B at first and last epoch, the six bait items across
epochs for **both** curves, and a short "what the gap says" paragraph.

Add one line stating plainly that the 2026-08-11 44/50 run was the oracle policy, that it
is retained as the ceiling control, and that curve B is the measured agent. Do not delete
the old numbers.

## 7. The two results I most want to see

Both are publishable either way — that is the point of freezing first.

1. **Do the baits actually fire?** The oracle fires all six by construction. If the real
   model over-generalizes on only two, the honest headline is *"I predicted six
   regressions; the model took four of the baits it was offered and resisted two"* — a
   negative result on my own prediction, which is worth more than a clean curve.
2. **What does the agent score at `memory_zero`?** If it beats 12% cold, it guessed some
   house semantics unaided, and the real story is the delta memory adds on top of a
   competent model — a smaller, truer claim than 12→88.

## 8. Acceptance checklist

- [ ] `run_exam.py verify` still green; frozen files untouched (`git diff --stat` clean for `eval/questions.json`, `eval/labels.json`)
- [ ] Grep proves no `gold_sql`/`naive_sql`/`bait_sql`/`house_rules` reference in the agent path
- [ ] `memory_zero` retrieval returns **0** rules via AOST (not a Python filter)
- [ ] Manifest shows `provider: bedrock-titan` and a real model id — not `mock-hasher`
- [ ] Both curves present in `curve.json`; every generated SQL persisted
- [ ] Malformed/rejected generations graded wrong, counted, and reported
- [ ] No prompt, retrieval-k, or model change made *after* seeing a score

## 9. If Bedrock access is blocked

Do not stall. Ship generation on any reachable model behind the same `Generator`
interface, mark the manifest `provider: non-bedrock`, and take AWS eligibility from a
**Lambda-hosted demo URL plus S3-published exam and curve artifacts** ("any other AWS
service that powers your agent's environment"). Weaker on AWS depth, but a real agent
with thin AWS beats a fake agent with deep AWS on four of the five criteria.
