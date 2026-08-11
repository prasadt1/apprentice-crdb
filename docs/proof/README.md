# Control-plane proof

`ccloud.txt` is a Cloud API listing of the live Basic cluster (AWS, eu-central-1).
It is the same control plane `ccloud cluster list` talks to.

To stamp the official CLI output on this machine (needs a browser login):

```bash
# Homebrew (needs current Xcode CLT) or the published tarball:
# brew install cockroachdb/tap/ccloud
curl -fsSL https://binaries.cockroachdb.com/ccloud/ccloud_darwin-arm64_0.8.23.tar.gz | tar -xJ
./ccloud auth login
./ccloud cluster list -o json | tee docs/proof/ccloud-cli.json
```

Do not commit DSNs or SQL passwords.
