# Apprentice

**an analyst agent that ships its own learning curve**

Memory helped, then hurt — and it replicated. Frozen 50-question exam, replayed on CockroachDB `AS OF SYSTEM TIME`. At full memory, retrieval is **44/44** and both Bedrock agents are already past their peak.

Built for the [CockroachDB × AWS Agentic Memory Hackathon](https://cockroachdb-ai.devpost.com/).

> Storage worked. Recall worked. Utilization did not.

## For judges

| Path | Time |
|---|---|
| The finding — [`eval/RESULTS.md`](eval/RESULTS.md) | 2 min |
| Three-curve chart — [`docs/media/learning-curve.png`](docs/media/learning-curve.png) | 20 s |
| Every generated string — [`eval/runs-nova-micro/`](eval/runs-nova-micro) · [`eval/runs-nova-lite/`](eval/runs-nova-lite) | — |
| Freeze + verify — `pytest -q` then `python eval/run_exam.py verify` | ~1 min |
| Devpost paste draft — [`docs/devpost-article-draft.md`](docs/devpost-article-draft.md) | — |

| Epoch | Live rules | Oracle | Nova Micro | Nova Lite |
|---|---|---:|---:|---:|
| `memory_zero` | 0 | 6/50 | 8/50 | 14/50 |
| `filters` | 2 | 7/50 | **21/50** | 19/50 |
| `revenue_and_fiscal` | 4 | 31/50 | 18/50 | **19/50** |
| `join_path` | 5 | **44/50** | 13/50 | 16/50 |

Bold = that column's peak. The oracle is a selector over frozen SQL, not an agent. I briefly published its 44/50 as the learning curve. That was wrong.

## Quick start

Python 3.11+. Every new terminal needs the venv activated — that is what puts the `apprentice` command on your `PATH`.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python eval/run_exam.py verify
```

If you see `apprentice: command not found`, the venv is not active.

## CockroachDB memory

The warehouse is a local SQLite prop. CockroachDB holds the brain: corrections, rules, embeddings. Replay is a timestamp clause, not a backup restore.

```bash
export APPRENTICE_CRDB_DSN='postgresql://USER:PASS@HOST:26257/defaultdb?sslmode=verify-full'
apprentice migrate --try-vector-index
apprentice gc-ttl                   # measured gc.ttlseconds = 4500
apprentice educate --policy oracle
```

Agent arms (Amazon Bedrock, us-east-1):

```bash
export APPRENTICE_EMBEDDER=bedrock AWS_REGION=us-east-1 APPRENTICE_RECALL_K=5
export APPRENTICE_GEN_MODEL=amazon.nova-micro-v1:0   # or amazon.nova-lite-v1:0
pip install -e ".[aws]"
apprentice educate --policy both
```

## What this is not

- Not a warehouse copilot, and not a dbt or Looker replacement.
- CockroachDB is not required to generate SQL. It is required to store and **replay** the education.
- I will not invent vector-index or GC facts. Those are measured on the live cluster.
- I will not call a rising oracle line the product. The product is the gap.

## License

[Apache-2.0](LICENSE)
