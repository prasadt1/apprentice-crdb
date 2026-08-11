# Apprentice

**memory that helps, then hurts**

Apprentice is an analyst agent that ships its own learning curve.

I am about to ask it for regional revenue. It will write competent SQL. It will also use the calendar year when I said “fiscal,” count a soft-deleted order, and attribute a region through the product instead of the customer. Tomorrow someone will correct it. The week after, the same mistake will come back, because nothing in the stack can show *what the agent knew when*.

Apprentice freezes a 50-question exam, teaches the house rules into CockroachDB, and replays the same exam against earlier brains via `AS OF SYSTEM TIME`. Storage worked. Recall worked. Utilization did not. Both Bedrock agents peak on partial memory and decline at full memory — while retrieval at that last epoch is **44/44**.

Built for the [CockroachDB × AWS Agentic Memory Hackathon](https://cockroachdb-ai.devpost.com/) (Apache-2.0).

Primary user: the analytics engineer whose house rules live in people’s heads. Secondary: the reviewer who has to trust the agent next week, and needs to see what it knew. Apprentice is a CLI + CockroachDB Cloud + Bedrock — not a BI fork. The warehouse is a local SQLite prop. CockroachDB holds the brain.

> ### For judges — fastest paths in
>
> | Path | Link | Time |
> | --- | --- | --- |
> | **Hosted page** | [prasadt1.github.io/apprentice-crdb](https://prasadt1.github.io/apprentice-crdb/) | 30 s |
> | **The finding** | [`eval/RESULTS.md`](eval/RESULTS.md) | 2 min |
> | **Three-curve chart** | [`docs/media/learning-curve.png`](docs/media/learning-curve.png) | 20 s |
> | **Try it locally (no cluster)** | [Quick start below](#try-it-locally-cli--no-cluster) | ~2 min |
> | **Reproduce the freeze** | `pytest -q` then `python eval/run_exam.py verify` | ~1 min |
> | **Every generated string** | [`eval/runs-nova-micro/`](eval/runs-nova-micro) · [`eval/runs-nova-lite/`](eval/runs-nova-lite) | — |
> | **Devpost paste draft** | [`docs/devpost-article-draft.md`](docs/devpost-article-draft.md) | skim |
>
> **TL;DR:** Freeze a 50-question exam → teach into CockroachDB → score each AOST epoch. Oracle rises to 88%. Two Bedrock agents peak before full memory and decline. Retrieval at that last epoch is **44/44**. Storage and recall look perfect. Utilization does not.

**Why it matters.** Most agent-memory demos are a chat that got longer, and a curve that only goes up. If memory cannot be replayed, it is not memory. It is a log. If it cannot get worse, you are not measuring it.

**What I built.** A frozen, execution-graded exam; sqlglot AST-diffs that write semantic rules into CockroachDB; Titan embeddings and `ORDER BY embedding <->` recall inside `BEGIN AS OF SYSTEM TIME`; two answering policies on the same HLCs — an oracle ceiling, and a Bedrock generator that never sees the labels.

**The differentiator.** I measure the third leg. Agent memory is usually scored on storage and retrieval. At full memory both of those are perfect, and accuracy is already falling. The 56-point gap (oracle 88%, best agent 32%) is utilization. It replicated on Nova Lite.

## Try it locally (CLI — no cluster)

Python **3.11+**. This is the same binder as the published freeze — no CockroachDB, no Bedrock:

```bash
git clone https://github.com/prasadt1/apprentice-crdb.git
cd apprentice-crdb
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 1) Naive vs house-correct result sets on the prop warehouse
apprentice warehouse-demo

# 2) sqlglot AST-diff of that pair → candidate house rules
apprentice distill

# 3) Frozen exam integrity — 18 tests, then VERIFY OK + matching sha256s
pytest -q
python eval/run_exam.py verify
python eval/run_exam.py questions   # agent-facing view: id + question only
```

If you see `apprentice: command not found`, the venv is not active.

### Measure the published curves

Not required to *try* the product — this is the receipt. Numbers and HLC timestamps live in [`eval/RESULTS.md`](eval/RESULTS.md). Every generated SQL string is on disk in [`eval/runs-nova-micro/`](eval/runs-nova-micro) and [`eval/runs-nova-lite/`](eval/runs-nova-lite). I do not ask you to re-pay Bedrock to believe the scores.

| Epoch | Live rules | Oracle (ceiling) | Nova Micro | Nova Lite |
|---|---|---:|---:|---:|
| `memory_zero` | 0 | 6/50 | 8/50 | 14/50 |
| `filters` | 2 | 7/50 | **21/50** | 19/50 |
| `revenue_and_fiscal` | 4 | 31/50 | 18/50 | **19/50** |
| `join_path` | 5 | **44/50** | 13/50 | 16/50 |

Bold = that column's peak. Both agents peak *before* full memory. Retrieval at `join_path` is **44/44**.

The oracle is a selector over frozen SQL, not an agent. I briefly published its 44/50 as the learning curve. That was wrong.

![Three curves: oracle rises to 44/50; both Nova agents peak early and decline](docs/media/learning-curve.png)

## Teach into CockroachDB (live memory)

The warehouse stays local SQLite. CockroachDB holds corrections, rules, embeddings. Replay is a timestamp clause, not a backup restore.

```bash
export APPRENTICE_CRDB_DSN='postgresql://USER:PASS@HOST:26257/defaultdb?sslmode=verify-full'
apprentice migrate --try-vector-index
apprentice gc-ttl                   # measured gc.ttlseconds = 4500
apprentice educate --policy oracle  # write rules, score the ceiling at each HLC
apprentice recall                   # live keys now
apprentice recall --as-of '<memory_zero HLC>'   # empty — none existed yet
```

`memory_zero` returns zero rules because none existed at that timestamp, not because Python filtered them.

### Agent arms (Amazon Bedrock, us-east-1)

```bash
export APPRENTICE_EMBEDDER=bedrock AWS_REGION=us-east-1 APPRENTICE_RECALL_K=5
export APPRENTICE_GEN_MODEL=amazon.nova-micro-v1:0   # or amazon.nova-lite-v1:0
pip install -e ".[aws]"
apprentice educate --policy both
```

Pre-registered model: Nova Micro. Nova Lite was added *after* seeing the Micro drop, as a disclosed extra arm, not a replacement. No prompt, `k`, or exam change after any score.

## What it does

One loop. Four compressed epochs (live GC TTL on Basic is **75 minutes**, so the clock is minutes, not months):

1. **Teach** — a wrong attempt and a correction go into `episodic_events`; sqlglot writes `semantic_rules` (soft-delete, cancelled orders, net revenue, fiscal calendar, region via the customer).
2. **Store** — CockroachDB Cloud. SERIALIZABLE upsert; one live rule per key; old row superseded, not deleted. Titan v2 embeddings, **1024-d**.
3. **Rewind** — `BEGIN AS OF SYSTEM TIME` on the cluster HLC.
4. **Answer** — oracle selects among frozen fixtures by live keys. Agent generates SQL via Bedrock Converse from `{id, question}` + retrieved rule statements + warehouse DDL only.
5. **Grade** — execution result signatures against labels frozen *before* any learning run ([`eval/FREEZE.md`](eval/FREEZE.md)).

![Who Apprentice is for, and what happens](docs/media/customer-journey.png)

![AOST replay: the same exam, the same cluster, an earlier brain](docs/media/aost-replay.png)

## Architecture

CockroachDB is the memory plane — rules, episodes, vectors, AOST. The warehouse is a prop. One teaching path; one answering path that cannot see the labels.

The cluster is CockroachDB Cloud on AWS (eu-central-1). That satisfies “deployed on AWS.” The AWS service I use is **Amazon Bedrock** — Titan embeddings on write and query, Converse for generation. I will not call the cluster an AWS service I built.

![Layered architecture: CLI and exam in, CockroachDB memory in the middle, Bedrock + SQLite on the edges](docs/media/architecture.png)

| CockroachDB tool | How it is used — not just that it is configured |
| --- | --- |
| **Distributed vector indexing** | `CREATE VECTOR INDEX semantic_embedding_idx` exists (`vector_l2_ops`). The answering path still runs `ORDER BY embedding <-> $1` inside `BEGIN AS OF SYSTEM TIME`. Live `EXPLAIN` is `semantic_rules@semantic_rules_pkey` / `FULL SCAN` — five live rows, planner will not pick the index. Receipt in [`eval/RESULTS.md`](eval/RESULTS.md) |
| **Cloud Managed MCP Server** | Cursor, read-only, to inspect the live schema and row counts while I built. The agent does **not** call MCP at answer time. Writes stay on the CLI |
| **ccloud CLI** | Same control plane as `ccloud cluster list`. Live listing: [`docs/proof/ccloud.txt`](docs/proof/ccloud.txt) (Cloud API, AWS / Basic / eu-central-1). Stamp the official CLI after `ccloud auth login` if a judge wants the binary’s own JSON |

| AWS service | How |
| --- | --- |
| **Amazon Bedrock** | Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`, 1024-d) on write and query. Converse API for generation. Pre-registered: `amazon.nova-micro-v1:0`. Replication arm, added after seeing the Micro drop and disclosed: `amazon.nova-lite-v1:0` |

### What happens when things go wrong

- **Concurrent teachers** — rule upserts are `SERIALIZABLE`; one live row per key; the old row is superseded, not deleted.
- **Time-travel races** — I do not `BEGIN` at now and then `AS OF`. I wait for the closed timestamp and `BEGIN AS OF SYSTEM TIME <hlc>`.
- **Bad SQL** — `sql_guard` rejects anything that is not a single `SELECT` / `WITH`. A reject grades **wrong**, not skipped.
- **Label leakage** — the generator never reads `gold_sql`, `naive_sql`, `bait_sql`, `house_rules.py`, or `seed.sql`.
- **MCP** — editor is read-only. A mistaken write grant is not the product path.
- **Self-report** — `-- used_rules:` citations are not evidence. At `memory_zero`, Nova Micro still cited memory on 34/50 items.

## Limits (honest)

- Not a warehouse copilot, and not a dbt or Looker replacement. CockroachDB is not required to generate SQL. It is required to store and **replay** the education.
- Prop warehouse: 6 orders. Item difficulty is semantic, not volume.
- Single run per model at `temperature=0`. Two Nova-family models only.
- `k=5` was fixed before the run. With five live rules, retrieval returns the whole corpus and ranks nothing.
- Over-application is real and replicated, not monotonic with rule count. Both models end below their own `unaffected` peak (Micro 5/6 → 3/6, Lite 6/6 → 4/6). Lite's worst cell (3/6) is at `filters` (two rules). Micro bottoms at 2/6 mid-curriculum.
- The `unaffected` stratum is n=6. Per-stratum movements are directional.
- I froze six regression baits and predicted all six would fire. Nova Lite resisted four of six. **q50** is wrong in every cell, including before its rule existed — a model prior. **q31** flips the other way: memory *corrected* a bias I had predicted it would cause. The failed prediction is in [`eval/RESULTS.md`](eval/RESULTS.md), not quietly removed.
- Self-reported `-- used_rules:` citations are not evidence: at `memory_zero`, with zero rules retrieved, Nova Micro still cited memory on 34/50 items.
- I will not invent vector-index or GC facts. Those are measured on the live cluster.
- I will not call a rising oracle line the product. The product is the gap.

## Documentation

| Doc | What |
| --- | --- |
| [`eval/RESULTS.md`](eval/RESULTS.md) | Published curves, retrieval, baits, limitations |
| [`eval/FREEZE.md`](eval/FREEZE.md) | Freeze commit, sha256s, what must not change |
| [`eval/PROTOCOL.md`](eval/PROTOCOL.md) | Strata, invariants, how grading works |
| [`eval/README.md`](eval/README.md) | Exam file map |
| [`docs/devpost-article-draft.md`](docs/devpost-article-draft.md) | Devpost form map |
| [`docs/CURSOR-AGENT-SEAM-SPEC.md`](docs/CURSOR-AGENT-SEAM-SPEC.md) | Bedrock answering-path spec |

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
