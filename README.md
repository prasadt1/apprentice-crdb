# Apprentice

**an analyst agent that ships its own learning curve**

Measured proof that agent memory works — a frozen exam, replayed against the agent's own memory as of earlier moments via CockroachDB `AS OF SYSTEM TIME`, regressions included. The chat box is how you watch it learn. The product is the memory.

Built for the [CockroachDB × AWS Agentic Memory Hackathon](https://cockroachdb-ai.devpost.com/).

> I built an analyst agent that ships its own learning curve — measured proof its memory works, regressions included.

## Quick start

Python 3.11+. Every new terminal needs the venv activated — that is what puts the `apprentice` command on your `PATH`.

```bash
cd /Users/prasadt1/Apprentice
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
apprentice warehouse-demo          # naive vs house-correct result sets
apprentice distill                 # sqlglot AST-diff of that pair
```

If you see `apprentice: command not found`, the venv is not active. Either `source .venv/bin/activate` or run:

```bash
.venv/bin/apprentice warehouse-demo
```

## CockroachDB memory

The warehouse in the demo is a local SQLite prop. CockroachDB holds the agent's brain: corrections, rules, embeddings. Replay is a timestamp clause, not a backup restore.

```bash
export APPRENTICE_CRDB_DSN='postgresql://USER:PASS@HOST:26257/defaultdb?sslmode=verify-full'
apprentice migrate --try-vector-index
apprentice gc-ttl
apprentice recall
apprentice recall --as-of '2026-08-12 12:00:00'
```

## What this is not

- Not a warehouse copilot product, and not a replacement for a dbt or Looker semantic layer.
- CockroachDB is not required to generate SQL. It is required to store and **replay** the agent's education.
- I will not invent vector-index or GC facts. Those are measured on the live cluster.

## License

[Apache-2.0](LICENSE)
