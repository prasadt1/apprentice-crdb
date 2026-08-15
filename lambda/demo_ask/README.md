# Deploy — live ask Lambda

Spec: [`docs/CURSOR-LIVE-DEMO-SPEC.md`](../../docs/CURSOR-LIVE-DEMO-SPEC.md).

## One-time AWS setup

1. **Read-only CRDB user** (Cloud SQL console):

```sql
CREATE USER demo_ask WITH PASSWORD '...';
GRANT SELECT ON TABLE semantic_rules TO demo_ask;
-- no INSERT/UPDATE/DELETE
```

DSN into Lambda env as `APPRENTICE_CRDB_DSN` (verify-full SSL).

2. **IAM role** for the function — only:

```json
{
  "Effect": "Allow",
  "Action": ["bedrock:InvokeModel"],
  "Resource": [
    "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0",
    "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
  ]
}
```

3. **Build zip**

```bash
bash lambda/demo_ask/build_zip.sh
```

4. **Create function** (console or CLI): Python 3.11 · handler `handler.handler` · timeout **25s** · memory **512 MB** · env:

| Key | Value |
|---|---|
| `APPRENTICE_CRDB_DSN` | read-only DSN |
| `APPRENTICE_GEN_MODEL` | `amazon.nova-lite-v1:0` |
| `APPRENTICE_GENERATOR` | `bedrock` |
| `APPRENTICE_EMBEDDER` | `bedrock` |
| `AWS_REGION` / region | `us-east-1` |

5. **Function URL** — auth `NONE`. CORS:

- Allow origin: `https://prasadt1.github.io`
- Allow methods: `POST`, `OPTIONS`
- Allow headers: `content-type`

6. **Wire Pages** — in `docs/index.html`, one line:

```js
const API = "https://xxxxxxxx.lambda-url.us-east-1.on.aws/";
```

Commit + push so GitHub Pages picks it up. Until then, `API = ""` forces the recorded degradation path (already works).

## Smoke

```bash
curl -sS -X POST "$API" \
  -H 'content-type: application/json' \
  -d '{"question_id":"q02","mode":"no_memory"}' | jq .verdict,.rows

curl -sS -X POST "$API" \
  -H 'content-type: application/json' \
  -d '{"question_id":"q02","mode":"with_memory"}' | jq .verdict,.rows,.retrieved
```

Expect: cold → wrong / `[[20000]]`; with memory → correct / `[[95000]]` and non-empty `retrieved` (needs live rules in the cluster from a prior `teach` / `educate`).

## Acceptance greps

```bash
# generation path must not mention fixture leakage columns
rg -n 'gold_sql|naive_sql|bait_sql|house_rules' lambda/demo_ask/handler.py
# should be empty
```
