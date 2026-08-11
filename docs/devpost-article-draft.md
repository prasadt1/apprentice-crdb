# Devpost submission draft — living document

> Working draft mapped 1:1 to the Devpost form. Legend: ✅ ready · 🔄 living · ⬜ blocked.
> Last updated: 2026-08-11 — Curve B in (`4df72a5`). Voice: first-person singular, plain.
> Numbers verified against `eval/RESULTS.md`. Headline: **memory helped, then hurt — twice.**
> Oracle 6→7→31→44. Nova Micro 8→21→18→13. Nova Lite 14→19→19→16. Retrieval at full memory **44/44**.
> **Still open:** video URL · hosted demo URL · ccloud proof screenshot · country.
> Structure follows Premortem + Engram: who + problem → product → numbers → reproduce → how/challenges → next → evidence.
> Inline story images: unframed `docs/media/*.png`. Framed copies (if any) go in the carousel only.

Hackathon: [CockroachDB × AWS Agentic Memory](https://cockroachdb-ai.devpost.com/) · due **Tue 18 Aug 2026, 5:00pm EDT**.

Repo: https://github.com/prasadt1/apprentice-crdb

---

## Page 1–2 · Project name + elevator pitch

**Project name (≤60 chars)** ✅:
> `Apprentice — memory that helps, then hurts` *(42)*

Keep-old alternate: `Apprentice — ships its own learning curve` *(41)*

**Elevator pitch (≤200 chars)** ✅ — **PASTE THIS ONE**:
> A frozen exam on CockroachDB time-travel. Two models peak before full memory and decline. Retrieval is 44/44 at the epoch accuracy falls. The product is the gap. *(166)*

Do **not** paste a rising-line pitch. The measured result is non-monotonic.

---

## Page 3 · Project story (paste between markers)

> Skimmable for judges. Order: who + problem → product → numbers → reproduce → how/challenges → next → evidence.
> **Inline images (unframed originals only):** journey + curve + AOST + architecture.
> Do **not** point story markdown at a `gallery/` folder — frames shrink the diagram.
> Video URL is 🔄 — leave the watch row as “coming” until YouTube is public, then paste the block as-is.

<!-- ════════════ COPY FROM HERE (Page 3 · Project story) ════════════ -->

## Inspiration

I am about to ask an analyst agent for regional revenue. It will write competent SQL. It will also use the calendar year when I said “fiscal,” count a soft-deleted order, and attribute a region through the product instead of the customer. Tomorrow someone will correct it. The week after, the same mistake will come back, because nothing in the stack can show *what the agent knew when*.

Most “agent memory” demos are a chat that got longer, and a curve that only goes up. I wanted a frozen exam, a brain I can rewind, and permission for the curve to fall. If memory cannot be replayed, it is not memory. It is a log. If it cannot get worse, you are not measuring it.

CockroachDB’s `AS OF SYSTEM TIME` is that rewind. Not a backup restore. A timestamp.

### For judges — fastest paths in

| Path | Link | Time |
| --- | --- | --- |
| **Watch the demo** | 🔄 video URL | ~3 min |
| **Source** | [github.com/prasadt1/apprentice-crdb](https://github.com/prasadt1/apprentice-crdb) | 30 s |
| **Published curve** | [`eval/RESULTS.md`](https://github.com/prasadt1/apprentice-crdb/blob/main/eval/RESULTS.md) | 60 s |
| **Reproduce the freeze** | `pytest -q` then `python eval/run_exam.py verify` | ~1 min |
| **Run the oracle educate** | `apprentice educate --policy oracle` (needs `APPRENTICE_CRDB_DSN`) | ~2 min |
| **Archived agent runs** | [`eval/runs-nova-micro/`](https://github.com/prasadt1/apprentice-crdb/tree/main/eval/runs-nova-micro) · [`eval/runs-nova-lite/`](https://github.com/prasadt1/apprentice-crdb/tree/main/eval/runs-nova-lite) | 60 s |

**TL;DR:** Freeze a 50-question exam → teach into CockroachDB → score each AOST epoch. Oracle rises to 88%. Two Bedrock agents peak on partial memory and decline. At full memory, retrieval is **44/44** and accuracy is falling. **Storage and recall look perfect. Utilization does not.**

### Why it matters

Without Apprentice I have a fluent SQL generator and a story that memory helped. With it I get a receipt I cannot edit: what the agent scored cold, what it scored after each lesson, and the epoch where more memory made it *worse*. The ugly epoch is the product. Filters lift Nova Micro to 21/50; five rules later it is at 13/50 with every needed rule in context. That is not a bug I hid. That is the third leg of agent memory — utilization — and almost nobody measures it.

I am not shipping a warehouse copilot. CockroachDB is not required to generate SQL. It is required to **store and replay** the education.

![Who Apprentice is for: an analyst whose house rules live in people’s heads, not in the warehouse](https://raw.githubusercontent.com/prasadt1/apprentice-crdb/main/docs/media/customer-journey.png)

*Primary user: the analytics engineer who owns the house definitions. Secondary: the reviewer who needs to see what the agent knew last Tuesday. Integration model: CLI + CockroachDB Cloud + Bedrock — not a BI fork.*

## What it does

Apprentice takes a frozen 50-question execution-graded exam about a tiny sales warehouse and teaches the house rules into CockroachDB. Each correction is an AST-diff (sqlglot) that writes a semantic rule — soft-delete, cancelled orders, net revenue, fiscal calendar, region via the customer. Rules carry Titan embeddings. Recall at answer time is vector similarity inside `BEGIN AS OF SYSTEM TIME <hlc>`.

Four compressed epochs (live GC TTL on Basic is **75 minutes**, so the clock is minutes, not months):

1. **memory_zero** — empty brain.
2. **filters** — `deleted_at IS NULL`, `status <> cancelled`.
3. **revenue_and_fiscal** — net of refunds, FY starts 1 February.
4. **join_path** — region through customers, not `product_id`.

Six items are published **regression baits**. I predicted all six would fire. Nova Lite resisted four of six at full memory. q50 is wrong in every cell, including before its rule existed — a model prior, not a memory regression. q31 flips the other way: memory *corrected* a bias I had predicted memory would cause. The exam says so. I did not remove the prediction.

![Three curves: oracle rises to 44/50; both Nova agents peak early and decline](https://raw.githubusercontent.com/prasadt1/apprentice-crdb/main/docs/media/learning-curve.png)

*Oracle 6-7-31-44. Nova Micro 8-21-18-13. Nova Lite 14-19-19-16. Bold peaks are not at full memory. Retrieval at join_path is 44/44.*

### Teach → store → rewind → answer

1. **Teach** — a wrong attempt and a correction go into `episodic_events`; sqlglot writes `semantic_rules`.
2. **Store** — CockroachDB Cloud (Basic, AWS eu-central-1). SERIALIZABLE upsert; one live rule per key; old row superseded, not deleted.
3. **Rewind** — `BEGIN AS OF SYSTEM TIME` on the cluster HLC. Replaying `memory_zero` returns **zero** rules because none existed at that timestamp — not because Python filtered them.
4. **Answer** — Curve A (oracle) selects among frozen fixtures by live rule keys. Curve B (agent) generates SQL via Bedrock Converse from `{id, question}` + retrieved rule statements + warehouse DDL only.
5. **Grade** — execution result signatures against labels frozen *before* any learning run (`eval/FREEZE.md`).

![AOST replay: the same exam, the same cluster, an earlier brain](https://raw.githubusercontent.com/prasadt1/apprentice-crdb/main/docs/media/aost-replay.png)

*Replay is a timestamp clause. I can show the moment before the bait fired.*

## The numbers

I froze the exam (`b043aea`) before any agent existed. Labels were not edited. Everything below is execution-graded. Full write-up: [`eval/RESULTS.md`](https://github.com/prasadt1/apprentice-crdb/blob/main/eval/RESULTS.md).

| Epoch | Live rules | Oracle (ceiling) | Nova Micro | Nova Lite |
|---|---|---:|---:|---:|
| `memory_zero` | 0 | 6/50 · 12% | 8/50 · 16% | 14/50 · 28% |
| `filters` | 2 | 7/50 · 14% | **21/50 · 42%** | 19/50 · 38% |
| `revenue_and_fiscal` | 4 | 31/50 · 62% | 18/50 · 36% | **19/50 · 38%** |
| `join_path` | 5 | **44/50 · 88%** | 13/50 · 26% | 16/50 · 32% |

Bold = that column's peak. Both agents peak *before* full memory. Lite is better cold and still ends below its own peak — so this is not Nova Micro being weak.

**The oracle is not an agent.** It is a selector over frozen SQL bodies, gated on exam metadata. Its 44/50 cannot fail and never wrote a line of SQL. I keep it only as the ceiling: what a perfect consumer of the retrieved rules would score. I briefly published that 44/50 as the learning curve. That was wrong. The correction is why the agent columns exist.

**Retrieval was not the bottleneck.** At `join_path`, every rule an item needed was in the model's context on **44/44** rule-bearing items. With five live rules and `k=5`, retrieval returns the whole corpus and ranks nothing. Every prompt carries all five rules — including on `unaffected` items that need none. Lite's `unaffected` goes 6/6 → 3/6. That is undifferentiated injection, not memory as such.

**The baits did not fire as designed.** I predicted six regressions. Lite resists four of six at full memory. q50 is wrong in every cell for both models at every epoch, including before its rule existed. q31 is wrong cold and right once `metric:revenue` lands — memory corrected a bias I had predicted it would cause. Self-reported `-- used_rules:` citations are not evidence: at `memory_zero`, with zero rules retrieved, Nova Micro still cited memory on 34/50 items.

The 56-point gap at full memory (oracle 88%, best agent 32%) is entirely *could the consumer use what it retrieved*. Storage and recall both look perfect at the exact epoch where accuracy is falling.

```bash
pip install -e ".[dev,aws]"
pytest -q
python eval/run_exam.py verify    # 50/50 gold reproduce labels; freeze sha256s match
```

## Reproduce it

Judges do **not** need my cluster to check the freeze. Clone the public repo:

```bash
git clone https://github.com/prasadt1/apprentice-crdb.git
cd apprentice-crdb
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python eval/run_exam.py verify
python eval/run_exam.py questions   # agent-facing view: id + question only
```

**Live memory (CockroachDB Cloud):**

```bash
export APPRENTICE_CRDB_DSN='postgresql://USER:PASS@HOST:26257/defaultdb?sslmode=verify-full'
apprentice migrate --try-vector-index
apprentice gc-ttl                   # measured gc.ttlseconds = 4500
apprentice educate --policy oracle  # writes eval/curve.json
```

**Agent curve (Amazon Bedrock, us-east-1):**

```bash
export APPRENTICE_EMBEDDER=bedrock AWS_REGION=us-east-1
export APPRENTICE_GEN_MODEL=amazon.nova-micro-v1:0
pip install -e ".[aws]"
apprentice educate --policy both
```

The warehouse is a local SQLite prop. CockroachDB holds the brain.

## How I built it

![Layered architecture: CLI and exam in, CockroachDB memory in the middle, Bedrock + SQLite on the edges](https://raw.githubusercontent.com/prasadt1/apprentice-crdb/main/docs/media/architecture.png)

*CockroachDB is the memory layer — rules, episodes, vectors, AOST. Bedrock generates. The warehouse is a prop. One binder for teaching; one answering path that cannot see the labels.*

Beyond what the diagram shows:

- **Freeze first** — `eval/questions.json` and `eval/labels.json` are immutable after `FREEZE.md`. Wrong label → erratum in RESULTS, never an edit.
- **Two curves on purpose** — oracle is the ceiling (did memory hold the rule). Agent is the measurement (could the model use it). The A−B gap is the finding.
- **Hard leakage rule** — the generator consumes `{id, question}` plus warehouse DDL and retrieved rule *statements*. Never `house_rules.py`, never `seed.sql`, never gold/naive/bait.
- **Vector index is real** — `CREATE VECTOR INDEX` on Basic succeeded; recall is `ORDER BY embedding <-> $1` inside the AOST transaction. Titan v2 is 1024-d (not 384); the column was widened to match.
- **Compressed clock** — Basic will not raise `gc.ttlseconds` above 4500. Epochs are minutes apart. I disclose that instead of pretending I have months of history.
- **Refuse bad SQL** — anything that is not a single `SELECT`/`WITH` grades wrong, not skipped.

**CockroachDB tools used**

| Tool | How, not just that it is configured |
|---|---|
| **Distributed vector indexing** | `CREATE VECTOR INDEX` on `semantic_rules.embedding`; answering path orders by `<->` |
| **Cloud Managed MCP Server** | Cursor connected to the live cluster (read path for inspection). Writes stay on the CLI. |
| **ccloud CLI** | 🔄 cluster list / zone proof — screenshot before submit |

**AWS services used**

| Service | How |
|---|---|
| **Amazon Bedrock** | Titan Text Embeddings V2 on write and query; Converse API for generation. Pre-registered model: `amazon.nova-micro-v1:0`. Replication arm (added after seeing the Micro drop, disclosed): `amazon.nova-lite-v1:0`. |
| **CockroachDB Cloud on AWS** | Basic cluster `solid-unicorn`, eu-central-1 — the memory plane. Bedrock calls run in us-east-1 (on-demand). |

## Challenges I ran into

- `AS OF` on the SELECT raced psycopg’s implicit `BEGIN` (“inconsistent AS OF SYSTEM TIME timestamp”). The fix is `BEGIN AS OF SYSTEM TIME <hlc>` on an autocommit connection, after waiting for the closed timestamp.
- Titan v2 does not do 384 dimensions. The first schema assumed 384 for a mock hasher. I widened to `VECTOR(1024)` rather than fake a Titan vector.
- The first educate run plateaued at 15/50 because the distiller named joins `join:customers`. I did not edit labels. I fixed the keys and re-ran.
- I published the oracle 44/50 as the learning curve, then had to take it back. The agent curves exist because of that mistake.
- With five rules and k=5, “vector recall” is just injecting the whole memory. The `unaffected` collapse is the receipt. Next experiment is smaller k / relevance gating — not a bigger model.
- Basic GC TTL is 75 minutes. I compressed the curriculum instead of claiming a year of memory.

## Accomplishments that I'm proud of

- Exam frozen **before** any graded learning run — same discipline as Premortem
- A finding that replicated: both models peak before full memory and decline
- Retrieval 44/44 at the epoch accuracy falls — the gap is utilization, not storage
- Publishing my own failed bait prediction instead of deleting it
- Taking back the 44/50 “learning curve” in public rather than leaving it up

## What I learned

- Memory that cannot be rewound is a log
- Storage and retrieval can both be perfect while the agent gets worse
- Self-reported memory citations are not evidence
- A bait that is wrong before its rule exists is measuring a prior, not a regression

## What's next for Apprentice

- Relevance-gated recall (smaller k, or a filter that does not inject unused rules) - this exam is the instrument
- Bedrock chat skin so a judge can ask one question at a chosen epoch
- 🔄 Lambda-hosted demo URL if a clone-and-run CLI is not enough for “functional demo”

## Links

| Evidence | Link |
|---|---|
| Source | [github.com/prasadt1/apprentice-crdb](https://github.com/prasadt1/apprentice-crdb) |
| Eval results | [eval/RESULTS.md](https://github.com/prasadt1/apprentice-crdb/blob/main/eval/RESULTS.md) |
| Freeze | [eval/FREEZE.md](https://github.com/prasadt1/apprentice-crdb/blob/main/eval/FREEZE.md) |
| Protocol | [eval/PROTOCOL.md](https://github.com/prasadt1/apprentice-crdb/blob/main/eval/PROTOCOL.md) |
| Demo video | 🔄 |
| Project page | 🔄 |

**Honest scope.** The warehouse is six orders by design — labels are hand-checkable. Single run per model at temperature=0. Two Nova-family models only (Claude on Bedrock needed an inference profile I did not have). Nova Lite was added *after* seeing the Micro drop, as a disclosed extra arm, not a replacement. The `unaffected` stratum is n=6. Epochs are minutes apart inside a 75-minute GC window. Every generated SQL string is in `eval/runs-nova-micro/` and `eval/runs-nova-lite/`.

<!-- ════════════ COPY TO HERE ════════════ -->

### Built with 🔄
One token per line. Do not paste commas or “CockroachDB Cloud Managed MCP Server” as a phrase — Devpost shreds multi-word tags.

```
python
cockroachdb
aws
bedrock
psycopg
sqlglot
pydantic
pytest
mcp
```

Optional extras if the form still looks sparse: `boto3` · `vector` · `sqlite`

### "Try it out" links 🔄

1. Repo: `https://github.com/prasadt1/apprentice-crdb`
2. Results: `https://github.com/prasadt1/apprentice-crdb/blob/main/eval/RESULTS.md`
3. 🔄 Hosted demo (Lambda / Pages) — add when it exists; do not duplicate two GitHub links that render as the same hostname

### Image gallery 🔄

**Budget:** video is the cover once it exists. Cap the carousel at **6**. Story already carries journey + curve + AOST + architecture (unframed) — do **not** re-upload those as the whole gallery unless you want the first slide to be the curve.

#### Planned carousel (upload in this order)

| # | Asset | Type | Caption (paste) | Why it’s here |
|---|---|---|---|---|
| 1 | `docs/media/learning-curve.png` | Diagram | Oracle rises to 88%. Both agents peak before full memory and decline. Retrieval at that last epoch is 44/44. | First slide = the finding |
| 2 | `docs/media/aost-replay.png` | Diagram | Same exam, earlier brain. `AS OF SYSTEM TIME` — not a backup restore. | Agentic Memory criterion |
| 3 | `docs/media/architecture.png` | Diagram | CockroachDB holds rules, episodes, vectors. Bedrock generates. Warehouse is a prop. | CRDB + AWS in one frame |
| 4 | `docs/media/product-workflow.png` | Diagram | Teach → distill → store → rewind → answer → grade. | Full loop, not chat-only |
| 5 | 🔄 LIVE: `apprentice recall --as-of <memory_zero HLC>` | Terminal | Empty keys at the first epoch — AOST, not a Python filter. | Working software |
| 6 | 🔄 LIVE: Bedrock / educate `--policy both` stderr | Terminal | Curve A and Curve B on the same HLCs. | The gap |

#### Do **not** upload to the carousel (already in the story)

| Asset | Covered by |
|---|---|
| `customer-journey.png` | Story (Inspiration) |
| Extra localhost IDE chrome | Nowhere — noise |

Regenerate PNGs after editing SVGs:

```bash
for f in docs/media/*.svg; do rsvg-convert -w 2400 "$f" -o "${f%.svg}.png"; done
```

### Video ⬜
Not filmed. Under 3:00. Climax is **not** a rising line.

**Title card (0:00–0:08)**
On-screen: `Apprentice` / `memory that helps, then hurts`.
Voice: “I built an analyst agent that ships its own learning curve. The curve went down.”

**Cold start (0:08–0:35)**
Terminal: `apprentice recall --as-of <memory_zero HLC>` → empty keys.
Voice: “Epoch one. Zero rules in CockroachDB. Nova Lite: fourteen out of fifty. Nova Micro: eight. The oracle, a selector over frozen SQL, gets six. That is the floor.”

**Partial memory (0:35–1:05)**
Cut to the three-curve chart, pause on `filters`.
Voice: “Two house rules land — soft-delete, cancelled orders. Micro jumps to twenty-one. Lite to nineteen. Memory helped.”

**The ugly epoch (1:05–1:50) — climax**
Split: left = retrieval log `44/44`. Right = scores Micro `13`, Lite `16`.
Then: `unaffected` table, Lite `6/6 → 3/6`.
Voice: “Full memory. Five rules. Retrieval is forty-four out of forty-four — every rule an item needed was in the prompt. Accuracy is already falling. On the six questions that need *no* house rule, Lite goes from six of six to three of six. k equals five with five rules. The retriever returns the whole corpus. It ranks nothing. That is not a storage miss. That is utilization.”

**Rewind (1:50–2:25)**
Live: `BEGIN AS OF SYSTEM TIME` / `apprentice recall --as-of` again → empty.
Voice: “Same cluster. Earlier brain. Not a backup restore. A timestamp. I can show you what it knew last Tuesday.”

**Close (2:25–2:50)**
Chart full-frame. Freeze sha256 line from `eval/FREEZE.md`.
Voice: “I froze the exam before I saw these numbers. Four of six bait predictions failed. One item memory *fixed* that I thought it would break. Storage worked. Recall worked. Utilization did not. Repo in the description.”

Do **not** film: warehouse-copilot tour, “watch it learn to 88%,” a rising-only oracle line presented as the product.

---

## Page 4 · Additional info

- **Repo:** ✅ `https://github.com/prasadt1/apprentice-crdb` (public, Apache-2.0)
- **Demo URL:** 🔄 CLI-only until a hosted URL exists — judges can clone; say so in Testing Instructions
- **CRDB tools (≥2):** ✅ Vector index (used on the answering path) · ✅ MCP (Cursor, inspect) · 🔄 ccloud (screenshot)
- **AWS (≥1):** ✅ Bedrock (Titan + Converse) · cluster is Cockroach Cloud on AWS eu-central-1
- **Country:** ⬜
- **New during period:** ✅ Yes (first public commit 2026-08-11)
- **Pre-existing code:** ✅ None beyond standard libs + AI assistants (Cursor, Claude). Exam authored independently and frozen before learning.
- **Testing instructions** ✅ paste:

> No login. Python 3.11+.
>
> 1. `git clone https://github.com/prasadt1/apprentice-crdb.git && cd apprentice-crdb`
> 2. `python3.11 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
> 3. `pytest -q` and `python eval/run_exam.py verify` — expect VERIFY OK, freeze sha256s match.
> 4. Read [`eval/RESULTS.md`](https://github.com/prasadt1/apprentice-crdb/blob/main/eval/RESULTS.md) for the published oracle curve and HLC timestamps.
> 5. Optional live path: set `APPRENTICE_CRDB_DSN`, then `apprentice migrate --try-vector-index` and `apprentice educate --policy oracle`.
> 6. Optional agent path: `APPRENTICE_EMBEDDER=bedrock AWS_REGION=us-east-1 apprentice educate --policy both` (needs Bedrock model access).

---

## Post-draft checklist (not submitted)

- [x] Curve B numbers written into RESULTS (`4df72a5`) + this draft
- [x] README + gallery SVGs/PNGs lead with 14 / 19 / 19 / 16, not the oracle rise
- [ ] Video filmed + YouTube URL pasted in story + Video field
- [ ] `ccloud cluster list` screenshot in gallery or proof doc
- [ ] GitHub social preview (`docs/media/social-preview.png`) uploaded on the GitHub repo settings page
- [ ] Built With tokens entered one at a time
- [ ] Story field pasted between the markers only
- [ ] MCP left read-only for the editor; app writes stay on CLI
