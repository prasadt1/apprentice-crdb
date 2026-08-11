# Apprentice — Design

**Date:** 2026-08-09  
**Hackathon:** CockroachDB × AWS — Build with Agentic Memory (due Aug 18, 2026)  
**Status:** **LOCKED** — contest entry (not a startup seed)  
**Product:** Apprentice — an analyst agent that **ships its own learning curve**

---

## 0. What this is (and is not)

**Is:** A competition entry whose product is **agent memory as a first-class, replayable database artifact**, demonstrated through a warehouse analyst that learns house SQL semantics from corrections.

**Is not:** A Snowflake/Databricks-style copilot product, a PMF claim, or “text-to-SQL as the innovation.” Chat Q&A is the **demo vehicle**. The **product** is the measured education of memory.

**Signature sentence (use everywhere):**

> I built an analyst agent that ships its own learning curve — measured proof its memory works, regressions included.

Same shape as Premortem (“how it breaks, before you merge”) and Privilege (“proof the masking holds”).

---

## 1. One-liner

A warehouse analyst agent learns organization-specific SQL semantics from human corrections (sqlglot AST-diff → durable rules in CockroachDB). It **proves** memory works by replaying a frozen, execution-graded benchmark against its own memory **as of day 1 / 3 / 5** via `AS OF SYSTEM TIME`, and publishes the honest learning curve — **including regressions**.

## 2. Protagonist and stakes

**Protagonist:** analytics engineer / warehouse analyst whose org has house semantics (revenue excludes refunds, soft-delete filters, fiscal calendar) that live in people’s heads.

**Stakes:** Generic copilots re-fail the same rules; silent wrong-but-runnable SQL misleads decisions. Corrections today are a recurring cost; here each correction becomes a compounding memory asset with provenance.

**Impact framing (honest):** meaningful workflow / trust / productivity — not social good, not a claimed ARR line. Market already invests in static semantic layers (dbt, Looker); this is the **dynamic, agent-memory** version with receipts.

## 3. Why CockroachDB is load-bearing (swap test)

The **warehouse being queried is a demo prop** (can be local Postgres/SQLite). What lives in CockroachDB is the **agent’s brain**.

| Without CRDB | This build |
|--------------|------------|
| “Show the day-3 agent” = snapshot/restore pipeline | `AS OF SYSTEM TIME` on memory retrieval — ablation in a clause |
| Rules + embeddings in split stores | One DB: episodic corrections, semantic rules, vectors, supersession |
| Concurrent corrections can accept contradictory live rules under weak isolation | Serializable upsert + supersession lineage (supporting beat, not the center) |
| Consolidation/expiry as cron app logic | Row-level TTL + CDC-driven distill (supporting) |

**Centerpiece:** AOST learning-curve replay. If you delete AOST and the demo still looks the same, the entry fails the swap test.

**Concession (README, own voice):** a single demo agent does not need distributed SQL for *scale*. The claim is memory *semantics* — replayable, contradiction-checked, lifecycle-managed — are native here and hand-built elsewhere.

## 4. Framing kill criteria

- README H1, repo description, and video **first line** = learning curve / proof. **Never** lead with “SQL copilot,” “chat with your warehouse,” or “text-to-SQL agent.”
- If a skimming judge can describe the entry as “another BI copilot” after 20 seconds, framing failed.
- Do not claim product-market fit or “no vendor has a brain.” Claim: **auditable, replayable agent memory — here’s what that looks like.**

## 5. Do not claim

- Not a replacement for dbt semantic layer / Looker
- Not “solved text-to-SQL”
- Not that CockroachDB is required to *generate* SQL
- No unverified C-SPANN / tier facts — confirm `CREATE VECTOR INDEX` on *your* cluster
- No fake learning: if the curve is flat or regressions dominate, **publish that**

## 6. Product behavior

### 6.1 Demo warehouse (prop)

Synthetic retail schema with deliberate house semantics, authored with Premortem-grade instinct:

| House rule | Wrong agent behavior | Correct behavior |
|------------|----------------------|------------------|
| `revenue` = net of refunds | `SUM(amount)` | Exclude refunds / use net column |
| Soft deletes | Ignore `deleted_at` | `deleted_at IS NULL` on orders |
| Fiscal calendar | Calendar quarters | Org fiscal start (e.g. Feb) |
| Join path | Wrong fact table | Canonical join documented in memory |

### 6.2 Memory model (the product)

Three stores in CockroachDB:

1. **Episodic** — question, generated SQL, execution result, human correction (raw).
2. **Semantic** — distilled rules/facts with provenance, embedding, supersession lineage (`superseded_by`).
3. **Procedural** — generalizable SQL idioms from sqlglot AST-diff (e.g. “always filter soft-deletes on orders”).

**Write path:** correction → AST-diff (sqlglot) → rule extraction → **serializable** upsert with contradiction check (exact key + vector-nearest); supersede or flag, never two live defs of the same metric.

**Read path:** one SQL query joining vector similarity with structured predicates (table relevance, recency, **not superseded**).

**Lifecycle (supporting):** CDC-driven consolidator folds episodic → semantic; row-level TTL expires distilled episodic rows after promotion.

### 6.3 Learning curve (must ship)

