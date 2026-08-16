# Control-plane proof

![Apprentice — memory you can rewind](../video/youtube/thumbnail.png)

Receipts for the two AWS services the submission claims, plus the CockroachDB Cloud control plane. The cluster being on AWS satisfies “deployed on AWS”; I do **not** count it as an AWS service I built.

## AWS services

| Service | How it is used — not just that it is configured |
| --- | --- |
| **Amazon Bedrock** | Titan Text Embeddings V2 on write and query; Converse for generation (`amazon.nova-micro-v1:0`, disclosed replication arm `amazon.nova-lite-v1:0`). us-east-1. Graded exam arms and the hosted demo both call Bedrock. |
| **AWS Lambda** | Serverless agent execution for the [hosted live demo](https://prasadt1.github.io/apprentice-crdb/). A Function URL runs the full turn: Titan embed → `embedding <->` recall against the live cluster → Converse → execute on the prop warehouse → grade. Read-only SQL user, fixed question set, rate limit + daily cap, CORS locked to the Pages origin; degrades to the recorded run if unavailable. Deploy notes: [`lambda/demo_ask/README.md`](../../lambda/demo_ask/README.md). |

Architecture (four doors into the same memory — CLI, frozen exam, Cloud MCP, hosted Lambda demo):

![Architecture: four doors, CockroachDB memory plane, Bedrock + Lambda + SQLite edges](../media/architecture.png?v=4doors)

## Official CLI (preferred)

[`ccloud-cli.json`](ccloud-cli.json) is the output of the real `ccloud` binary:

```bash
./ccloud auth login
./ccloud cluster list -o json | tee docs/proof/ccloud-cli.json
```

Captured cluster: **solid-unicorn** · AWS · Basic · eu-central-1 · v26.2.5.

## Earlier Cloud API dump

[`ccloud.txt`](ccloud.txt) was captured via the Cockroach Cloud API / MCP (same control plane). Keep it as a secondary receipt; judges should prefer `ccloud-cli.json`.

Do not commit DSNs or SQL passwords.
