# Results

Frozen exam: `eval/FREEZE.md` (2026-08-11). Labels were not edited after freeze.

## Memory-zero baseline

Policy: competent SQL with **no house-rule memory** (`naive_sql` fixtures). This is the protocol floor, not a Bedrock run.

| | |
|---|---|
| Score | **6 / 50 = 12%** |
| Correct | all 6 `unaffected` items |
| Wrong | every item that needs a house rule |

Regression baits at memory-zero (no over-applied rules yet):

| id | outcome |
|---|---|
| q03 | correct |
| q07 | correct |
| q31 | wrong (also needs fiscal + live-order filters) |
| q36 | wrong (needs net + live-order filters on a calendar window) |
| q47 | correct |
| q50 | wrong (needs soft-delete filter) |

Re-run: `apprentice baseline`

## Education / AOST curve

Measured `gc.ttlseconds = 4500` (75 minutes) on Basic. Epochs are minutes apart, not calendar days.
Replay used `BEGIN AS OF SYSTEM TIME <cluster_logical_timestamp>` on the live cluster.

Published run 2026-08-11 (`eval/curve.json`):

| Epoch | Correct | Accuracy | Live rule keys | What moved |
|---|---:|---:|---|---|
| `memory_zero` | 6 / 50 | 12% | *(none)* | Floor: the 6 `unaffected` items |
| `filters` | 7 / 50 | 14% | `filter:orders_soft_delete`, `filter:orders_not_cancelled` | Soft-delete 0→4/8. All six baits red; `unaffected` 6→3 |
| `revenue_and_fiscal` | 31 / 50 | 62% | + `metric:revenue`, `calendar:fiscal` | Fiscal 0→7/8, traps 4/4, composition 5/8. Join still 0/6 |
| `join_path` | **44 / 50** | **88%** | + `join:orders_customers_regions` | Join 6/6, composition 8/8. The six misses are the six baits |

The six items still wrong at the last epoch are exactly the published regression baits (q03, q07, q31, q36, q47, q50). Memory made the agent better *and* over-apply. AOST can replay the moment before that.

| id | memory_zero | filters | revenue_and_fiscal | join_path |
|---|---|---|---|---|
| q03 | correct | wrong | wrong | wrong |
| q07 | correct | wrong | wrong | wrong |
| q31 | wrong | wrong | wrong | wrong |
| q36 | wrong | wrong | wrong | wrong |
| q47 | correct | wrong | wrong | wrong |
| q50 | wrong | wrong | wrong | wrong |

AOST ticks (HLC decimals):

- memory_zero `1786459251103416273.0000000000`
- filters `1786459271499784483.0000000000`
- revenue_and_fiscal `1786459303318273257.0000000000`
- join_path `1786459319281930469.0000000000`

An earlier cluster run plateaued at 15/50 because AST-diff wrote `filter:generic` / `join:customers` instead of the exam keys. That run is superseded; I did not edit labels to chase the score.

Re-run: `apprentice educate` (needs `APPRENTICE_CRDB_DSN`). Writes `eval/curve.json` and `eval/runs/answers_*.json`.
