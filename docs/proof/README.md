# Control-plane proof

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
