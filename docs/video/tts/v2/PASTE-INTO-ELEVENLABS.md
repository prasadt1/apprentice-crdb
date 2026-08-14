# VO v2 — record as TEN separate files

**Do not paste this as one block.** v1 was a single 85s read, which is exactly why every
paragraph landed on the wrong picture. Synthesise each segment separately, save as
`s0.mp3` … `s9.mp3`, and cut each picture segment to its own audio file. Sync then cannot
drift.

Voice: calm, first person, **speed 1.0**, no SSML. Target ~140 wpm.
After each download, check the length against the target below.

```bash
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 sN.mp3
```

Numbers spoken aloud: *forty-four out of forty-four* · *twenty thousand* ·
*ninety-five thousand* · *eighty-eight percent*.

> **v2.1 (2026-08-15): s2–s5 rewritten for q02.** The q11 cold failure was luck-based —
> Nova Lite answered it correctly cold on 2026-08-14. q02's cold failure is
> knowledge-based (1-Feb fiscal year + refund netting) and was cold-wrong in both
> archived arms. Only s2–s5 need re-recording; s0, s1, s6–s9 are unchanged.

---

## s0 — title · target 12–13s (unchanged)

Analyst agents write confident SQL, and still get the house rules wrong. Soft-deleted orders. Cancelled orders. Fiscal calendars. Correct them today, and the same mistake comes back next week.

## s1 — empty memory · target 9–10s (unchanged)

Here is the memory, empty. I capture a timestamp — t-zero. Nothing is stored yet, and CockroachDB will be able to prove that later.

## s2 — ask cold · target 16–17s (REWRITTEN for q02)

I ask one question from the fifty-question exam I froze before any agent existed. Zero rules retrieved. Nova Lite assumes the calendar quarter and answers twenty thousand. But this company's fiscal year starts in February. The exam says wrong.

## s3 — teach · target 15–16s (REWRITTEN for q02)

Now one correction. sqlglot diffs the fix against the attempt as syntax trees — no model in this path — and distils four rules: the fiscal calendar, refund netting, two hygiene filters. They land in CockroachDB under a new timestamp.

## s4 — ask again · target 15–17s (REWRITTEN for q02)

Same question, same model. This time recall returns those rules, the window shifts to May through July, refunds come off, and the answer is ninety-five thousand. The frozen exam says correct. One correction moved the behaviour.

## s5 — rewind · target 15–17s (REWRITTEN: four rules)

Now the part only CockroachDB gives me. Same cluster, two timestamps. As of now: four rules. As of t-zero: zero rules, because none existed yet. That is not a backup restore. It is a clause.

## s6 — the frozen exam · target 14–16s

Scale it up. Four memory snapshots, the same frozen exam replayed at each one, graded by executing the SQL. The ceiling climbs to eighty-eight percent. Both Bedrock models peak early, and fall.

## s7 — the curve · target 18–20s  ← the climax, do not rush

This is the finding. At full memory every rule an item needed was retrieved — forty-four out of forty-four. Retrieval is perfect, and accuracy is already down. Storage worked. Recall worked. Utilisation did not. That third leg is what almost nobody measures.

## s8 — consoles · target 11–12s

CockroachDB Cloud on AWS holds the rules, the vectors and the timestamps. Amazon Bedrock embeds each rule with Titan and generates every query through Converse.

## s9 — close · target 14–15s

Apprentice is a release gate for agent memory. It catches the case where storage and recall both look perfect while the agent is quietly getting worse. The exam, the receipts and the code are in the repo.

---

## Lines that must not be spoken

- *"the two rules fixed it"* — the cold query already contained the soft-delete predicate.
  The receipt is on screen; narrate observables only (s4 does).
- *"watch it learn to eighty-eight percent"* — 88% is the oracle **ceiling**, a selector
  over frozen SQL. It is not the agent.
- Any GDPR / compliance framing, or a rising-curve pitch.
