#!/usr/bin/env bash
# Live demo, structured for filming: six titled sections, one highlighted outcome each,
# deliberate pauses so every beat gets its own voiceover segment.
#
#   APPRENTICE_DEMO_RESET=YES bash tools/run_live_demo_v2.sh
#
# Terminal: 100 columns, 18-20pt. v1 ran 207 columns and was unreadable at 1080p.
# Tuning:   DEMO_BEAT=5   seconds each outcome holds on screen (use 5 for filming)
#           DEMO_TYPE=0.015  per-character delay when echoing a command (0 = instant)
# Filming: do NOT scroll. Each section clears the screen so the beat stays in frame.
#
# Full receipts still land in docs/video/live/session/. The screen shows the condensed
# view; the files keep everything.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/docs/video/live/session"
# q02 (fiscal Q2 net revenue) — chosen because its COLD failure is knowledge-based, not
# luck-based: hitting 95,000 needs the 1-Feb fiscal start AND refund netting; no plausible
# guess lands there. q11's cold failure depended on the model forgetting filters, and on
# 2026-08-14 Nova Lite added them spontaneously and answered q11 correctly cold. Evidence:
# q02 was cold-wrong in BOTH archived arms and correct in both once the rules landed.
QUESTION_ID="${APPRENTICE_DEMO_QUESTION:-q02}"
BEAT="${DEMO_BEAT:-5}"
TYPE_DELAY="${DEMO_TYPE:-0.015}"
COLS=100
CLEAR_BETWEEN="${DEMO_CLEAR:-1}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT}/.venv/bin/python"
else
  PYTHON_BIN="python3.11"
fi

# ---------- preflight (unchanged from v1) ----------
if [[ -z "${APPRENTICE_CRDB_DSN:-}" ]]; then
  echo "APPRENTICE_CRDB_DSN is not set. Export it in this terminal; never paste it into the video."
  exit 2
fi
if [[ "${APPRENTICE_DEMO_RESET:-}" != "YES" ]]; then
  echo "This demo resets the live memory tables before rebuilding fresh AOST epochs."
  echo "Run again with APPRENTICE_DEMO_RESET=YES after confirming the published runs are archived."
  exit 2
fi
if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS credentials are not available to Amazon Bedrock."
  exit 2
fi
if ! "${PYTHON_BIN}" -c "import sqlglot, psycopg" >/dev/null 2>&1; then
  echo "Python deps missing in ${PYTHON_BIN}. Run: pip install -e '.[aws]'"
  exit 2
fi

mkdir -p "${OUT}"
export PYTHONPATH="${ROOT}/src"
export APPRENTICE_EMBEDDER="${APPRENTICE_EMBEDDER:-bedrock}"
export APPRENTICE_GEN_MODEL="${APPRENTICE_GEN_MODEL:-amazon.nova-lite-v1:0}"
export APPRENTICE_RECALL_K="${APPRENTICE_RECALL_K:-5}"
APP=("${PYTHON_BIN}" -m apprentice_crdb.cli)

# ---------- presentation helpers ----------
BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
ORANGE=$'\033[38;5;208m'; GREEN=$'\033[38;5;42m'; RED=$'\033[38;5;203m'; BLUE=$'\033[38;5;39m'

rule() { printf '%s%s%s\n' "${DIM}" "$(printf '─%.0s' $(seq 1 ${COLS}))" "${RESET}"; }

banner() { # banner <n> <title>
  if [[ "${CLEAR_BETWEEN}" == "1" ]]; then
    clear
    printf '\n%s  Apprentice — live memory demo%s\n' "${BOLD}" "${RESET}"
    say "CockroachDB Cloud on AWS · Amazon Bedrock · frozen 50-question exam"
    printf '\n'
  else
    printf '\n\n'
  fi
  rule
  printf '%s%s  SECTION %s · %s%s\n' "${BOLD}" "${ORANGE}" "$1" "$2" "${RESET}"
  rule; printf '\n'
  sleep 2
}

