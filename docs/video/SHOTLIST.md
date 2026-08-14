# Apprentice — demo video shot list (v2)

Target **2:35**. Hard cap 3:00; judges are not required to watch past it.

**Why v2 exists.** v1 was 1:50 with the terminal at 54% of runtime, the curve at 10%, and
every VO paragraph landing on the wrong picture (the "44/44 — utilisation did not" line
played over scrolling terminal text; the chart appeared 15s later in silence; 24.8s of
silent stills at the end). The fix is not re-syncing v1. It is cutting to **beats**: every
outcome gets a banner, a pause, and its own VO line, so picture and audio lock by
construction.

## Recording setup (do this first)

| Setting | Value | Why |
|---|---|---|
| Terminal columns | **100** (not 207) | v1 was 7.4px/char ≈ 12px cap height at 1080p — unreadable. 100 cols ≈ 15px/char |
| Font | 18–20pt monospace | Same reason |
| Window | Fill ~90% of a 1920×1080 capture | No wasted margin |
| Theme | Dark, high contrast | — |
| Command | `APPRENTICE_DEMO_RESET=YES bash tools/run_live_demo_v2.sh` | Banners + pauses built in |
| Pace | `DEMO_BEAT=3` (default) | Each outcome holds 3s. Raise to 4 if VO feels rushed |

Record **one clean take**. The command sequence is deterministic; **the model's cold
answer is not** — on 2026-08-14 Nova Lite answered q11 correctly cold, which is why the
demo question is now **q02**: hitting its gold answer (95,000) requires knowing the
fiscal year starts 1 February *and* netting refunds, so a cold model cannot luck into
it. Evidence: q02 was cold-wrong in both archived arms and correct in both once the
rules landed. If a beat runs long, trim in post rather than re-shooting.

---

## Shots

Durations are picture. VO word counts assume ~140 wpm. Terminal shots come from one take;
cut on the banner lines.

### S0 · Title — 0:00–0:13 (13s)

**Picture:** `docs/video/slides/01-title.png` — "Apprentice / memory that helps, then hurts"

**VO** (29 w):
> Analyst agents write confident SQL, and still get the house rules wrong. Soft-deleted orders. Cancelled orders. Fiscal calendars. Correct them today, and the same mistake comes back next week.

---

### S1 · Empty memory — 0:13–0:23 (10s)

**Picture:** Terminal, `SECTION 1 · EMPTY MEMORY` banner → `OUTCOME · 0 rules at t0`

**VO** (23 w):
> Here is the memory, empty. I capture a timestamp — t-zero. Nothing is stored yet, and CockroachDB will be able to prove that later.

---

### S2 · Ask cold — 0:23–0:40 (17s)

**Picture:** Terminal, `SECTION 2 · ASK COLD` → receipt (guessed Apr–Jun window visible) →
`OUTCOME · q02 — WRONG` (answer 20,000)

**VO** (40 w):
> I ask one question from the fifty-question exam I froze before any agent existed. Zero rules retrieved. Nova Lite assumes the calendar quarter and answers twenty thousand. But this company's fiscal year starts in February. The exam says wrong.

---

### S3 · Teach one correction — 0:40–0:56 (16s)

**Picture:** Terminal, `SECTION 3 · TEACH` → four distilled rules → `OUTCOME · 4 rules stored`

**VO** (38 w):
> Now one correction. sqlglot diffs the fix against the attempt as syntax trees — no model in this path — and distils four rules: the fiscal calendar, refund netting, two hygiene filters. They land in CockroachDB under a new timestamp.

---

### S4 · Ask again — 0:56–1:13 (17s)

**Picture:** Terminal, `SECTION 4 · ASK AGAIN` → receipt (May–Jul window + refunds visible) →
`OUTCOME · q02 — CORRECT` (answer 95,000)

**VO** (36 w):
> Same question, same model. This time recall returns those rules, the window shifts to May through July, refunds come off, and the answer is ninety-five thousand. The frozen exam says correct. One correction moved the behaviour.

---

### S5 · Rewind — 1:13–1:30 (17s)

**Picture:** Terminal, `SECTION 5 · REWIND` → two recalls side by side → `OUTCOME · now 4 · t0 0`

**VO** (36 w):
> Now the part only CockroachDB gives me. Same cluster, two timestamps. As of now: four rules. As of t-zero: zero rules, because none existed yet. That is not a backup restore. It is a clause.

*This is the strongest CockroachDB beat and v1 buried it. The t0 recall runs **after**
teaching, so the contrast is live: memory has rules now, and the past is still empty.*

---

### S6 · The frozen exam — 1:30–1:50 (20s)

**Picture:** Terminal, `SECTION 6 · THE FROZEN EXAM` → `apprentice report` table. Hold on the table.

**VO** (33 w):
> Scale it up. Four memory snapshots, the same frozen exam replayed at each one, graded by executing the SQL. The ceiling climbs to eighty-eight percent. Both Bedrock models peak early, and fall.

---

### S7 · The curve — 1:50–2:13 (23s) ← **the climax**

**Picture:** `docs/media/learning-curve.png` full frame. Hold long enough to read the
"THE THIRD LEG" box. In v1 this had 11s and no narration.

**VO** (43 w):
> This is the finding. At full memory every rule an item needed was retrieved — forty-four out of forty-four. Retrieval is perfect, and accuracy is already down. Storage worked. Recall worked. Utilisation did not. That third leg is what almost nobody measures.

---

### S8 · Consoles — 2:13–2:27 (14s)

**Picture:** Three shots under one VO.
1. **CockroachDB Cloud SQL Shell** — `SELECT rule_key, statement FROM semantic_rules WHERE superseded_by IS NULL;` with results (not the overview dashboard).
2. **AWS Bedrock Model catalog** — Amazon Nova models (Nova 2 Lite visible in the grid).
3. **AWS Bedrock Model catalog** — Titan Text Embeddings V2 (matches the embed line in the VO).

**VO** (27 w):
> CockroachDB Cloud on AWS holds the rules, the vectors and the timestamps. Amazon Bedrock embeds each rule with Titan and generates every query through Converse.

*Blur or crop account ids and cluster hostnames. Never show the DSN.*

---

### S9 · Close — 2:27–2:41 (14s)

**Picture:** `docs/video/slides/99-end.png` — repo URL + project page. Freeze-frame the
`eval/FREEZE.md` sha256 line for 2s if it fits.

**VO** (35 w):
> Apprentice is a release gate for agent memory. It catches the case where storage and recall both look perfect while the agent is quietly getting worse. The exam, the receipts and the code are in the repo.

---

## Totals

| | |
|---|---|
| Picture | **2:41** |
| VO | ~301 words ≈ **2:09** spoken, spread across 10 segments |
| Air | ~30s distributed as pauses on outcomes and the curve — deliberate, not a silent tail |

If it overruns 3:00, trim S2/S3/S4 by 2s each (lower `DEMO_BEAT`), never S7.

## Assembly

Record VO **per segment** (10 files), not one continuous read. Then each picture segment is
cut to its own audio file and sync cannot drift. v1's single 85s read is exactly why every
paragraph landed on the wrong shot.

```bash
# per-segment: place s0.mp3 under 01-title.mp4, s1.mp3 under the S1 terminal cut, etc.
ffmpeg -i shot.mp4 -i sN.mp3 -c:v copy -c:a aac -shortest out/NN-shot.mp4
```

## Do not film

- A warehouse-copilot tour
- "Watch it learn to 88%" — the oracle line is a ceiling, not the product
- The DSN, AWS account ids, or cluster hostnames
