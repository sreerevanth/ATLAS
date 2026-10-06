# Implementation audit

Baseline: `c8bf38a`. Audit begun 2026-10-06. Historical claims are not release evidence.
No architecture changes preceded this initial audit. Status is based on source inspection;
execution status below is deliberately separate. The repository has no AGENTS.md.

## Source availability and precedence

Neither `ATLAS_PROMPT_BOOK.pdf` nor `ATLAS.pdf` exists in this checkout.
Available substitutes are `ATLAS_PROMPT_BOOK.md` and
`ATLAS_TECHNICAL_README (1).md`; equivalence to missing PDFs is unverified.
The corrected local-neighborhood TIP and sandbox requirements take precedence
over MASTER_PLAN's conflicting global-signature/HTTP and deleted-sandbox roadmap.
The technical specification itself overstates hash non-invertibility: lossiness
does not establish confidentiality. Core principles are objectives, not guarantees.

## Baseline evidence matrix (commit `c8bf38a`)

| Requirement | Baseline status | Source files | Baseline tests | Executed during baseline audit? | Evidence artifact | Baseline gap |
|---|---|---|---|---|---|---|
| Public corpus / preprocessing / text embeddings | STUB | `month1_accelerator.py` generates random arrays | None | No | None | Script public data, exclusions, pinned encoder |
| Exact / ANN baseline | PARTIAL, UNTESTED | `month1_accelerator.py`, `atlas-core/benchmark_sota.py` | None | No | None | Real corpus, sweep, quantiles, serialization |
| Persistent homology | IMPLEMENTED, UNTESTED mathematically | `atlas-experiments/EXP-001/topology.py`, `atlas-core/simulate_real_world.py` | `test_tda_mathematics` tests shape/nonzero, not expected topology | No | None | Circle/cluster gates |
| Sparse/witness topology | UNSUPPORTED CLAIM | `month1_accelerator.py` caps filtration radius; this is not a sparse approximation | None | No | None | Exact overlap, established approximation, native RSS |
| Potential traversal | STUB | No implementation in package topology initializer | None | No | None | Define potential, paths and ablations |
| External multi-hop retrieval | UNSUPPORTED CLAIM | README tables only | None | No | None | HotpotQA or MuSiQue controlled experiment |
| Structural anomaly | UNSUPPORTED CLAIM | README only | None | No | None | Relational benchmark and baselines |
| Landscape / image representation | PARTIAL | EXP-001/002/003 representations | None | No | Historical markdown only | Shared fixed grid; independent validation |
| Local TIP | OBSOLETE, PARTIAL | `atlas-core/atlas/protocol/message.py`, `atlas_server.py` advertise dataset signatures | JSON / API tests | No | None | Query-local topology, region references, state |
| QUIC | STUB | FastAPI HTTP implementation only | None | No | None | Real transport and local nodes |
| LSH | IMPLEMENTED, UNTESTED accuracy | `atlas-core/atlas/hashing/lsh.py` | Determinism test on duplicate implementation | No | None | Confusion matrices and parameter sweeps |
| Privacy layer | PARTIAL, UNSUPPORTED CLAIM | `atlas-core/train_lpl.py`, `atlas/privacy/lpl.py` | None | No | Unproven tracked weights | Disjoint source records, held-out attackers |
| Repeated query privacy / DP | UNSUPPORTED CLAIM | EXP-007/011, SPEC-001 | None | No | Unverified reports | Explicit threat model; no epsilon claim |
| S-MCP | SIMULATED, PARTIAL | `month1_accelerator.py` Wasmtime loop; `secure_enclave.py`, `advanced_enclave.py` Python monkey patches | No sandbox regression tests | No | None | Signed modules, scoped inputs, Wasmtime limits |
| Authentication | PARTIAL, BROKEN | `atlas_server.py` hardcoded shared API key | API tests accept public key | No | None | Configured credentials, message validation |
| SQLite state | IMPLEMENTED, UNTESTED | `atlas_server.py` import creates relative DB | Test deletes relative DB | No | Tracked `atlas_node.db` is generated state | Isolate test storage; untrack DB |
| Integrated deployment | SIMULATED | `simulate_network.py`, `simulate_real_world.py`, client/server | No full pipeline test | No | None | Actual matching to constrained execution |
| Packaging / reproducibility | PARTIAL | `atlas-core/pyproject.toml`, setup.py | None | No | None | Clean environment, root CLI, lock, CI |
| Production / pilots / security review / FDA / PQ / ZK | UNSUPPORTED CLAIM / STUB | README, specs/Phase12-19, report generators | None | No | None | Retract claims; not release capabilities |

## Material findings

