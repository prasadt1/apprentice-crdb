# Results

Frozen exam: `eval/FREEZE.md` (2026-08-11), committed at `b043aea` **before** any agent
existed. Labels were never edited. Everything below was graded by executing SQL against
the seeded warehouse and comparing result signatures — no LLM judge anywhere.

**Headline: memory made the agent better, then worse.** Both models peak with partial
memory and decline at full memory, while the oracle ceiling rises monotonically to 88%.
Retrieval was not the bottleneck — at full memory every rule an item needed was in the
model's context on 44 of 44 rule-bearing items. The rules were present, sufficient, and
unusable.

---

## The three curves

| Epoch | Live rules | Oracle (ceiling) | Nova Micro | Nova Lite |
|---|---|---:|---:|---:|
| `memory_zero` | none | 6/50 · 12% | 8/50 · 16% | 14/50 · 28% |
| `filters` | 2 | 7/50 · 14% | **21/50 · 42%** | 19/50 · 38% |
| `revenue_and_fiscal` | 4 | 31/50 · 62% | 18/50 · 36% | **19/50 · 38%** |
| `join_path` | 5 | **44/50 · 88%** | 13/50 · 26% | 16/50 · 32% |

Bold = that column's peak. Both agents peak *before* full memory. The decline replicates
across two model tiers, so it is not an artifact of one weak model.

**The oracle is not an agent.** It is `student.choose_sql()`, a selector that picks among
SQL bodies authored inside the frozen exam, gated on that exam's own `house_rules`
metadata. Its 44/50 is a deterministic function of static data — it cannot fail, and it
never wrote a line of SQL. It is retained *only* as the ceiling: what a perfect consumer
of the retrieved rules would score. An earlier version of this file reported that 44/50
as the project's learning curve. That was wrong, and the correction is why the agent
curves above exist.

Epochs are AOST ticks minutes apart on a live CockroachDB cluster with a measured
`gc.ttlseconds = 4500` (75 min), replayed with `BEGIN AS OF SYSTEM TIME <hlc>`.

## Where the decline comes from

Two mechanisms, both visible in strata the exam was designed to separate.

**1. Over-application.** The `unaffected` stratum (6 items where house rules do *not*
apply and the naive answer is correct) exists to catch memory being used where it should
not be.

| Epoch | Rules | Nova Micro | Nova Lite |
|---|---|---:|---:|
| `memory_zero` | 0 | 4/6 | **6/6** |
| `filters` | 2 | **5/6** | **3/6** |
| `revenue_and_fiscal` | 4 | **2/6** | 4/6 |
| `join_path` | 5 | 3/6 | 4/6 |

Both models end below their own `unaffected` peak (Micro 5/6 → 3/6, Lite 6/6 → 4/6).
Lite's worst cell is 3/6 at `filters` — two rules, not five. Micro bottoms at 2/6
mid-curriculum. Over-application is real and replicated; it is not monotonic with rule
count. Teaching the join rule also drove Nova Micro's `join_path` stratum from 2/6 to
**0/6** — the rule meant to fix those questions broke them.

**2. Harder SQL, attempted and botched.** Invalid-SQL counts per epoch:

| Epoch | Nova Micro | Nova Lite |
|---|---:|---:|
| `memory_zero` | 12 | 9 |
| `filters` | 8 | 4 |
| `revenue_and_fiscal` | 11 | 7 |
| `join_path` | 13 | 11 |

Dominant error: `misuse of aggregate function SUM()` — both models write
`SUM(amount - SUM(refund))`, a nested aggregate, while chasing the refund-netting rule.
The rule is correct; the model cannot express it. Invalid SQL is roughly flat across
epochs, so it does not explain the decline on its own — it compounds it.

## Retrieval was not the problem

| Epoch | All needed rules retrieved (k=5) | Would-be at k=3 |
|---|---:|---:|
| `filters` | 5/44 | 5/44 |
| `revenue_and_fiscal` | 31/44 | 11/44 |
| `join_path` | **44/44** | 13/44 |

At full memory, retrieval was perfect. `k=5` was fixed before the run and never adjusted;
the k=3 column is computed post-hoc from recorded rank order, not from a second run.

This exposes a design limit worth stating plainly: **with five rules total and k=5,
retrieval returns the entire corpus and ranks nothing.** Every prompt at full memory
carried all five rules, including on `unaffected` items where none applied. So this run
measures *undifferentiated memory injection*, not relevance-gated recall. That is the
right description of the prompt. It is not a complete explanation of the `unaffected`
column — Lite's worst cell is at two rules, not five.

## Regression baits — my prediction was wrong

I froze six items where a plausibly over-generalized rule produces a worse answer, and
predicted all six would fire. Correct answers on those six:

