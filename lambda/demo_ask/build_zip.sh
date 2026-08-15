#!/usr/bin/env bash
# Build a Lambda deployment zip for the live ask endpoint.
# Usage: bash lambda/demo_ask/build_zip.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="$(mktemp -d)"
ZIP="$ROOT/lambda/demo_ask/demo_ask.zip"
trap 'rm -rf "$STAGE"' EXIT

python3.11 -m pip install \
  --quiet --target "$STAGE" \
  "psycopg[binary]>=3.1" "boto3>=1.34" "sqlglot>=25" "pydantic>=2"

# Library + warehouse SQL
mkdir -p "$STAGE/apprentice_crdb"
cp -R "$ROOT/src/apprentice_crdb/"* "$STAGE/apprentice_crdb/"

# Frozen exam (questions loaded only via agent_facing_items / run_exam)
mkdir -p "$STAGE/eval"
cp "$ROOT/eval/questions.json" "$ROOT/eval/labels.json" "$ROOT/eval/run_exam.py" "$STAGE/eval/"

# Handler at zip root
cp "$ROOT/lambda/demo_ask/handler.py" "$STAGE/handler.py"

# REPO_ROOT marker: paths.py walks up looking for pyproject / eval — plant a stub
printf '%s\n' '[project]' 'name = "apprentice-crdb-lambda"' >"$STAGE/pyproject.toml"

rm -f "$ZIP"
( cd "$STAGE" && zip -qr "$ZIP" . -x '*/__pycache__/*' '*.pyc' )
echo "Wrote $ZIP ($(du -h "$ZIP" | cut -f1))"
