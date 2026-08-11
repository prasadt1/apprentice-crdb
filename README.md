# Apprentice

**an analyst agent that ships its own learning curve**

Measured proof that agent memory works — frozen exam, `AS OF SYSTEM TIME` epoch replay, regressions included. Chat Q&A is the demo vehicle; the product is the memory.

Built for the [CockroachDB × AWS Agentic Memory Hackathon](https://cockroachdb-ai.devpost.com/).

> I built an analyst agent that ships its own learning curve — measured proof its memory works, regressions included.

## Status

- **LOCKED** contest entry (not a startup seed). Deadline **18 Aug 2026**.
- Design: [`docs/superpowers/specs/2026-08-09-apprentice-design.md`](docs/superpowers/specs/2026-08-09-apprentice-design.md)
- Local + GitHub: this repo (`apprentice-crdb`). Expunction (`expunction-crdb`) is a dropped idea — leave it alone.
- Frozen 50-question exam: **not yet committed.** Claude brief: [`docs/CLAUDE-EXAM-BRIEF.md`](docs/CLAUDE-EXAM-BRIEF.md)

## Quick start (no cluster)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
apprentice warehouse-demo    # naive vs gold result sets
apprentice distill           # sqlglot AST-diff of that pair
```

## CockroachDB memory (brain, not the warehouse)

```bash
export APPRENTICE_CRDB_DSN='postgresql://...'
apprentice migrate --try-vector-index
apprentice gc-ttl
apprentice recall            # live rules
apprentice recall --as-of '2026-08-12 12:00:00'
```

The warehouse is a SQLite prop. CockroachDB stores episodic corrections + semantic rules + embeddings. Replay is a timestamp clause.

## Do not claim

- Not “another SQL copilot” (framing kill if assets lead that way)
- Not a dbt/Looker semantic-layer replacement
- Not that CockroachDB is required to *generate* SQL — it is required to **replay and prove** memory education
- No fake curves — publish flat or regressing results if that’s what you get
- No unverified vector-index / GC facts — measure via `VERIFY.md`

## License

[Apache-2.0](LICENSE)
