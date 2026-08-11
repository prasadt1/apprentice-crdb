# Labor split

| Role | Owner |
|------|--------|
| Cluster, `ccloud`, MCP, Bedrock/S3 access, own-voice README/video | **Prasad** |
| Specs, scaffold, implementation, tests | **Cursor** |
| Frozen 50-question exam (protocol + labels) **before** any graded learning run; seam reviews; judge-eye positioning | **Claude** |

Hard rule: `eval/labels.json` is frozen before the agent is tuned against it. Results go in `eval/RESULTS.md` only.