1. README openly labels figures illustrative yet also says measured, production,
   peer-reviewed, two pilots, and passed audit. No supporting raw run lineage exists.
2. `benchmark_sota.py` sets privacy leakage to zero, sleeps to simulate a ZK
   verifier and uses random projection as a lattice proxy. Its concluding claim
   is printed regardless of measurements. None is valid security evidence.
3. `generate_report.py` contains a hard-coded zero-leakage proof that omits
   information in the gate outcome. The other report generators embed results
   and peer-review language without review provenance.
4. `month1_accelerator.py` calls flattened intervals a mock landscape, then
   describes the synthetic output as non-synthetic and declares all deliverables
   met without assertions. `tracemalloc` is not native-library peak RSS.
5. EXP-002/003 and EXP-007 tradeoff refit representation grids separately on
   compared diagrams. Coordinate positions then need not mean the same thing.
   EXP-003 silently drops invalid configurations and reports only the winner.
6. EXP-007/011 sum marginal bit mutual information. This is not joint hash MI
   and is not a differential privacy guarantee. Hash agreement is not retrieval
   accuracy. Existing reports and both paper drafts cannot support public claims.
7. LPL training splits overlapping sampled neighborhoods after fitting a scaler
   to all records. Source patients may occur on both sides. A weak adversary near
   chance does not establish privacy. Missing weights silently use random weights.
8. Server compares user-controlled commitment strings, not proofs; zip-based
   Hamming ignores unequal suffixes and divides by a fixed length. Dashboard
   interpolates unescaped names. No replay protection or per-region authorization.
9. Python socket/open monkey patches do not isolate native calls or subprocesses.
   Opcode tracing cannot bound time inside C calls. Crash/timeout counted as
   blocked attacks in `benchmark_sandbox.py` does not prove correct enforcement.
10. Tracked bytecode, database and model lack reproducible evidence manifests.
    There is no bibliography file for either paper's `references` citation target.

## Historical material policy

All pre-audit reports, papers, phase labels, scores, model weights and benchmarks
are quarantined as historical, unverified material. Retention preserves forensic
history, not endorsement. New release evidence must include command, source
fingerprints, dependency versions, seed, raw observations and analysis.
No production, privacy, clinical, cryptographic or superiority claim is approved.

## Execution update

The new `src/atlas` implementation was added after the baseline audit. This
supersedes the baseline execution cells above for those components only.

| Requirement | Current status | Executed/tested | Evidence |
|---|---|---|---|
| HotpotQA acquisition, cleaning, text embeddings | IMPLEMENTED, EXECUTED | Pinned validation subset and encoder; clean env | `artifacts/local/research/data_quality.json`; `embedding_metadata.json` |
| Circle/noisy-circle/two-cluster persistence gates | IMPLEMENTED, TESTED, PASS | `pytest`; CLI `validate` | `artifacts/local/validate/topology_gate.json` |
| Exact-vs-HNSW ANN sweeps | IMPLEMENTED, EXECUTED | 24 configurations, exact cosine reference, 300 queries | `artifacts/local/research/ann.json` |
| Exact-vs-greedy-landmark topology scaling | PARTIAL, EXECUTED | Exact overlap to 1k, landmark to 10k; distances expose material H0/H1 loss; essential H0 JSON bug found and fixed | `artifacts/local/research/scaling.json`; `scaling.png` |
| Cosine vs graph/topology multi-hop retrieval | IMPLEMENTED, EXECUTED; NO-GO | 300 paired sampled HotpotQA questions; ATLAS all-support@5 delta -0.0100, bootstrap 95% CI [-0.0267, 0.0033] | `artifacts/local/research/retrieval.json` |
| TIP signature error rates | IMPLEMENTED, EXECUTED | Synthetic circle/uniform-cloud pair sweep | `artifacts/local/tip/tip.json` |
| Signed Wasm region-input bounds | IMPLEMENTED, TESTED | Fuel, memory, import, signature tests | `tests/test_protocol.py` |
| Two-node TIP/S-MCP over QUIC | IMPLEMENTED, EXECUTED | Synthetic loopback OFFER/MATCH/EXECUTE/RESULT | `artifacts/local/integration/integration.json` |
| Relational structural anomaly | IMPLEMENTED, EXECUTED | Synthetic graph vs independent random-feature control | `artifacts/local/anomaly/anomaly.json` |
| Clean Python 3.12 environment | IMPLEMENTED, EXECUTED | Fresh `.venv-release` lock install; pytest and Ruff pass | `requirements-lock.txt`; 12 tests pass |

## Prompt Book phase mapping

