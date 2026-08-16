# Hackathon audit (consolidated) — 2026-08-16

Against `coackroachdb-aws-hackathon-deep-dive.md` + live submission.
Deadline: **Tue 18 Aug 2026, 5:00pm EDT**.

## Hard requirements — pass

| Requirement | Status |
|---|---|
| CRDB as persistent memory, on AWS | Pass |
| ≥2 CRDB tools | Pass (3): vector · MCP (dev) · ccloud |
| ≥1 AWS service | Pass — claim **Bedrock + Lambda** |
| Public repo + detectable OSS license | Pass (Apache-2.0) |
| Functional demo URL | Pass (live Ask) |
| Video &lt;3 min, public, shows CRDB memory | Pass (2:59) |
| Identify tools + how | Pass (after re-paste) |
| New during period | Pass |

Do **not** tick Agent Skills.

## Judge criteria — where weight sits

| Criterion | Assessment |
|---|---|
| Agentic Memory Design | Strong — AOST replay, SERIALIZABLE, utilization gap |
| Technical Implementation | Strong once Lambda is claimed |
| Real-World Impact | Medium-strong — analytics engineer + reviewer |
| Production Readiness | Medium-high — guardrails in Lambda paragraph |
| Creativity & Originality | Very strong — non-monotonic finding, failed prediction published |

Rob Reid FAQ alignment: SERIALIZABLE ✓ · agentic not pure-ReAct ✓ · creativity of example ✓ · skip TTL/CDC bolt-ons.

## The gap that mattered

Lambda ran the live agent turn but the form said Bedrock singular. **Fixed in draft** (story AWS table, gallery ticks, meaningfully-integrated paragraph, testing instructions, Built With `aws-lambda`).

## Your form checklist (do these)

1. Re-paste story between markers in `docs/devpost-article-draft.md`
2. Tick **Amazon Bedrock** + **AWS Lambda**
3. Confirm three CRDB tools (not Agent Skills)
4. Re-paste “meaningfully integrated” (§7) — includes Lambda
5. Paste CRDB AI tools feedback (§11)
6. Update testing instructions (§2) — live Ask called out
7. Built With: add `aws-lambda`
8. Confirm Video field = `https://youtu.be/xmxEFkEiJLY`
9. Optional: GitHub social preview upload
10. Rotate leaked CRDB password when convenient

## Done in repo

- [x] Draft Lambda claims
- [x] GitHub topics: `cockroachdb`, `agentic-memory`, `amazon-bedrock`, `aws-lambda`, `vector-search`, `llm-evaluation`