say() { printf '%s  %s%s\n' "${DIM}" "$1" "${RESET}"; }

cmd() { # cmd <text>  — echo a prompt line, typed
  printf '\n%s$ %s' "${BOLD}" "${RESET}"
  if [[ "${TYPE_DELAY}" == "0" ]]; then printf '%s\n' "$1"
  else
    local i
    for ((i=0; i<${#1}; i++)); do printf '%s' "${1:i:1}"; sleep "${TYPE_DELAY}"; done
    printf '\n'
  fi
}

outcome() { # outcome <colour> <text>
  printf '\n%s%s  ▶ OUTCOME · %s%s\n' "${BOLD}" "$1" "$2" "${RESET}"
  sleep "${BEAT}"
}

# Condensed probe view: question, retrieval, the predicate diff, the number, the verdict.
show_probe() { # show_probe <receipt-file>
  "${PYTHON_BIN}" - "$1" <<'PY'
import json, re, sys, textwrap
raw = open(sys.argv[1]).read()
def field(name, default=""):
    m = re.search(rf"^{name}:\s*(.*)$", raw, re.M)
    return m.group(1).strip() if m else default
print("  question : " + "\n             ".join(textwrap.wrap(field("question"), 76)))
print("  model    : " + field("model"))
print("  retrieved: " + field("retrieved"))
for m in re.finditer(r"^\s+- ([a-z_]+:[a-z_]+):", raw, re.M):
    print("             \033[38;5;39m• " + m.group(1) + "\033[0m")
sql = raw.split("sql:", 1)[1].split("result:", 1)[0] if "sql:" in raw else ""
preds = [l.strip() for l in sql.splitlines()
         if re.search(r"\b(WHERE|AND|BETWEEN|ordered_at|refund|status|deleted_at)\b", l)]
if preds:
    print("  filters  :")
    for p in preds[:6]:
        print("             " + p)
try:
    res = json.loads(raw.split("result:", 1)[1].split("frozen_exam:", 1)[0])
    print("  columns  : " + ", ".join(res["columns"]))
    print(f"  answer   : {res['rows'][0][0]:,}")
except Exception:
    pass
PY
}

clear
printf '\n%s  Apprentice — live memory demo%s\n' "${BOLD}" "${RESET}"
say "CockroachDB Cloud on AWS · Amazon Bedrock · frozen 50-question exam"
sleep 2

# ══════════════════════════════ 1 ══════════════════════════════
banner 1 "EMPTY MEMORY"
say "Wipe agent memory and capture the timestamp before anything is learned."
cmd "apprentice memory-reset --yes"
"${APP[@]}" memory-reset --yes >"${OUT}/memory-reset.json"
ZERO_HLC="$("${PYTHON_BIN}" -c "import json,sys;print(json.load(open(sys.argv[1]))['memory_zero_as_of'])" "${OUT}/memory-reset.json")"
printf '%s\n' "${ZERO_HLC}" >"${OUT}/memory-zero.hlc"
printf '  t0 = %s\n' "${ZERO_HLC}"

cmd "apprentice recall --as-of \$t0"
"${APP[@]}" recall --as-of "${ZERO_HLC}" --limit 5 >"${OUT}/recall-memory-zero.json"
printf '  keys = []\n'
outcome "${BLUE}" "0 rules at t0"

# ══════════════════════════════ 2 ══════════════════════════════
banner 2 "ASK COLD"
say "One question from the exam frozen at commit b043aea, before any agent existed."
cmd "apprentice probe ${QUESTION_ID} --as-of \$t0"
"${APP[@]}" probe "${QUESTION_ID}" --as-of "${ZERO_HLC}" >"${OUT}/probe-memory-zero.txt"
show_probe "${OUT}/probe-memory-zero.txt"
outcome "${RED}" "${QUESTION_ID} — WRONG"

# ══════════════════════════════ 3 ══════════════════════════════
banner 3 "TEACH ONE CORRECTION"
say "sqlglot diffs attempt vs correction as syntax trees. No model in this path."
cmd "apprentice teach --attempt fiscal-revenue-attempt.sql --correction fiscal-revenue-correction.sql"
"${APP[@]}" teach \
  "What was total net revenue for fiscal Q2 2026? Return columns: revenue_cents." \
  --attempt "${ROOT}/examples/demo/fiscal-revenue-attempt.sql" \
  --correction "${ROOT}/examples/demo/fiscal-revenue-correction.sql" \
  >"${OUT}/teach-filters.json"
FILTER_HLC="$("${PYTHON_BIN}" -c "import json,sys;print(json.load(open(sys.argv[1]))['as_of'])" "${OUT}/teach-filters.json")"
printf '%s\n' "${FILTER_HLC}" >"${OUT}/filters.hlc"
N_RULES="$("${PYTHON_BIN}" -c "import json,sys;print(len(json.load(open(sys.argv[1]))['rules']))" "${OUT}/teach-filters.json")"
"${PYTHON_BIN}" - "${OUT}/teach-filters.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
for r in d["rules"]:
    print(f"  \033[38;5;39m• {r['rule_key']}\033[0m")
    print(f"    {r['statement']}")
print(f"  t1 = {d['as_of']}")
PY
outcome "${GREEN}" "${N_RULES} rules stored in CockroachDB"

# ══════════════════════════════ 4 ══════════════════════════════
banner 4 "ASK AGAIN"
say "Same question. Same model. Memory is the only thing that changed."
cmd "apprentice probe ${QUESTION_ID} --as-of \$t1"
"${APP[@]}" probe "${QUESTION_ID}" --as-of "${FILTER_HLC}" >"${OUT}/probe-after-teaching.txt"
show_probe "${OUT}/probe-after-teaching.txt"
outcome "${GREEN}" "${QUESTION_ID} — CORRECT"

# ══════════════════════════════ 5 ══════════════════════════════
banner 5 "REWIND"
say "Same cluster, two timestamps. The past is still queryable."
cmd "apprentice recall --as-of \$t1   # now"
"${APP[@]}" recall --as-of "${FILTER_HLC}" --limit 5 >"${OUT}/recall-after-teaching.json"
"${PYTHON_BIN}" -c "
import json,sys
rows=json.load(open(sys.argv[1]))
print(f'  {len(rows)} rule(s): ' + ', '.join(r['rule_key'] for r in rows))" "${OUT}/recall-after-teaching.json"

cmd "apprentice recall --as-of \$t0   # then"
"${APP[@]}" recall --as-of "${ZERO_HLC}" --limit 5 >"${OUT}/recall-memory-zero.json"
printf '  0 rule(s): []   %s(because none existed at t0)%s\n' "${DIM}" "${RESET}"
N_NOW="$("${PYTHON_BIN}" -c "import json,sys;print(len(json.load(open(sys.argv[1]))))" "${OUT}/recall-after-teaching.json")"
outcome "${ORANGE}" "now ${N_NOW} rules · t0 still 0 — AS OF SYSTEM TIME, not a restore"

# ══════════════════════════════ 6 ══════════════════════════════
banner 6 "THE FROZEN EXAM"
say "Four snapshots, 50 questions each, graded by executing the SQL."
cmd "apprentice educate --policy oracle"
say "Building four AOST epochs off-screen… (progress saved to session/)"
"${APP[@]}" educate --policy oracle \
  >"${OUT}/oracle-curve.json" \
  2>"${OUT}/oracle-progress.txt"
# Show only the concise epoch lines, not a live scroll flood.
while IFS= read -r line; do
  printf '  %s\n' "$line"
done <"${OUT}/oracle-progress.txt"
sleep 2

cmd "apprentice report"
"${APP[@]}" report | tee "${OUT}/published-result.txt"
outcome "${ORANGE}" "retrieval 44/44 at the epoch accuracy falls"

printf '\n'; rule
say "Receipts: docs/video/live/session/   Curve: eval/RESULTS.md"
rule; printf '\n'
sleep 2
