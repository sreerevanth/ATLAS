# Research threat model

ATLAS v0.1.0 is research software. The current local TIP demo uses a pre-shared
HMAC key, an ephemeral self-signed TLS certificate with client verification
disabled on loopback, public deterministic random-projection seed, and local
region indices. It demonstrates QUIC framing and Wasmtime execution; it is not
an authenticated multi-organization deployment.

## Assets and observations

Assets include raw records, embeddings, topology neighborhoods, region references,
module signing keys and execution results. A peer sees exchanged signatures,
query references, match/no-match responses, result vectors, message lengths,
timing and repeated outcomes. A local operator can inspect the entire node state.

The synthetic TIP sweeps measure threshold classification errors for one circle
family against an unrelated uniform-cloud family. They do not measure membership
inference, reconstruction, adaptive probing, or privacy leakage. The protocol
stores only a bounded nonce set by its query budget; persistence and key rotation
are not implemented. HMAC authenticates only parties sharing the key. Signatures
are lossy but are not confidential, and a public projection is not a secret.

Wasmtime receives copied local embeddings for the matched region. Modules have no
imports, WASI, filesystem, or network capabilities, have an Ed25519 signature
check, memory cap, and fuel budget. This is a prototype capability boundary;
the demonstration does not establish zero exfiltration against host/runtime
vulnerabilities, side channels, denial of service outside configured limits,
malicious signed code, key compromise, or deployment misconfiguration.

No differential privacy mechanism, neighboring relation, epsilon, or delta is
implemented. ATLAS makes no formal privacy, compliance, or production security
claim. Do not send sensitive data to the research demonstration.
