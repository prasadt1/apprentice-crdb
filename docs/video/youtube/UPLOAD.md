# YouTube upload — Apprentice demo

Video file: `docs/video/youtube/apprentice-demo-final.mp4` (~2:59, 1920×1080).
Thumbnail: `docs/video/youtube/thumbnail.png` (1280×720).
Exam chart (for the article, not the cover): `docs/video/youtube/thumbnail-exam-chart.png`.

Paste the blocks below into YouTube Studio. Keep the video **Unlisted** until the Devpost submission is live, then set it Public (or leave Unlisted if Devpost only needs the embed URL).

---

## Title (≤100 characters)

```
Apprentice: memory that helps, then hurts | CockroachDB × AWS
```

Backup if you want the number in the title:

```
44/44 retrieved — accuracy still fell | Apprentice (CockroachDB × AWS)
```

---

## Description

```
Analyst agents write confident SQL and still get the house rules wrong. Soft-deleted orders. Cancelled orders. Fiscal calendars. Correct them today, and the same mistake comes back next week.

Apprentice is a release gate for agent memory. A human teaches a SQL correction; sqlglot distils rules (no model on that path); CockroachDB stores the rules, Titan vectors, and timestamps; Bedrock answers; a frozen 50-question exam grades storage, recall, and utilization separately.

The finding: at full memory, retrieval is 44/44. Storage worked. Recall worked. Utilization did not. Both Nova Micro and Nova Lite peak on partial memory and decline.

Built for the CockroachDB × AWS Agentic Memory Hackathon.

0:00  The problem
0:13  How this run works
0:30  Empty memory, t-zero
0:42  Ask cold — fiscal Q2, 20,000, wrong
1:00  Teach one correction — four rules in CockroachDB
1:19  Ask again — 95,000, correct
1:38  Rewind with AS OF SYSTEM TIME
1:54  Scale the frozen exam
2:10  The curve — 44/44 and falling accuracy
2:33  CockroachDB Cloud + Bedrock
2:46  Repo and receipts

Hosted page
https://prasadt1.github.io/apprentice-crdb/

Code
https://github.com/prasadt1/apprentice-crdb

The finding
https://github.com/prasadt1/apprentice-crdb/blob/main/eval/RESULTS.md

Hackathon
https://cockroachdb-ai.devpost.com/

Apache-2.0. I am the author. CockroachDB Cloud on AWS holds the brain; Amazon Bedrock (Titan + Nova via Converse) embeds and generates.

#CockroachDB #AWS #AgenticMemory #Bedrock #AmazonBedrock
```

---

## Tags (YouTube → Details → Show more)

```
CockroachDB, AWS, Amazon Bedrock, Agentic Memory, agent memory, Titan embeddings, Nova Lite, Nova Micro, AS OF SYSTEM TIME, AOST, sqlglot, SQL agent, retrieval, utilization, frozen exam, hackathon, apprentice-crdb
```

Hashtags in the description (YouTube also uses the first 3 as title chips if you add them at the end of the title — I left the title clean).

---

## Studio settings

| Field | Value |
| --- | --- |
| Visibility | Unlisted until Devpost is submitted |
| Audience | No, not made for kids |
| Category | Science & Technology |
| Language | English |
| Captions | Auto-generate (English) |
| Altered content | No |
| Recording date | 2026-08-15 |
| License | Standard YouTube (source code is Apache-2.0; the video is the demo) |
| Comments | Hold for review, or allow — your call |
| Cards | At ~2:10, card to GitHub; at ~2:46, card to the hosted page |
| End screen | Subscribe (optional) + link to GitHub + hosted page |
| Playlist | new: “Apprentice / CockroachDB hackathon” |

---

## Devpost embed notes

1. Upload this thumbnail as the YouTube custom thumbnail *before* you paste the URL into Devpost.
2. Devpost’s gallery crops 16:9 YouTube posters from the sides. Keep using this file — the 44/44 and the word *Apprentice* sit inside the center ~70% of width.
3. Same PNG can be the project’s gallery image if Devpost asks for a separate cover (16:9). Do not use the title slide (`01-title.png`); it is left-heavy and will clip.

---

## Thumbnail intent

Dark editorial cover: mark + wordmark **Apprentice**, tagline **Memory you can rewind.**,
growth-ring hero, footer CockroachDB × AWS. No screenshots, no vendor logos, no desk
photography.

**Source of truth is `thumbnail.svg`. Never hand-edit or re-export `thumbnail.png`** —
regenerate it, so the rings stay semantically correct:

```bash
rsvg-convert -w 1280 -h 720 docs/video/youtube/thumbnail.svg -o docs/video/youtube/thumbnail.png
```

The rings are not decoration. They read **outward through time**, like real growth rings,
and there are exactly four because there are four AOST epochs in `eval/RESULTS.md`:
t0 `memory_zero` (0 rules, innermost, accented — the epoch rewound to) → t1 `filters` (2)
→ t2 `revenue_and_fiscal` (4) → t3 `join_path` (5, outermost). The read head travels
**inward** to t0, which is what `AS OF SYSTEM TIME` does and what SECTION 5 of the demo
shows. An earlier render had `AS OF t0` on an outer ring — backwards — and was letterboxed
inside a dark border; both are fixed. Full bleed, no border.

Identity is shared across surfaces: `docs/media/mark.svg` → `mark-512.png` /
`mark-1024.png` for the GitHub repo avatar (artwork sits inside r=200, so a circular crop
is safe). Exam chart for the write-up: `thumbnail-exam-chart.png`.
