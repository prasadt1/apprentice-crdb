#!/usr/bin/env bash
# Provision notes for CockroachDB Cloud (AWS). Prasad runs this.
# Requires: ccloud authenticated. Does not invent cluster IDs.
set -euo pipefail

echo "1. Create or select a CockroachDB Cloud cluster on AWS (Basic/serverless is fine)."
echo "   ccloud cluster list"
echo "2. Copy the SQL connection string into APPRENTICE_CRDB_DSN."
echo "3. From the Cloud console: cluster → MCP → paste snippet into Cursor/Claude (read-only OK)."
echo "4. Then:"
echo "   apprentice migrate --try-vector-index"
echo "   apprentice gc-ttl"
echo
echo "Do not claim C-SPANN or a custom gc.ttlseconds until those two commands print live truth."