1. **Freeze** a 50-question benchmark + gold SQL / result signatures **before** any learning run. Commit hash publicly. (Claude owns protocol; Cursor does not implement the agent until the freeze exists.)
2. Grade by **execution result accuracy** (result-set signature), not LLM-as-judge.
3. Run education: scripted correction sessions across simulated days.
4. Re-score the **same** frozen exam with memory read `AS OF` epoch timestamps (day 0 / mid / end).
5. Publish curve + **regressions** (rules that made some questions worse).

### 6.4 Agent loop (vehicle)

Bedrock (or documented fallback) generates SQL; executes against demo warehouse; on failure or human correction, memory write path runs. Answers **cite memory IDs** used.

## 7. Architecture

```text
Analyst (UI / CLI)
    │ NL question
    ▼
Agent loop (Bedrock) ── SQL ──► Demo warehouse (prop)
    │
    │ corrections + citations
    ▼
Memory service (accumulate / distill / recall / AOST replay)
    │ SQL + VECTOR
    ▼
CockroachDB Cloud (serializable memory + optional C-SPANN)
    │
    ├── Managed MCP (inspect / agent DB path; R/O default)
    ├── ccloud CLI (provision + gc.ttlseconds scripts)
    ├── CDC → consolidator (optional Lambda)
    └── S3 (frozen exam, curve artifacts, receipts)
```

**Schema notes (day one):**

- `USING HASH` on hot time-ordered episodic keys — avoid sequential hotspots.
- Explicit history/supersession — do not rely on GC for audit lookback.
- Raise / verify `gc.ttlseconds` so multi-epoch AOST fits the education window (or compress timeline and disclose).

## 8. Hackathon tool checklist

Must use ≥2 CockroachDB tools — target **3** for Stage One screener safety:

| Tool | How |
|------|-----|
| Distributed Vector Indexing | Semantic rule/question recall |
| Managed MCP Server | Dev-side +/or agent memory path (FAQ: dev-only counts) |
| ccloud CLI | Provision, zone/GC config scripts |
| Agent Skills | Optional stretch |

AWS (≥1): **Bedrock** (SQL + embeddings) + **S3** (exam + curve). Lambda optional for consolidator / demo URL.

## 9. Verification gates (day 1 — measure, don’t assume)

| # | Gate | Pass |
|---|------|------|
| 1 | Cluster up via ccloud; MCP connected | |
| 2 | Live `gc.ttlseconds` — AOST window fits planned epochs **or** compressed-clock plan written | |
| 3 | `CREATE VECTOR INDEX` (or honest fallback + still ≥2 tools) | |
| 4 | Bedrock model access **or** S3-only AWS path + non-Bedrock model disclosed | |
| 5 | sqlglot AST-diff spike: one known correction → rule shape | |

## 10. Demo script (~3 min)

1. **0:00–0:20** Hook: “Every agent on this Devpost claims memory makes it better. Almost none show the curve.” Show frozen-exam commit hash.
2. **0:20–0:50** Day-0 failure: “Q3 revenue by region” — wrong column / missed soft-delete. Human corrects. Watch AST-diff → rule land in memory (UI/MCP).
3. **0:50–1:20** Later session: same question correct with cited memories; harder unseen question composing multiple rules.
4. **1:20–2:00** Trick shot: identical question with memory `AS OF` earlier epoch — visibly dumber. Timeline slider / epoch labels.
5. **2:00–2:40** The chart: 50Q execution-graded curve; call out N regressions. Architecture slate: AOST, vector+SQL, MCP, ccloud, Bedrock/S3.
6. **2:40–3:00** Limits: prop warehouse; not a semantic-layer replacement; GC window disclosure.

## 11. Sequencing (8 days)

| Day | Focus |
|-----|--------|
| 0 (lock) | This spec; Claude freezes 50Q protocol **before** agent answers |
| 1 | Cluster, VERIFY gates, schema, demo warehouse seed |
| 2 | Commit frozen exam hash; memory-zero baseline run |
| 3 | Agent loop + MCP; citation-required answers |
| 4 | Correction → sqlglot → serializable semantic upsert |
| 5 | Education run; AOST replay harness |
| 6 | Curve report + UI; consolidator/TTL if time |
| 7 | Harden, README, video draft |
| 8 | Buffer, submit (Aug 18) |

**Hard rule:** no graded learning run until the exam is frozen and hash-committed.

## 12. Kill / demote

- Cannot show AOST epoch replay → thesis collapses to copilot → fail.
- Cannot show agent accumulate+recall of rules → fail Agentic Memory Design.
- Vector index unavailable → document fallback; keep ≥2 other CRDB tools.
- Builder frames as copilot in assets → framing kill (fix before ship).

## 13. Division of labor

| Role | Owner |
|------|--------|
| Frozen 50-question exam protocol + labels before results | **Claude** |
| Design (this doc), scaffold, implementation | **Cursor** |
| Cluster, ccloud, MCP, Bedrock/S3 access, own-voice README/video | **Prasad** |

---

## Appendix — Repo

- Local: `/Users/prasadt1/Apprentice`
- Suggested GitHub slug: `apprentice-crdb` (verify `apprentice` / `apprentice-crdb` — both free as of lock)
- Do **not** reuse `expunction-crdb` contents as the product surface
