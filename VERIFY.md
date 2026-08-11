# Apprentice — verification checklist

Prasad. Day-1 / this week. Do not start graded education until `eval/FREEZE.md` exists.

- [ ] GitHub repo is `prasadt1/apprentice-crdb` (this tree), not `expunction-crdb`
- [ ] CockroachDB Cloud on **AWS** up; `APPRENTICE_CRDB_DSN` set
- [ ] `ccloud` can see the cluster (`ccloud cluster list`)
- [ ] Managed MCP connected (read-only OK)
- [ ] `apprentice migrate --try-vector-index` — paste the VECTOR INDEX line (ok or the real error)
- [ ] `apprentice gc-ttl` — live `gc.ttlseconds`; if the window is short, we compress education into hours and disclose it
- [ ] Bedrock model access in chosen region **or** stay on mock embedder + S3 for artifacts (AWS still cleared via S3)
- [ ] `pytest` green
- [ ] Claude: `eval/FREEZE.md` landed