| Epoch | Oracle | Nova Micro | Nova Lite |
|---|---:|---:|---:|
| `memory_zero` | 3/6 | 1/6 | 3/6 |
| `filters` | 0/6 | 4/6 | 3/6 |
| `revenue_and_fiscal` | 0/6 | 2/6 | 3/6 |
| `join_path` | 0/6 | 2/6 | **4/6** |

The oracle fires all six by construction. The real models did not. Nova Lite resisted
four of six at full memory. **The prediction this exam was built to test came out wrong,
and the exam says so.**

Two specific findings against my own bait design:

- **q50 is wrong in every cell, for both models, at every epoch — including before the
  rule existed.** Both models already net refunds when asked for gross billings. That is
  a model prior, not a memory-induced regression, so q50 does not measure what I built it
  to measure.
- **q31 flips the other way.** Both models get it wrong cold and right after
  `metric:revenue` lands. Memory *corrected* a bias I had predicted memory would cause.

Baits assume the taught rule is the source of over-generalization. Where the model
already holds the bias, the bait measures the prior instead. Stated, not fixed — the
labels are frozen.

## What the gap says

At full memory the oracle scores 88% and the best agent scores 32%. The same rule set,
verifiably in context on every item, supports both numbers. The 56-point gap is entirely
*could the consumer use what it retrieved*.

Agent-memory systems are usually evaluated on two legs — did we store it, did we recall
it. This measures the third: **utilization**. On that leg, more memory made both models
worse, and the effect is invisible to storage and retrieval metrics, which both look
perfect at the exact epoch where accuracy is falling.

The honest read is that undifferentiated injection is a real property of this setup, not
that every `unaffected` miss is caused by the fifth rule. Relevance gating — retrieving
*fewer* rules, ranked by whether they bear on the question — is the obvious next
experiment, and this exam is the instrument for running it.

## Self-reported citations are not evidence

At `memory_zero`, with zero rules retrieved, Nova Micro still emitted `-- used_rules:`
citations on 34/50 items. The agent's own account of which memories it used cannot be
taken at face value; only the retrieval log and the graded result can.

## Superseded runs

- An early cluster run plateaued at 15/50 because the AST-diff wrote `filter:generic` /
  `join:customers` instead of the canonical rule keys. Superseded; labels were not edited
  to chase the score.
- The oracle 44/50 was briefly published as the learning curve. Corrected above.

## Vector index — real, unused at this scale

`CREATE VECTOR INDEX semantic_embedding_idx ON semantic_rules (embedding)` succeeded
(`vector_l2_ops` in `SHOW CREATE`). Live row count at the probe: **5** embedded live
rules, 15 rows including superseded. `EXPLAIN` of the answering-path recall
(`ORDER BY embedding <-> $1 LIMIT 5`, `superseded_by IS NULL`) on 2026-08-11:

```
• top-k
│ estimated row count: 5
│ k: 5
│
└── • filter
    │ filter: (superseded_by IS NULL) AND (embedding IS NOT NULL)
    │
    └── • scan
          estimated row count: 15 (100% of the table)
          table: semantic_rules@semantic_rules_pkey
          spans: FULL SCAN
```

The index is in the catalog. The planner full-scans the primary key. Five rows is too
small for a vector index to win. I say so rather than claim scale I do not have.

## Limitations

- Prop warehouse: 6 orders, 3 customers, 3 products. Item difficulty comes from
  semantics, not data volume.
- Single run per model at `temperature=0`. No repeated-sampling variance estimate.
- Two Bedrock models from one family (Nova Micro, Nova Lite). Claude on Bedrock required
  an inference profile that was not available; the finding is not established beyond
  this family.
- Nova Micro was the pre-registered model. **Nova Lite was added after observing the
  non-monotonic Micro curve** — as an additional arm, not a replacement. Both are
  published in full. No prompt, `k`, or exam change was made after seeing any score.
- The `unaffected` stratum is 6 items; per-stratum movements are small-n and directional.

## Reproduce

```bash
export APPRENTICE_EMBEDDER=bedrock AWS_REGION=us-east-1 APPRENTICE_RECALL_K=5
export APPRENTICE_GEN_MODEL=amazon.nova-micro-v1:0   # or amazon.nova-lite-v1:0
apprentice migrate --try-vector-index
apprentice educate --policy both                     # oracle + agent
python eval/run_exam.py verify                       # exam integrity
```

Artifacts: `eval/runs-nova-micro/` and `eval/runs-nova-lite/` — every generated SQL
string, retrieved rule ids in rank order, per-item outcome, and a manifest recording
model id, embedder provider, region, `k`, temperature, epoch HLCs, and git HEAD.
Filenames in `eval/runs/` do not carry the model id, so each arm is archived separately.