Prompt Book numbering is authoritative for implementation status. `MASTER_PLAN.md`
and `specs/Phase12...Phase19` reuse conflicting phase numbers and are mapped below
separately; their labels must not be read as completion gates.

| Prompt Book phases | Status after new implementation | Evidence / limitation |
|---|---|---|
| 1: corpus and embeddings | IMPLEMENTED, EXECUTED | Pinned HotpotQA subset and encoder; 256-token truncation disclosed |
| 2: exact and approximate neighbors | IMPLEMENTED, EXECUTED | 300-query exact cosine vs HNSW sweep; no 50k dataset evidence |
| 3: persistence correctness | IMPLEMENTED, TESTED | Circle, noisy-circle and two-cluster fixtures pass |
| 4: sparsification | PARTIAL, EXECUTED | Greedy landmarks through 10k; not witness; exact overlap only to 1k and material diagram/lifetime errors |
| 5: potential traversal | PARTIAL, TESTED | Five synthetic source-bridge-answer chains pass with density potential and title diversification |
| 6: external retrieval comparison | IMPLEMENTED, EXECUTED; NO-GO | Paired sampled HotpotQA distractor result does not improve on cosine; shared-document dependence is not addressed by question bootstrap |
| 7: distillation | STUB / UNSUPPORTED | No teacher/student held-out model study |
| 8: quantization and Wasm model | STUB / UNSUPPORTED | Demo is a signed byte-summing WAT module, not a distilled inference model |
| 9: sandbox runtime | PARTIAL, TESTED | Wasmtime fuel/memory/import/signature limits tested; no independent review |
| 10: scoped data access | PARTIAL, TESTED | Matched local embedding rows are copied into module memory; no original-record interface |
| 11: attestation and demo | PARTIAL, EXECUTED | Ed25519 module signature and loopback demo; no remote attestation or authenticated peer identity |
| 12: local persistence and landscape | PARTIAL, TESTED | Fixed-grid landscape exists; protocol regions are in-memory, not persistent |
| 13: LSH | IMPLEMENTED, EXECUTED | Empirical synthetic threshold/noise sweep; no privacy guarantee |
| 14: protocol schema | PARTIAL, TESTED | Canonical JSON, HMAC, basic validation/replay checks; shared-secret research protocol |
| 15: QUIC | PARTIAL, EXECUTED | Real aioquic loopback streams; certificate verification disabled in demo |
| 16: multi-node environment | PARTIAL | Two logical nodes in a local process/loopback setup; no independent deployment |
| 17: full end-to-end and failure handling | PARTIAL, EXECUTED | OFFER/MATCH/EXECUTE/RESULT and unit failure cases; not production operations |
| 18-21: design partner, real-data adaptation, benchmark, scenario | UNSUPPORTED | No partners, private data, real deployments or pilots |
| 22: threat model | PARTIAL, DOCUMENTED | `docs/THREAT_MODEL.md` covers principal observations; no formal verification |
| 23: differential privacy | UNSUPPORTED | No DP mechanism, accountant, epsilon or delta |
| 24: red-team suite | PARTIAL | Wasm tests cover fuel, memory, imports and signatures; broad attack suite absent |
| 25: external security audit | UNSUPPORTED | No review was conducted |
| 26: compliance package | UNSUPPORTED | No certification or compliance evidence |
| 27: scale profile | PARTIAL, EXECUTED | Exact overlap through 1k, landmark runs through 10k; resource/error limits apply |
| 28-31: incremental update, tenancy, observability, cost | UNSUPPORTED / PARTIAL | No incremental or tenant isolation; basic logs only; no cost model |
| 32: API/SDK | PARTIAL, EXECUTED | Installable research package and CLI; no public release |
| 33-40: deploy, onboarding, support, commercial and SLA | UNSUPPORTED | No deployments, customers, contracts or operations |
| 41-50: expansion and continual review | UNSUPPORTED | Proposal text only |

The separate Master Plan/spec phase labels for production hardening, consortium,
clinical pilot, post-quantum security, ZK, regulatory/FDA, global federation,
hardware acceleration and final ADR remain UNSUPPORTED. The synthetic anomaly
experiment is an added research result and does not satisfy a real-data pilot.

The synthetic anomaly run achieved AUROC 0.8005 and AUPRC 0.1582 for local
clustering versus 0.4876 and 0.0704 for a random-feature control; threshold
precision was 0.1582 at recall 1.0. This weak precision is a material failure
mode, not evidence of field performance. The current sampled retrieval experiment
is NO-GO: ATLAS change in all-support@5 vs cosine was -0.0100 with a question-
bootstrap 95% interval [-0.0267, 0.0033]. Material embedding, anomaly and TIP
limitations remain as documented in the research report.
