# Claims and evidence boundaries

Scientific status: **D — CENTRAL HYPOTHESIS NOT SUPPORTED**.

The tested ATLAS graph/topology retrieval formulations did not establish an
improvement over semantic retrieval. This is not a universal statement about
topology, other encoders, other scoring functions, or other retrieval settings.
The completed research sprint is closed; no new architecture search is implied.

| Claim | Status | Evidence / limitation |
|---|---|---|
| Controlled geometry-aware retrieval is implemented and executable | Supported within the recorded environment | `research/v2/evidence/final-results.json`, manifests and raw rankings |
| Tested graph/topology reranking improves held-out retrieval | Not established | HotpotQA and MuSiQue paired comparisons; no replicated improvement |
| The frozen primary V2 path uses cosine | Supported | `research/v2/evidence/frozen-config.json`, `research/v2/api.py` |
| Mathematical topology fixtures pass | Supported for those fixtures | `research/v2/evidence/topology-gate.json`; not proof of useful semantic topology |
| Landmark VR trades speed for topology fidelity | Measured on bounded samples | `research/v2/evidence/scaling-resource-corrected.json` |
| Original V2 launcher-only RSS is a valid memory measurement | Retracted | `research/v2/evidence/INCIDENTS.md`; use corrected process-tree measurements |
| HNSW is indistinguishable from exact search | Not established | Explicit query/neighborhood recall and retrieval changes in `diagnostics.json` |
| TIP matches local topology signatures | Local/synthetic prototype evidence only | Core tests, synthetic sweep and local QUIC integration |
| TIP provides differential privacy, zero knowledge or zero leakage | Unsupported | No DP mechanism/accounting or ZK proof system; threat model documents leakage channels |
| S-MCP executes signed, resource-bounded Wasm | Local prototype evidence only | Wasmtime implementation, tests and loopback smoke; not comprehensive security assurance |
| Structural anomaly experiments establish fraud detection | Unsupported | Synthetic graph construction only; no real-world fraud validation |
| ATLAS is production-ready or institutionally deployed | Unsupported | No operational deployment evidence |
| ATLAS is clinically validated or FDA/regulatory authorized | Unsupported | No clinical study or external authorization evidence |
| ATLAS has an independent security audit or post-quantum security | Unsupported | Neither is established by the executed research |
| Old paper drafts are peer-reviewed publications | Unsupported | Drafts retained as historical material; no publication or DOI asserted |
| This repository grants a particular software license | Not established | No repository-wide license file found; no license invented during cleanup |

## Interpretation limits

The held-out evaluations use internal splits of public development datasets and
pooled distractor contexts. They do not represent official hidden-test or fullwiki
leaderboard scores. The unsupervised corpus index is transductive. Pretrained
encoder exposure and semantic near-duplicate leakage remain possible. The
hostile leakage audit was performed by the same implementation operator, not an
independent external auditor. Confidence intervals are not equivalence proofs.

## Historical material

Phase labels, benchmark numbers in legacy drafts, and proposed clinical,
regulatory, cryptographic or federation features are not current capabilities.
See [the historical-material index](HISTORICAL_MATERIAL.md). Frozen reports are
preserved verbatim; interpret the V1 report as a dated execution snapshot and
the corrected V2 report as the latest retrieval evidence.
