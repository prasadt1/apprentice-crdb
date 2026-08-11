# Exam freeze

**Date frozen:** 2026-08-11
**Frozen by:** Claude (exam protocol + labels lane, per `docs/LABOR.md`), before any
graded learning run and before the Bedrock agent existed in any tunable form.

## Frozen artifacts

| File | sha256 |
|---|---|
| `eval/questions.json` | `c644565ac522d483e8e9841af9ec56f36df610e4cd516687aeab50ae69b1d911` |
| `eval/labels.json` | `8ce8c1481acd20bd24a344cb5fa4a566774b0261909827839509d84cfc161a91` |

50 questions, 50 execution-signature labels. Protocol, strata, invariants, and
limitations: `eval/PROTOCOL.md` (sha256 at freeze time
`c4ecd5842786059888eb9144d3c4be2f8c8f7243dd4620a9c866b679c3ce8358`; the protocol
document may gain clarifications after the freeze, but the two frozen artifacts and
the grading rule may not change).

## No further edits

From this commit forward, `questions.json` and `labels.json` are immutable:

- A wrong label is an **erratum in `eval/RESULTS.md`** — item id, what was wrong,
  corrected value. Scored runs keep the frozen label; published curves state errata.
- `run_exam.py emit-labels` refuses to run while this file exists.
- `run_exam.py verify` re-checks at any time that the gold SQL still reproduces the
  frozen labels and that all authoring invariants hold.
- The agent-facing exam is `run_exam.py questions` (id + question text only).

Verification at freeze time: `verify` green (50/50 reproduce labels, divergence and
leakage invariants hold), repo test suite green (6/6), naive-baseline smoke grade
6/50 = 12% (unaffected stratum only), matching the protocol's floor.
