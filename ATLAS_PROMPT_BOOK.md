# ATLAS — Prompt Book

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](docs/HISTORICAL_MATERIAL.md).
### Full Detailed Prompts, Every Phase, Groups A–I

Confidential — internal build document. Just the prompts, full length, no checklists or commentary. Hand the relevant block directly to whichever coding agent or engineer owns that phase.

---

# GROUP A — Manifold Core Foundation

## Phase 1 — Data Pipeline & Embedding Layer

```
You are building the data ingestion and embedding layer for ATLAS's Manifold-Core component.

GOAL: Stand up a clean, reproducible pipeline that ingests a text corpus and
produces high-quality, well-documented embeddings that every later phase in
Group A will depend on. Treat this as foundational infrastructure, not a
throwaway script — bugs introduced here will silently propagate into every
downstream phase.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Corpus acquisition
   - Acquire a text corpus of 10,000-50,000 documents. Use a publicly
     available, named source (a Wikipedia dump subset or an ArXiv abstracts
     dataset) rather than a scraped or ad hoc collection, so results are
     reproducible and comparable to prior published work.
   - Store the raw corpus in an immutable, versioned location (e.g., a
     dated snapshot on disk) so later phases can always re-derive from the
     exact same starting point.

2. Preprocessing and cleaning
   - Normalize text encoding (UTF-8 throughout), strip markup/boilerplate
     specific to the source format, and deduplicate near-identical
     documents using a content hash or shingling method.
   - Produce a data-quality report covering: total document count before
     and after cleaning, duplicate count and examples, encoding-error
     count and examples, and an empty/near-empty document count.

3. Embedding generation
   - Use an existing, well-established open embedding model (e.g. a
     sentence-transformers model). Do not train or fine-tune a new encoder
     at this stage — the goal is a clean pipeline, not a novel embedding
     method.
   - Batch the embedding process efficiently, log throughput (documents
     per second) and total wall-clock time, and store embeddings alongside
     their source document IDs and metadata in a queryable columnar format
     (e.g. Parquet).

4. Reproducibility verification
   - Re-run the embedding step on a fixed subsample twice, independently,
     and confirm the outputs are bit-for-bit or numerically identical
     within floating-point tolerance. Document the exact model version,
     library versions, and hardware used.

5. Basic query interface
   - Build a minimal API or script that, given a document ID or raw text,
     returns its embedding and metadata — this will be the integration
     point for Phase 2's neighborhood graph work.

CONSTRAINTS:
- Every step must be scripted and re-runnable from raw corpus to final
  embeddings with a single command — no manual, undocumented steps.
- Do not silently drop problematic documents; log every exclusion with a
  reason.
- Do not proceed to embedding generation until the data-quality report has
  been reviewed and any blocking issues addressed.

DELIVERABLE: A versioned repo containing the ingestion and embedding
pipeline, the data-quality report, the reproducibility verification
results, and a README with exact reproduction steps and the hardware/
library versions used.
```

---

## Phase 2 — Neighborhood Graph Construction

```
You are building the approximate nearest-neighbor graph layer for ATLAS's
Manifold-Core, on top of the Phase 1 embedding pipeline.

GOAL: Produce a fast, accurate approximate k-nearest-neighbor graph over
the full embedding set, with measured accuracy against an exact baseline,
since every later topology computation in Group A depends on this graph
being both fast enough to use and accurate enough to trust.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Exact k-NN baseline (small scale only)
   - On a subsample of 1,000-2,000 embeddings from Phase 1, compute exact
     k-nearest-neighbors (brute-force cosine or Euclidean distance,
     whichever the embedding model was trained/optimized for) for a fixed
     k (e.g. k=15). This is the ground truth you'll measure approximate
     methods against — do not skip this step even though it doesn't scale.

2. Approximate graph construction
   - Using an established library (hnswlib, faiss-HNSW, or equivalent),
     build an approximate k-NN graph over the full 10k-50k embedding set
     from Phase 1.
   - Expose and tune the key parameters (e.g. M, ef_construction, ef_search
     for HNSW) and document what values you land on and why.

3. Accuracy benchmarking
   - On the same 1,000-2,000 point subsample used for the exact baseline,
     compute the approximate graph's neighbors and measure recall@k against
     the exact baseline (what fraction of true nearest neighbors does the
     approximate method actually find?).
   - Report this recall number explicitly — do not simply assert the
     approximate method is "good enough" without the measurement.

4. Performance benchmarking
   - Measure and report: graph construction time (wall-clock) at full
     corpus scale, memory footprint of the constructed graph, and query
     latency (time to retrieve k neighbors for a single new query point)
     at both p50 and p99.

5. Query API
   - Build a simple API that, given an embedding vector, returns its k
     approximate nearest neighbors with distances, for use by Phase 3
     onward.

CONSTRAINTS:
- Recall accuracy must be measured against a real exact baseline, not
  estimated or assumed from library documentation claims.
- If recall falls below a level you consider acceptable for the topology
  work downstream, document this explicitly rather than silently
  proceeding — it may mean revisiting graph parameters before Phase 3.
- Graph must be persistable to disk and reloadable without rebuilding from
  scratch every run.

DELIVERABLE: A repo with the graph construction pipeline, the exact-vs-
approximate recall benchmark results, the performance benchmark numbers,
and a query API ready for Phase 3's topology computation to consume.
```

---

## Phase 3 — Vietoris–Rips Filtration (Small Scale)

```
You are building the core topological computation for ATLAS's Manifold-
Core: constructing a Vietoris-Rips filtration and extracting persistent
homology, validated on a small scale before any optimization work begins.

GOAL: Get an exact, correct persistent-homology computation working and
validated against known ground truth, so every later optimization
(sparsification, incremental updates) has a trustworthy baseline to be
checked against.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Library selection and integration
   - Integrate an established, peer-reviewed persistent homology library
     (GUDHI or Ripser, via their Python bindings) into the pipeline. Do
     not implement persistence computation from scratch — this is a
     mathematically subtle area where using a tested library is the
     responsible choice.

2. Small-scale filtration
   - On a 500-1,000 point subsample of the Phase 1 embeddings, construct a
     Vietoris-Rips filtration: a sequence of simplicial complexes built at
     increasing distance thresholds (epsilon values).
   - Compute persistent homology across this filtration for dimensions H0
     (connected components) and H1 (loops) at minimum; H2 (voids) if
     computationally feasible at this small scale.

3. Ground-truth validation
   - Before trusting the pipeline on real data, run it against at least
     two synthetic point clouds with known topology: (a) a circle of
     points, which should show exactly one persistent H1 feature, and
     (b) two well-separated clusters, which should show exactly two
     persistent H0 features (connected components). Confirm the pipeline
     produces exactly these expected results.
   - Only after both synthetic validations pass exactly as expected,
     proceed to running the pipeline on the real embedding subsample.

4. Output format and persistence diagrams
   - Store the resulting persistence diagrams (birth/death interval pairs
     per homology dimension) in a documented, structured format that later
     phases (sparsification, landscape transforms) can consume directly.
   - Generate a simple visualization (persistence diagram plot or barcode
     plot) for manual inspection of the real-data results.

5. Compute-cost baseline
   - Log wall-clock time and peak memory usage for the filtration and
     persistence computation at this small scale. This becomes the
     baseline that Phase 4's sparsification work will be measured against.

CONSTRAINTS:
- Do not proceed past the ground-truth validation step until both
  synthetic test cases produce exactly the expected topological features
  — a subtle bug here will silently corrupt every downstream phase's
  results.
- Document the exact library versions used, since persistent homology
  library APIs and default behaviors can vary meaningfully between
  versions.

DELIVERABLE: A repo with the filtration and persistence computation
pipeline, the two synthetic ground-truth validation results (with plots),
the real-data persistence diagram output and visualization, and the
compute-cost baseline numbers.
```

---

## Phase 4 — Sparsification

```
You are building the sparsification layer that makes ATLAS's Manifold-Core
topology computation tractable at real corpus scale, building directly on
Phase 3's validated small-scale pipeline.

GOAL: Make persistent homology computation feasible at 10,000-50,000
points without losing the topological features that actually matter,
and prove this with a direct, measured comparison against the exact
computation from Phase 3 wherever exact computation is still feasible.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Sparsification method implementation
   - Implement a witness-complex construction (or a comparable, published
     sparsification approach — e.g. a sparse Rips approximation with a
     bounded approximation factor). Use an established method with known
     theoretical guarantees rather than an ad hoc heuristic.
   - Integrate this as a preprocessing step before the Phase 3 persistence
     computation pipeline, so the rest of that pipeline can be reused
     largely unchanged.

2. Correctness comparison at overlapping scale
   - At a scale where exact Vietoris-Rips computation from Phase 3 is
     still feasible (e.g. 1,000-2,000 points), run both the exact and the
     sparsified pipeline on the same data and directly compare the
     resulting persistence diagrams.
   - Report which topological features are preserved, which are lost, and
     which spurious features (if any) are introduced by sparsification.
     This comparison is the core deliverable of this phase — do not skip
     or shortcut it.

3. Scale-up testing
   - Run the sparsified pipeline at 10,000 and then 50,000 points from the
     Phase 1 corpus. Log wall-clock time, peak memory, and simplex count
     at each scale, compared against the Phase 3 baseline extrapolated (or
     directly measured, if feasible) at the same scale.

4. Parameter sensitivity
   - Test at least three different sparsification parameter settings
     (e.g. different witness-set sizes or approximation factors) and
     report how the accuracy/performance tradeoff shifts across them,
     so the eventual production setting is chosen from evidence rather
     than a single untested guess.

5. Output compatibility
   - Confirm the sparsified pipeline's output format is identical to
     Phase 3's, so downstream phases (query traversal, landscape
     transforms) require no changes to consume it.

CONSTRAINTS:
- Do not report "sparsification works" without the direct overlapping-
  scale comparison against exact computation — a performance win that
  silently discards the topological features you actually need is not a
  win.
- If no sparsification parameter setting preserves the topology
  adequately at target scale within a feasible compute budget, report
  this honestly as an open problem rather than picking whichever setting
  runs fastest.

DELIVERABLE: A repo with the sparsification implementation, the exact-vs-
sparsified comparison results at overlapping scale, the 10k/50k scale-up
performance numbers, and the parameter sensitivity analysis.
```

---

## Phase 5 — Potential-Field Query Traversal

```
You are building the core retrieval mechanism for ATLAS's Manifold-Core:
resolving a query via traversal across a potential field defined over the
topological structure, replacing simple nearest-neighbor lookup.

GOAL: Implement and validate that queries can be resolved by traversing
the manifold's structure — surfacing multi-hop, chained relationships
that a pointwise similarity search structurally cannot represent — and
prove this works on hand-crafted test cases before any external
benchmarking begins.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Potential field definition
   - Define a scalar potential field over the manifold using two inputs:
     local point density (from the Phase 2 neighborhood graph) and
     persistence weight (from the Phase 3/4 persistence diagrams — more
     persistent features contribute a stronger "gravity well").
   - Document the exact mathematical formulation used, including how the
     two inputs are combined and weighted, so it can be tuned and
     reasoned about later.

2. Query insertion
   - Implement inserting a new query embedding into the existing indexed
     structure: locate its position relative to the existing k-NN graph
     and persistence structure without requiring a full reindex.

3. Traversal algorithm
   - Implement resolving a query via a traversal process across the
     potential field (conceptually similar to gradient descent, but
     respecting the manifold's actual connectivity rather than assuming a
     simple continuous space) — the query should be able to pass through
     multiple gravity wells in sequence, producing a path rather than a
     single nearest point.
   - Make the resulting traversal path inspectable and loggable (each
     step, its potential value, and why the traversal moved there) —
     this must not be a black box, since debugging and validating it
     depends entirely on being able to see the path it took.

4. Hand-crafted multi-hop validation
   - Before running any external benchmark, write five multi-hop test
     queries where you know the correct answer requires chaining
     information across two or three specific documents in the corpus
     (verify this manually yourself first). Confirm the traversal
     mechanism actually retrieves the correct chain for all five, and
     document any that fail along with a hypothesis for why.

5. Latency measurement
   - Measure and report query latency (time from query embedding to
     resolved traversal path) at the target corpus scale (10k-50k
     documents, using the Phase 4 sparsified index).

CONSTRAINTS:
- Do not treat this phase as complete based on the traversal "running
  without errors" — it must correctly resolve the hand-crafted multi-hop
  test cases, which are the actual bar for this mechanism doing what it's
  supposed to do.
- If fewer than all five hand-crafted test cases pass, do not proceed to
  Phase 6's external benchmark until you understand why, since a flawed
  traversal mechanism will produce misleading benchmark results either
  way.

DELIVERABLE: A repo with the potential-field and traversal implementation,
the five hand-crafted multi-hop test cases and their pass/fail results
with explanations, the inspectable traversal-path logging, and the
latency measurements at target scale.
```

---

## Phase 6 — Benchmark vs. Cosine-Similarity RAG

```
You are running the single most important evaluation in the entire
Manifold-Core workstream: a direct, honest comparison between the Phase
1-5 traversal-based retrieval system and standard cosine-similarity RAG,
on a named external benchmark.

GOAL: Produce a rigorous, reproducible, honestly-reported comparison that
will determine whether the rest of the ATLAS roadmap proceeds as scoped.
This phase's result is a genuine go/no-go gate, not a formality.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Cosine-similarity RAG baseline
   - Using the exact same Phase 1 embeddings (so the comparison isolates
     the retrieval mechanism, not the embedding quality), implement a
     standard cosine-similarity nearest-neighbor RAG retriever as the
     baseline.

2. External benchmark selection and integration
   - Select a named, established external multi-hop question-answering
     benchmark (HotpotQA or a MuSiQue-style multi-document QA dataset).
     Do not construct a custom evaluation set for this comparison — the
     credibility of this result depends entirely on it being measured
     against a benchmark the field already recognizes.
   - Map the benchmark's document corpus and questions into the same
     pipeline used for Phase 1-5, so both systems are evaluated on
     identical underlying data.

3. Side-by-side evaluation
   - Run both the cosine-similarity baseline and the Phase 5 traversal
     system against the full benchmark question set.
   - Report retrieval accuracy (using the benchmark's standard metric),
     end-to-end query latency, and compute cost per query for both
     systems, side by side in a single table.

4. Error analysis
   - For a sample of questions where the two systems disagree, manually
     review and categorize why: does the traversal system correctly solve
     multi-hop cases the baseline misses, or does it introduce different
     kinds of errors of its own? Report both directions honestly.

5. Full, honest reporting
   - Write up the complete result, including any categories of questions
     where cosine-similarity RAG performs better, any cases where the
     traversal system's advantage doesn't hold, and the actual measured
     accuracy delta with a stated margin, not a rounded-up or best-case
     framing of it.

CONSTRAINTS:
- Every reported number must come from an actual run against the named
  external benchmark — no estimated, extrapolated, or "expected" figures
  standing in for a real measurement.
- Report negative or mixed results with the same clarity as positive
  ones; the credibility of every phase that follows depends on this one
  being trustworthy.

DELIVERABLE: A repo with both retrieval systems, the full benchmark
evaluation harness, the side-by-side results table, the error analysis,
and a written report stating plainly whether the traversal approach beat
the baseline, by how much, and where it didn't.
```

---

# GROUP B — Sovereign-MCP Runtime

## Phase 7 — Distillation Pipeline

```
You are building the model distillation pipeline that produces the small,
task-specific inference modules ATLAS's Sovereign-MCP execution model
depends on.

GOAL: Produce a small "student" model that retains as much of a larger
"teacher" model's task-specific accuracy as possible, with the accuracy
retention measured and reported honestly, since this number determines
whether the entire Sovereign-MCP execution model is viable.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Task definition
   - Select one narrow, well-defined task appropriate for a distilled,
     sandboxed inference module — for example, a binary anomaly/fraud
     classifier on structured transaction-style data, or an entity-
     linkage scorer. The task must be narrow enough that a small model can
     plausibly do it well; do not select an open-ended generation or
     reasoning task for this first module.

2. Teacher model training
   - Train (or fine-tune an existing pretrained model into) a larger
     "teacher" model on this task, using a properly held-out test set that
     will not be touched again until final evaluation.

3. Student model distillation
   - Design a small "student" model architecture appropriate for later
     Wasm compilation (favor simple architectures — small MLPs, small
     CNNs, or lightweight transformer variants — over anything with
     exotic operations that may not have mature Wasm-compilation support).
   - Train the student via standard knowledge distillation from the
     teacher (matching the teacher's output distribution/soft labels, not
     just hard labels), on the same training data split used for the
     teacher.

4. Accuracy retention measurement
   - Evaluate both the teacher and the student on the same held-out test
     set. Report both accuracy numbers explicitly and calculate the
     student's retention as a percentage of the teacher's performance.
   - If retention is poor, do not simply report a lower number and move
     on — investigate whether the student architecture, distillation
     method, or training data size is the limiting factor, and document
     what you tried.

5. Model characterization
   - Document the student model's parameter count, on-disk size (before
     quantization), and inference latency on standard (non-Wasm) hardware,
     as the baseline Phase 8's quantization and compilation work will be
     measured against.

CONSTRAINTS:
- The held-out test set must genuinely never be used in training or
  hyperparameter tuning for either the teacher or student — a leaked test
  set invalidates every accuracy number in this phase.
- Report the actual retention percentage plainly, even if it is
  disappointing; this number is a hard input to whether Sovereign-MCP is
  viable at all.

DELIVERABLE: A repo with the teacher and student training pipelines, the
held-out test set (clearly separated from training data), the accuracy
retention report, and the student model characterization numbers.
```

---

## Phase 8 — Quantization & Wasm Compilation

```
You are taking the Phase 7 distilled student model and making it run
inside a WebAssembly sandbox — the execution environment Sovereign-MCP
depends on.

GOAL: Prove a small, distilled model can be quantized and compiled to
run correctly inside a wasm32-wasi target, with output verified to match
native inference within a stated, measured tolerance.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Quantization
   - Quantize the Phase 7 student model to int8 precision using a
     standard, established quantization toolchain (post-training
     quantization to start; quantization-aware training only if
     post-training quantization causes unacceptable accuracy loss).
   - Measure accuracy on the same held-out test set from Phase 7 after
     quantization, and report the additional accuracy change caused by
     quantization specifically (separate from the distillation loss
     already measured in Phase 7).

2. Wasm compilation
   - Compile the quantized model to a wasm32-wasi target using an
     established path (tract or wonnx, or an equivalent maintained
     ONNX-to-Wasm toolchain). Do not attempt to compile a large,
     general-purpose model — this must remain the small, task-specific
     student model only.
   - Resolve and document any operator-compatibility issues encountered
     during compilation (some model operations may not have mature Wasm
     support and may require architecture adjustments).

3. Output equivalence verification
   - Run a fresh test batch (not previously used in Phase 7's test set,
     to avoid any risk of the compilation process being implicitly tuned
     to it) through both the native (non-Wasm) quantized model and the
     compiled Wasm module.
   - Measure and report the numerical difference between the two outputs,
     establishing a concrete tolerance value rather than an assumed "close
     enough."

4. Performance characterization
   - Measure and report: compiled Wasm module size on disk, inference
     latency inside a Wasm runtime (outside the full sandbox for now —
     that's Phase 9), and memory footprint during inference.

CONSTRAINTS:
- The output-equivalence test batch must be genuinely fresh, not reused
  from earlier test sets, to avoid any risk of unintentionally tuning the
  compilation process to a specific evaluation set.
- Do not proceed to Phase 9's sandbox work until output equivalence is
  verified within a documented, acceptable tolerance — a compilation bug
  here would silently corrupt every later phase's results.

DELIVERABLE: A repo with the quantization pipeline, the compiled Wasm
module, the output-equivalence verification results and stated tolerance,
and the performance characterization numbers.
```

---

## Phase 9 — Sandbox Runtime & Resource Capping

```
You are building the actual security boundary for ATLAS's Sovereign-MCP
execution model: a Wasmtime-based sandbox with hard resource limits.

GOAL: Build a sandbox that runs the Phase 8 compiled module correctly
under normal conditions, but safely halts any module — malicious or
buggy — that attempts to exceed defined memory or compute limits, and
prove this with a deliberately adversarial test.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Basic sandbox setup
   - Stand up a Wasmtime-based host runtime capable of loading and
     executing the Phase 8 compiled Wasm module, confirming correct
     execution under normal, well-behaved conditions first.

2. Resource limit configuration
   - Implement a configurable fixed memory ceiling for the sandbox.
   - Implement a configurable fixed compute-step ("fuel") budget using
     Wasmtime's fuel-metering mechanism, so execution can be halted based
     on actual computational work performed, not just wall-clock time.

3. Adversarial test module — memory
   - Write a deliberately malicious or buggy test Wasm module that
     attempts to allocate memory far beyond the configured ceiling.
   - Confirm the sandbox halts this module safely: no host crash, a clear
     and loggable failure reason, and no partial/corrupted state left
     behind.

4. Adversarial test module — compute
   - Write a second deliberately malicious or buggy test module containing
     an unbounded or near-unbounded loop.
   - Confirm the fuel-based budget halts this module before it can
     consume unbounded host resources, again with a clean, loggable
     failure and no host crash.

5. Configurability and defaults
   - Ensure memory and fuel limits are configurable per-invocation (since
     different task types may warrant different limits) rather than
     hardcoded, while establishing sensible default values suitable for
     the Phase 7-8 distilled module's actual resource needs.

CONSTRAINTS:
- Both adversarial tests must be run and must both result in safe,
  logged, non-crashing failure — this is a hard requirement, not a nice-
  to-have, since it is the core security property the rest of the
  Sovereign-MCP model depends on.
- Do not rely on Wasmtime's default limits without explicit configuration
  and testing — verify the actual limits enforced match what you intend.

DELIVERABLE: A repo with the sandbox runtime, its resource-limit
configuration, the two adversarial test modules and their confirmed safe-
failure results (including logs), and documentation of the default limits
chosen and why.
```

---

## Phase 10 — Scoped Data Access

```
You are restricting what a sandboxed Sovereign-MCP module can actually
see and touch, so it can only access the specific data it was authorized
for — nothing else on the host.

GOAL: Prove that a sandboxed module, however it behaves, can only read
data within its explicitly granted scope, and cannot reach the
filesystem, network, or any data outside that scope, via a deliberate
adversarial test.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Scoped data-access API design
   - Design a narrow, read-only data-access interface exposed to the
     sandboxed module — for example, a function that returns only the
     specific data region matched by a prior TIP handshake (see Group C),
     with no ability to request arbitrary data outside that region.
   - Use WASI's capability-based model deliberately: the module should be
     granted only the specific capability handle needed for its task, with
     no ambient authority to the filesystem or network at all.

2. Legitimate access path implementation
   - Wire this scoped API into the Phase 9 sandbox runtime, and confirm
     the Phase 7-8 distilled module can successfully read its intended
     data region and produce a correct result through this interface.

3. Adversarial test — unauthorized data access
   - Write a deliberately malicious test module that attempts to request
     data outside its granted scope (e.g. a different region ID, or a
     direct attempt to enumerate available data rather than using its
     specific handle).
   - Confirm this is blocked at the API boundary, with a clear, loggable
     denial — not a silent no-op that could be mistaken for a legitimate
     empty result.

4. Adversarial test — filesystem/network escape attempt
   - Write a second deliberately malicious test module that attempts to
     make a filesystem read/write call or a network call using any WASI
     capability that might be ambiently available.
   - Confirm these attempts fail because no such capability was granted,
     and that the failure is clean (no host crash, no partial side
     effect).

5. Audit logging
   - Ensure every data-access attempt — successful or blocked — through
     this interface is logged with enough detail to support later
     forensic review (see Group C's audit requirements).

CONSTRAINTS:
- Both adversarial tests must be run and confirmed blocked before this
  phase is considered complete — an unauthorized access path here breaks
  the core privacy guarantee the whole ATLAS system depends on.
- Do not grant any capability "just in case it's needed later" — the
  scoped interface should expose the absolute minimum access required for
  the task at hand.

DELIVERABLE: A repo with the scoped data-access API, its integration into
the Phase 9 sandbox, the two adversarial test modules and their confirmed
blocked-access results, and the audit logging implementation.
```

---

## Phase 11 — Attestation & End-to-End Demo

```
You are completing ATLAS's Sovereign-MCP workstream by adding verifiable
attestation of sandbox execution, and proving the entire chain works
end-to-end with an inspectable, reproducible demo.

GOAL: Let a requester independently verify that a remote host actually
executed their module under the declared resource and access constraints
— not just trust the host's word for it — and demonstrate the complete
flow with a network capture a third party can inspect.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Resource-usage logging
   - During each sandboxed execution (Phases 9-10), capture a structured
     log of actual resource usage: memory consumed, compute steps/fuel
     consumed, wall-clock execution time, and which scoped data region was
     accessed.

2. Signed attestation
   - Implement cryptographic signing of this resource-usage log by the
     host, using a key the requester can verify against a known public
     key, so the requester can confirm the log wasn't fabricated or
     altered after the fact.
   - Write a test that deliberately tampers with a resource-usage log
     after signing, and confirm the requester-side verification correctly
     detects the tampering and rejects the attestation.

3. End-to-end demo setup
   - Simulate two separate roles (can be two separate processes or
     containers): a "requester" that has a signed Phase 8 Wasm module
     ready to send, and a "host" running the Phase 9-10 sandbox runtime
     ready to receive and execute it.

4. Full exchange execution
   - Run the complete exchange: requester sends the signed module and
     specifies the target scoped data region, host executes it in the
     sandbox, host returns the result vector along with the signed
     attestation log, requester verifies the attestation signature.

5. Network capture and inspection
   - Capture the full network traffic of this exchange (e.g. with
     Wireshark or an equivalent packet-capture tool).
   - Personally review the capture and confirm that only the signed
     module, the small result vector, and the signed attestation log
     appear on the wire — no raw underlying data content is visible
     anywhere in the capture.

CONSTRAINTS:
- The tampered-attestation test must be run and must result in the
  requester correctly detecting and rejecting the tampered log — this is
  the property that makes attestation meaningful rather than decorative.
- The network capture review must be done by an actual person examining
  actual packet contents, not inferred from code review alone.

DELIVERABLE: A repo with the attestation signing/verification
implementation, the tampering-detection test result, the full end-to-end
demo (runnable by a second person from the repo alone), and the reviewed
network capture confirming no data leakage.
```

---

# GROUP C — Distributed TIP Protocol

## Phase 12 — Local Persistence + Landscape Transform

```
You are building the mathematical core of ATLAS's TIP protocol: local
persistent homology restricted to a query's neighborhood, transformed
into a fixed-length, comparable vector.

GOAL: Produce a representation of "the shape of the data immediately
around a specific point" that is both mathematically meaningful and
practically comparable between two independent organizations' systems —
this is the foundation everything in Group C builds on.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Local neighborhood restriction
   - Reusing the Group A pipeline's underlying components, implement
     restricting the Vietoris-Rips filtration and persistence computation
     to strictly the k-nearest-neighborhood of a given query point, rather
     than the whole dataset — confirm this restriction is actually
     enforced (i.e. the computation genuinely doesn't touch data outside
     the local neighborhood) as a correctness property, not just a
     performance optimization.

2. Local persistence diagram computation
   - Compute the local persistence diagram (birth/death intervals for H0
     and H1 at minimum) for this restricted neighborhood, using the same
     validated library (GUDHI/Ripser) from Phase 3.

3. Persistence landscape transform
   - Implement the persistence landscape transform: converting the
     (variable-size, awkward-to-compare) persistence diagram into a fixed-
     length vector representation, using the standard mathematical
     definition of persistence landscapes from the TDA literature (do not
     invent a custom transform without grounding it in an established
     definition).
   - Confirm the output vector length is genuinely fixed regardless of how
     many topological features the input local neighborhood contains.

4. Determinism verification
   - Run the full pipeline (local restriction → persistence → landscape
     transform) twice on the exact same input, and confirm the output
     vector is identical both times. Non-determinism here would break the
     cross-organization matching in Phase 13.

5. Discriminative power validation
   - Select several pairs of local neighborhoods you expect to be
     genuinely similar (e.g. two regions around near-duplicate anomaly
     patterns you construct synthetically) and several pairs you expect
     to be genuinely different. Compute landscape vectors for all of them
     and confirm similar pairs produce measurably close vectors (by a
     standard distance metric) while different pairs produce measurably
     distant vectors.

CONSTRAINTS:
- The local restriction must be verified as a genuine correctness
  property — confirm via logging or direct inspection that the
  computation does not access data outside the intended neighborhood.
- Do not proceed to Phase 13's LSH work until determinism and
  discriminative power are both confirmed with actual measurements, since
  a flaw here would silently undermine the entire matching protocol.

DELIVERABLE: A repo with the local persistence and landscape transform
pipeline, the determinism verification results, and the discriminative-
power validation results on the constructed similar/different pairs.
```

---

## Phase 13 — Locality-Sensitive Hashing

```
You are building the privacy-preserving matching mechanism for ATLAS's
TIP protocol: hashing the Phase 12 landscape vectors so similar local
structures can be matched across organizations without exchanging the
underlying vectors themselves.

GOAL: Prove that locality-sensitive hashing over the landscape vectors
achieves the three properties the entire TIP protocol depends on: similar
vectors collide with high probability, dissimilar vectors almost never
collide, and the original vector cannot be recovered from the hash.

BUILD THE FOLLOWING, IN THIS ORDER:

1. LSH implementation
   - Implement locality-sensitive hashing over the Phase 12 landscape
     vectors using random hyperplane projection (SimHash-style), producing
     a short, fixed-length hash code per vector.
   - Make the number of hyperplanes (hash length) a configurable
     parameter, since this directly trades off collision precision against
     hash length.

2. Collision-rate measurement — similar vectors
   - Using the "similar pairs" constructed in Phase 12's discriminative-
     power validation, compute LSH hashes for both vectors in each pair
     and measure the empirical collision rate. Report this as an actual
     percentage across many repeated trials with different random
     hyperplane seeds, not a single anecdotal run.

3. Collision-rate measurement — dissimilar vectors
   - Using the "different pairs" from Phase 12, perform the same
     measurement and report the false-collision rate — this should be
     substantially lower than the similar-pair collision rate, and you
     should quantify exactly how much lower.

4. Non-reconstructability test
   - Attempt to reconstruct or meaningfully approximate the original
     landscape vector given only its LSH hash code (e.g. try a brute-force
     or optimization-based reconstruction attempt). Confirm this fails to
     recover anything beyond the hash's inherent (low) information
     content, and document the attempt and result explicitly rather than
     asserting non-reconstructability without having tried.

5. Parameter tuning
   - Test at least three different hash-length (number of hyperplanes)
     settings and report how the collision-rate and false-collision-rate
     tradeoff shifts, so the production setting is chosen from evidence.

CONSTRAINTS:
- All collision rates must be measured across multiple trials with
  different random seeds, not reported from a single lucky or unlucky run.
- The non-reconstructability claim must be backed by an actual attempted
  reconstruction, not asserted purely from the theoretical properties of
  LSH in the abstract.

DELIVERABLE: A repo with the LSH implementation, the similar/dissimilar
collision-rate measurements across multiple trials, the non-
reconstructability test and its result, and the hash-length parameter
sensitivity analysis.
```

---

## Phase 14 — Protocol Message Schema

```
You are defining the exact wire format for ATLAS's TIP protocol before any
transport-layer code is written, so every later phase builds against a
stable, reviewed contract.

GOAL: Produce a precise, versioned, documented schema for all four TIP
messages, with validation that rejects malformed input safely, since this
schema is the contract every node implementation in Group C will depend
on matching exactly.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Schema definition
   - Define explicit field-level schemas for all four TIP messages:
     OFFER (carries query reference and LSH hash codes), MATCH (carries
     the matched hash code and a locally-scoped region reference), EXECUTE
     (carries the signed Wasm module and target region reference), and
     RESULT (carries the result vector and signed attestation log).
   - Use a structured schema definition format (protobuf, or an equivalent
     schema language) rather than ad hoc JSON with implicit structure, so
     the schema itself is machine-checkable.

2. Field-level constraints
   - For every field, define explicit size/type constraints (e.g. maximum
     hash code length, maximum result vector size — recall this should be
     in the 256-byte class, not unbounded) so a malformed or oversized
     message can be rejected mechanically rather than by convention.

3. Serialization and deserialization
   - Implement serialization and deserialization for all four message
     types, with the schema's constraints enforced during deserialization
     (not just documented and hoped for).

4. Malformed-message handling
   - Write a suite of malformed-message test cases: truncated messages,
     messages with fields exceeding defined size limits, messages with
     unexpected/extra fields, and messages with an invalid message-type
     tag.
   - Confirm every malformed test case is rejected gracefully with a clear
     error, not a crash or an unhandled exception.

5. Versioning
   - Add an explicit protocol-version field to every message, and
     implement basic version-mismatch handling (reject or negotiate,
     documented explicitly) so the schema can evolve later without
     silently breaking older node implementations.

CONSTRAINTS:
- Every malformed-message test case must result in graceful rejection,
  confirmed by actually running the tests — not asserted from code
  inspection alone.
- The schema must be reviewed by at least one person other than whoever
  wrote it before Phase 15's transport implementation begins.

DELIVERABLE: A repo with the formal schema definitions, the
serialization/deserialization implementation, the malformed-message test
suite and its confirmed-safe results, and the documented versioning
scheme.
```

---

## Phase 15 — QUIC Transport Layer

```
You are implementing the actual network transport for ATLAS's TIP
protocol, wiring the Phase 14 message schema onto a real QUIC connection
between genuinely separate processes.

GOAL: Prove two independent node processes can reliably exchange all four
TIP message types over a real network connection, including handling a
dropped connection gracefully, before any multi-node simulation work
begins.

BUILD THE FOLLOWING, IN THIS ORDER:

1. QUIC connection setup
   - Using an established async QUIC implementation (quinn, paired with
     tokio, or an equivalent maintained stack), implement basic connection
     establishment between two processes: one acting as a TIP client, one
     as a TIP server.

2. Message exchange over the connection
   - Wire the Phase 14 serialization/deserialization and schema validation
     into the QUIC connection, and implement sending and receiving all
     four TIP message types over it.

3. Two-process verification
   - Run the client and server as two genuinely separate operating-system
     processes (not two objects in the same process pretending to be
     separate) and confirm a full OFFER → MATCH → EXECUTE → RESULT
     exchange completes correctly between them.

4. Connection resilience
   - Implement and test a dropped-connection scenario: forcibly kill the
     connection mid-exchange and confirm the affected side detects this
     and either retries the connection or fails cleanly with a clear
     error, rather than hanging indefinitely or crashing.

5. Logging
   - Log every message sent and received, with timestamps, at both the
     client and server side, in a format that will support the forensic-
     replay requirement in later phases.

CONSTRAINTS:
- The two-process test must use genuinely separate processes communicating
  over a real network socket — do not substitute in-process function calls
  standing in for the network layer, since that would not actually test
  what this phase is meant to prove.
- The dropped-connection test must be run and its result (retry or clean
  failure) explicitly confirmed, not assumed to work based on the
  underlying QUIC library's general reliability claims.

DELIVERABLE: A repo with the QUIC transport implementation, the two-
process end-to-end message exchange demonstration, the dropped-connection
resilience test and its result, and the message logging implementation.
```

---

## Phase 16 — Multi-Node Simulation Environment

```
You are standing up the containerized, multi-node test environment that
Phase 17's full end-to-end scenario will run in.

GOAL: Get three genuinely separate ATLAS nodes running reliably via
container orchestration, with a synthetic dataset containing a
deliberately planted, discoverable anomaly shared across two of the
nodes, ready for the full protocol demonstration.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Node containerization
   - Package a full ATLAS node (the Group A manifold-indexing components,
     the Group B S-MCP runtime, and the Group C TIP transport/protocol
     components) into a single container image, configurable via
     environment variables or a config file for different roles (data
     node vs. requester node).

2. Multi-node orchestration
   - Using Docker Compose or Kubernetes, define a deployment of three
     nodes: two data nodes (representing, for example, "Bank A" and
     "Bank B") and one requester node (representing "the Regulator").
   - Confirm all three nodes start cleanly from a single deployment
     command, with correct networking between them (each node reachable
     by the others at a stable address).

3. Synthetic dataset generation
   - Generate two synthetic datasets, one per data node, using a
     documented, reproducible generation script (not hand-crafted data
     that can't be regenerated).
   - Deliberately plant one shared anomaly pattern across both datasets —
     structured so it is genuinely discoverable via the Group A/C pipeline
     (i.e. it actually produces matching local topological structure, not
     just matching surface-level values) — and document exactly what was
     planted and where, so later phases can verify detection against
     ground truth.

4. Node lifecycle testing
   - Test stopping and restarting individual nodes independently and
     confirm this doesn't break the other running nodes' state or
     connectivity.

5. Basic health checks
   - Implement simple health-check endpoints for each node so the
     orchestration layer (and later, Group F's observability work) can
     confirm each node is actually up and its indexing pipeline has
     completed, not just that the container process is running.

CONSTRAINTS:
- All three nodes must be genuinely separate containers/processes with
  real network communication between them — this environment exists
  specifically to test real distributed behavior, not simulate it
  in-process.
- The planted anomaly must be verified as actually discoverable by the
  underlying topological pipeline before proceeding to Phase 17 — confirm
  this with a quick manual check, not just an assumption that planting it
  in the raw data is sufficient.

DELIVERABLE: A repo with the containerized node image, the multi-node
orchestration configuration, the synthetic dataset generation scripts and
documented planted-anomaly ground truth, and the node lifecycle and
health-check test results.
```

---

## Phase 17 — Full End-to-End Scenario + Failure Handling

```
You are running the culminating demonstration of ATLAS's core protocol:
the full three-node scenario from Phase 16, proving the entire TIP → S-MCP
chain works together, plus two deliberate failure-mode tests.

GOAL: Prove, in a real (if simulated) multi-node deployment, that a
structural anomaly shared across two independent data nodes can be
discovered and confirmed by a requester without any raw data leaving
either data node, and that the system fails safely under two realistic
failure conditions.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Full-flow wiring
   - Wire together the Group A manifold indexing (per data node), the
     Group C TIP handshake (OFFER/MATCH), and the Group B S-MCP sandboxed
     execution (EXECUTE/RESULT) into a single coherent flow triggered by
     the requester node.

2. End-to-end execution against the planted anomaly
   - From the requester node, issue a TIP query targeting the kind of
     anomaly planted in Phase 16. Confirm both data nodes compute and
     return LSH hash codes, a MATCH is correctly found on the planted
     anomaly (and not a false match elsewhere), the requester dispatches a
     signed S-MCP module scoped to the matched region on both data nodes,
     and both return valid result vectors that the requester combines to
     correctly identify the planted anomaly.
   - Compare the result against the Phase 16 documented ground truth to
     confirm correctness, not just "a result was produced."

3. Failure case — node offline mid-handshake
   - Deliberately kill one data node's process partway through a TIP
     handshake. Confirm the requester detects this failure and handles it
     cleanly (clear error, no hang, no partial/corrupted state), rather
     than crashing or silently proceeding as if the handshake succeeded.

4. Failure case — tampered/malformed message
   - Deliberately inject a tampered or malformed message into the exchange
     (e.g. altering a hash code or corrupting the message schema mid-
     flight). Confirm the receiving node's Phase 14 validation rejects it
     cleanly, with no data leak and no crash.

5. Forensic replay verification
   - After the full successful run, using only the logs captured at both
     the requester and data nodes (per Phase 15's logging), attempt to
     fully reconstruct the sequence of messages and actions that occurred
     — without referring back to your live memory of running it — and
     confirm the logs alone are sufficient to do this.

CONSTRAINTS:
- The end-to-end result must be checked against the Phase 16 documented
  ground truth, not just accepted because "something matched."
- Both failure-case tests must be run and confirmed to fail safely — a
  crash, hang, or silent data leak in either case is a phase-blocking
  issue, not a minor bug to note and move past.
- The forensic replay must be performed using only stored logs, as a
  genuine test of whether the audit trail is actually sufficient after
  the fact.

DELIVERABLE: A repo with the fully wired end-to-end flow, the successful
run's results compared against Phase 16's ground truth, both failure-case
test results, and the forensic replay demonstration using stored logs
alone.
```

---

# GROUP D — Real-Data Pilot Integration

## Phase 18 — Design Partner Data Agreement

```
You are establishing the legal and compliance foundation required before
any real design-partner data touches the ATLAS pipeline. This phase is
primarily a legal/business task, not a coding task, but the technical
team's input on what data access and anonymization actually require is
essential to getting the agreement right.

GOAL: Produce a signed agreement with one design partner that precisely
specifies what data will be used, how it will be anonymized or sandboxed,
what "success" for the pilot means in concrete, measurable terms, and
what happens to the data and any derived artifacts after the pilot ends.

WORK THROUGH THE FOLLOWING, IN THIS ORDER:

1. Technical requirements input
   - Before legal drafting begins, have the engineering team document
     exactly what data fields, formats, and volume are needed for
     meaningful pilot testing (informed by the Group A-C pipeline's actual
     requirements), and what anonymization/sandboxing approach would be
     technically sufficient given the S-MCP execution model's scoped-
     access guarantees from Phase 10.

2. Draft agreement terms
   - Draft an agreement specifying: the exact data scope permitted, the
     anonymization/sandboxing method required before data enters any
     ATLAS component, data retention and deletion terms after the pilot,
     and explicit, numerical success criteria for the pilot (e.g. what
     accuracy or detection result would constitute a successful pilot from
     the partner's perspective).

3. Compliance review
   - Have the agreement reviewed against the partner's actual regulatory
     obligations (e.g. financial-services data handling rules relevant to
     their jurisdiction), not just generic data-processing language.

4. Sign-off process
   - Establish a clear internal sign-off checklist confirming the
     agreement is fully executed before any real data is requested from
     the partner or ingested into any pipeline.

CONSTRAINTS:
- No real partner data may be requested, transmitted, or ingested into any
  ATLAS component until this agreement is fully signed — this is an
  absolute gate, not a "we'll finalize paperwork in parallel" situation.
- Success criteria must be specific and numerical wherever possible (e.g.
  "detect at least X% of a defined synthetic-injected anomaly type,
  reviewed and confirmed by the partner"), not vague language like
  "demonstrate value."

DELIVERABLE: A fully signed data-sharing and compliance agreement, the
documented technical data requirements that informed it, and an internal
sign-off checklist confirming the agreement is executed before Phase 19
begins.
```

---

## Phase 19 — Real-Data Ingestion Adaptation

```
You are adapting the Group A ingestion pipeline to handle the design
partner's real (anonymized/sandboxed, per Phase 18's agreement) data,
which will expose data-quality problems the synthetic and public
benchmark data never did.

GOAL: Get the partner's real data flowing correctly through the existing
pipeline, with every place the real data broke an assumption from Groups
A-C explicitly documented rather than silently patched around.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Format mapping
   - Map the partner's real data format (received per the Phase 18
     agreement's anonymization/sandboxing terms) into the input format the
     Group A pipeline expects, documenting every transformation applied.

2. Data-quality issue identification
   - Run the Phase 1-style data-quality report against the real data
     specifically, identifying: missing or null fields not present in the
     synthetic/benchmark data, inconsistent formatting or encoding issues
     specific to the partner's systems, duplicate or near-duplicate
     records at a different rate than synthetic data exhibited, and any
     class imbalance in the actual anomaly rate compared to the synthetic
     data's constructed rate.

3. Assumption audit
   - Go through each prior Group A-C phase's stated assumptions (e.g.
     Phase 2's k-NN parameters tuned on synthetic data, Phase 4's
     sparsification parameters) and explicitly test whether each still
     holds on the real data. Document every assumption that breaks, with
     enough detail that whoever fixes it later understands exactly what
     changed and why.

4. Remediation
   - For each identified issue, implement a fix (data cleaning step,
     parameter retuning, or pipeline adjustment) and re-verify the
     specific downstream behavior that was affected, rather than assuming
     the fix resolves the issue without checking.

5. Partner visibility
   - Provide the design partner with visibility into what transformations
     were applied to their data at each step, consistent with the
     transparency terms of the Phase 18 agreement.

CONSTRAINTS:
- Every "the synthetic data didn't expose this" finding must be written
  down explicitly, even for issues that get quickly fixed — this record is
  what makes Group F's later scale-engineering work grounded in real
  experience rather than guesswork.
- No silent workarounds: if a fix changes a parameter or assumption from
  an earlier Group A-C phase, that phase's documentation must be updated
  to reflect the change.

DELIVERABLE: A repo update with the real-data ingestion adaptation, the
data-quality report specific to the real data, the full assumption-audit
document listing every broken assumption and its fix, and the partner-
facing transparency documentation.
```

---

## Phase 20 — Real-Data Benchmark Re-Run

```
You are re-running the Phase 6 benchmark methodology against the design
partner's real data, to find out whether the Manifold-Core approach's
advantage over cosine-similarity RAG holds outside synthetic and public
benchmark conditions.

GOAL: Produce an honest, real-data accuracy comparison, reported with the
same rigor as Phase 6, even if the result is less favorable than the
original benchmark suggested.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Real-data evaluation set construction
   - Working within the Phase 18 agreement's terms, construct an
     evaluation set from the partner's real data analogous to Phase 6's
     benchmark structure (queries with known correct multi-hop or
     structural answers), with the partner's input on what a "correct"
     answer looks like in their domain.

2. Side-by-side re-run
   - Run both the cosine-similarity RAG baseline and the Manifold-Core
     traversal system (using the Phase 19-adapted real-data pipeline)
     against this real-data evaluation set, using the same reporting
     structure as Phase 6 (accuracy, latency, compute cost side by side).

3. Comparison against the original benchmark result
   - Directly compare the real-data accuracy delta against the Phase 6
     external-benchmark accuracy delta. If there is a meaningful gap
     between the two, investigate why: is it a data-quality issue from
     Phase 19, a domain-specific structural difference the public
     benchmark didn't capture, or something else?

4. Partner review
   - Have the design partner review the results and confirm, from their
     domain expertise, whether the reported accuracy improvement (or lack
     thereof) is meaningful in a way that matters to their actual use
     case, not just statistically present.

CONSTRAINTS:
- Report the real-data numbers even if they are worse than the Phase 6
  synthetic/public-benchmark numbers — this comparison exists specifically
  to catch that gap if it's there, not to confirm a foregone conclusion.
- The partner's domain-expert review must be a genuine, documented
  conversation, not a formality — their judgment on "does this matter in
  practice" carries real weight here.

DELIVERABLE: A report comparing real-data accuracy results against the
Phase 6 external-benchmark results side by side, an investigation of any
significant gap between the two, and documented partner sign-off on
whether the results are meaningful for their use case.
```

---

## Phase 21 — Real-Scenario TIP/S-MCP Validation

```
You are replacing the Phase 17 synthetic planted-anomaly scenario with a
real anomaly pattern from the design partner's actual data, under their
explicit sign-off, to validate the full TIP/S-MCP protocol chain against
a genuine (not constructed) structural pattern.

GOAL: Prove the full cross-node protocol correctly detects and confirms a
real anomaly pattern meaningful to the design partner, while re-verifying
— fresh, not assumed carried over — that no raw data leaves either data
node during the process.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Real anomaly pattern selection
   - Working with the design partner, identify a real (but appropriately
     scoped and sign-off'd) anomaly or structural pattern present in their
     actual data that would be meaningful for them to see correctly
     detected — get their explicit agreement on exactly what is being
     tested before proceeding.

2. Re-run the Group C end-to-end flow
   - Using the Phase 19-adapted real-data pipeline in place of the Phase
     16 synthetic dataset, re-run the full Phase 17 end-to-end scenario
     (TIP handshake → match → S-MCP execution → result combination)
     targeting the real anomaly pattern identified in step 1.

3. Partner confirmation of meaningful detection
   - Have the design partner review the detected result and confirm it
     represents a genuinely meaningful finding in their domain, not merely
     a statistically present match that lacks real-world significance.

4. Fresh data-leakage verification
   - Re-run the Phase 17-style network-capture review and audit-log
     forensic-replay check specifically on this real-data run — do not
     assume the Phase 17 leakage guarantees automatically transfer
     unchanged to a new dataset and scenario; verify it fresh, on this
     specific run, with this specific data.

CONSTRAINTS:
- The partner's explicit sign-off on what pattern is being tested must be
  obtained and documented before this phase begins, consistent with the
  Phase 18 agreement's terms.
- The data-leakage verification in step 4 must be performed as a fresh,
  independent check on this run — treating Phase 17's result as
  automatically still valid here would be an unverified assumption, not a
  confirmed fact.

DELIVERABLE: A report on the real-scenario end-to-end run, the design
partner's documented confirmation that the detected pattern is
meaningful, and the fresh data-leakage verification results (network
capture and forensic replay) specific to this real-data run.
```

---

# GROUP E — Security & Compliance Hardening

## Phase 22 — Formal Threat Model

```
You are writing the formal, comprehensive threat model covering every
mechanism built across Groups A through D, as the foundation for all of
Group E's hardening work.

GOAL: Produce a threat-model document thorough enough that an independent
reviewer (Phase 25's external auditor) could use it as a starting map of
what to test, with every major mechanism from prior groups represented and
every identified threat given an explicit mitigation or an explicit,
written "accepted risk" label.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Mechanism inventory
   - Systematically list every major mechanism built in Groups A-D: the
     manifold indexing pipeline, the local persistence/landscape/LSH
     matching, the QUIC transport and message schema, the S-MCP sandbox
     and scoped data access, the attestation mechanism, and the real-data
     ingestion/adaptation layer.

2. Threat identification per mechanism
   - For each mechanism, identify concrete threat scenarios: data-exposure
     vectors (could raw data leak through this mechanism under any
     condition?), sandbox-escape vectors (could a malicious module use
     this mechanism to exceed its intended boundaries?), protocol replay
     or tampering vectors (could a captured or modified message be reused
     maliciously?), and the known, previously-identified information-
     leakage question from repeated TIP querying over time (documented
     honestly here as a named, tracked threat, not omitted because it's
     unsolved).

3. Mitigation mapping
   - For each identified threat, map it to either an existing mitigation
     already built in a prior phase (citing exactly which phase and test
     addresses it), a planned mitigation to be built in a later Group E
     phase (Phase 23's differential-privacy work, for instance), or an
     explicit "accepted risk" designation with a written rationale for why
     it's accepted at this stage.

4. External review
   - Have the complete threat model reviewed by someone who did not build
     the system (an internal colleague at minimum, ahead of the Phase 25
     external audit), and incorporate their feedback on anything missed.

CONSTRAINTS:
- Every major mechanism from Groups A-D must appear somewhere in this
  document — a mechanism with zero associated threats listed should be
  treated as a sign the analysis is incomplete, not as a mechanism with no
  risk.
- "Accepted risk" is a legitimate outcome for a threat, but it must be
  written down explicitly with a stated rationale, not implied by silence.

DELIVERABLE: A complete threat-model document covering every mechanism
from Groups A-D, with every identified threat mapped to a mitigation or an
explicit accepted-risk rationale, and documented review feedback from at
least one person outside the immediate build team.
```

---

## Phase 23 — Differential Privacy Layer for TIP

```
You are closing the specific, previously-identified open risk from Phase
4's threat model: information leakage from repeated TIP queries over
time, by adding rate-limiting and differential-privacy noise to the LSH
hash-generation process.

GOAL: Implement a concrete mitigation for the repeated-querying leakage
risk, and honestly measure the resulting tradeoff between privacy
protection and match accuracy — this is not a mitigation you can add
without cost, and that cost needs to be quantified.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Rate-limiting implementation
   - Implement rate-limiting on TIP handshake requests, per requester
     identity, with a configurable threshold (e.g. maximum handshakes per
     time window) enforced at the receiving node.
   - Write a test that deliberately exceeds the rate limit and confirms
     it's enforced (requests beyond the limit are rejected or delayed, not
     silently processed).

2. Differential privacy noise injection
   - Implement adding calibrated noise to the Phase 13 LSH hash-generation
     step, using an established differential-privacy mechanism (e.g. a
     randomized-response-style perturbation appropriate to the hash-
     generation process), with a tunable privacy parameter (epsilon).

3. Privacy/accuracy tradeoff measurement
   - Using the Phase 13 similar/dissimilar vector pairs, measure how the
     collision rate for genuinely similar vectors and the false-collision
     rate for genuinely dissimilar vectors both change as the noise level
     (epsilon) is increased.
   - Report this as a clear tradeoff curve, not a single chosen setting
     presented without the alternatives that were considered.

4. Repeated-query leakage estimation
   - Construct a test simulating an adversary issuing many repeated,
     slightly-varied queries against the same target region, and measure
     empirically how much information (if any) can be inferred about the
     underlying data after the differential-privacy mitigation is applied,
     compared to before it.

CONSTRAINTS:
- The privacy/accuracy tradeoff must be reported as a real measured curve
  across multiple epsilon values, not a single asserted "good" setting.
- The repeated-query leakage estimation must be an actual empirical test
  against a simulated adversary, not a theoretical argument alone — report
  the result honestly even if it shows the mitigation only partially
  closes the gap.

DELIVERABLE: A repo with the rate-limiting implementation and its
enforcement test, the differential-privacy noise injection implementation,
the privacy/accuracy tradeoff curve across multiple epsilon settings, and
the repeated-query leakage estimation results before and after mitigation.
```

---

## Phase 24 — Red-Team Test Suite

```
You are building an automated adversarial test suite that systematically
attempts to violate every threat identified in the Phase 22 threat model,
as a standing regression check the system must keep passing going forward.

GOAL: Produce a re-runnable suite of adversarial tests covering every
major threat category from Phase 22, so that every future phase and code
change can be checked against it automatically, rather than security
testing being a one-time manual exercise.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Test case derivation from the threat model
   - Go through the Phase 22 threat model systematically, and for every
     identified threat with an existing mitigation, write at least one
     automated test that attempts to trigger the threat and confirms the
     mitigation holds (many of these tests will build directly on the
     adversarial tests already written in Phases 9, 10, 11, 15, and 17 —
     consolidate and extend them here rather than starting from scratch).

2. Coverage mapping
   - Produce an explicit mapping document showing which Phase 22 threat
     maps to which specific automated test, so gaps in coverage are
     visible rather than hidden.

3. Near-miss and partial-failure handling
   - For any test where the mitigation partially holds but doesn't fully
     close the threat (this is expected for the Phase 23 differential-
     privacy mitigation specifically), document this as a partial pass
     with the specific residual risk noted, rather than marking it a full
     pass or a full failure inaccurately.

4. Suite automation
   - Integrate the full suite into a re-runnable automated pipeline (e.g.
     a CI job) so it can be run against every future code change across
     Groups A-D without manual setup each time.

5. Baseline run and sign-off
   - Run the complete suite against the current system state, review every
     result personally, and produce a signed-off summary report before
     proceeding to Phase 25's external audit.

CONSTRAINTS:
- Every threat in the Phase 22 document with a claimed mitigation must
  have a corresponding automated test — a mitigation with no test is
  effectively an unverified claim.
- Partial passes must be reported as partial, with the specific residual
  gap named — do not round a partial mitigation up to a full pass.

DELIVERABLE: A repo with the automated red-team test suite, the threat-
to-test coverage mapping document, the CI integration, and a signed-off
baseline test-run report identifying any full or partial failures.
```

---

## Phase 25 — External Security Audit

```
You are preparing ATLAS for, and then acting on the results of, an
independent third-party security audit of the sandbox and protocol —
this phase is primarily about facilitating and responding to external
review, not internal development.

GOAL: Get a genuinely independent security firm to audit the system, and
ensure every finding is addressed or explicitly accepted as a documented
residual risk before any real institutional pilot proceeds.

WORK THROUGH THE FOLLOWING, IN THIS ORDER:

1. Audit preparation
   - Assemble a complete documentation package for the auditors: the
     Phase 22 threat model, the Phase 24 red-team suite and its coverage
     mapping, architecture documentation for the sandbox (Group B) and
     protocol (Group C), and access to a representative test environment
     (using synthetic data only, not real partner data, unless separately
     authorized).

2. Engage an independent firm
   - Select and engage a security firm with no prior involvement in
     building the system, specifically scoped to review the sandbox
     isolation boundary (Group B) and the protocol's cryptographic/privacy
     properties (Group C).

3. Findings triage
   - For every finding the auditors report, triage it explicitly: fix
     immediately, schedule a fix with a committed timeline, or accept as a
     documented residual risk with a written rationale approved by
     technical leadership.

4. Remediation and re-verification
   - Implement fixes for findings that require immediate action, and have
     the auditors (or an equivalent independent check) re-verify that the
     fix actually resolves the finding, rather than closing it out based
     on internal confirmation alone.

5. Full disclosure documentation
   - Document the complete audit findings and their resolution status —
     including accepted risks — in a form suitable for later inclusion in
     the Phase 26 compliance documentation package.

CONSTRAINTS:
- The auditing firm must be genuinely independent, with no involvement in
  building the system being audited.
- Every finding must be documented regardless of severity or how it
  reflects on the team — omitting a finding from the record defeats the
  entire purpose of an independent audit.

DELIVERABLE: The complete external audit report, the findings-triage
documentation, evidence of remediation and re-verification for fixed
findings, and the full disclosure documentation including any accepted
residual risks.
```

---

## Phase 26 — Compliance Documentation Package

```
You are assembling the compliance documentation package that a regulated
customer's compliance and legal teams will actually need to review before
approving deployment.

GOAL: Produce documentation that accurately represents what has been
proven (from Phases 22-25) about the system's privacy and security
properties — no more, no less — in a form a non-technical compliance
officer can actually understand and act on.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Data flow documentation
   - Produce clear diagrams showing exactly what data moves where, at each
     stage of the pipeline (ingestion, indexing, TIP handshake, S-MCP
     execution), explicitly marking what never leaves a node's boundary
     versus what does cross a network boundary (and in what form — hash
     codes, signed modules, result vectors).

2. Plain-language privacy guarantee explanation
   - Write a plain-language explanation of the actual privacy guarantees
     the system provides, calibrated precisely to what Phases 4, 13, and
     23 actually proved — explicitly stating that this is privacy-
     preserving approximate matching, not a formal zero-knowledge
     guarantee, and explaining what the differential-privacy mitigation
     does and does not fully close.

3. Threat model and audit summary inclusion
   - Include a compliance-appropriate summary of the Phase 22 threat model
     and the Phase 25 external audit findings and their resolution status,
     translated from technical detail into language a compliance reviewer
     can evaluate against their own regulatory obligations.

4. Non-technical review
   - Have the complete package reviewed by someone with a compliance or
     legal background (not an engineer), and confirm they can correctly
     explain the system's actual privacy guarantees back to you after
     reading it — this is the real test of whether the plain-language
     explanation succeeded.

CONSTRAINTS:
- Every privacy or security claim in this package must trace back to a
  specific, actually-completed phase's actual result — no claim should
  describe an aspirational or planned property as if it were already
  proven.
- The non-technical reviewer's comprehension check in step 4 is a required
  gate, not an optional nicety — a compliance package that only engineers
  can correctly interpret has failed its purpose.

DELIVERABLE: The complete compliance documentation package, including data
flow diagrams, the plain-language privacy guarantee explanation, the
compliance-oriented threat/audit summary, and documented confirmation from
a non-technical reviewer that they understood it correctly.
```

---

# GROUP F — Scale Engineering

## Phase 27 — Large-Scale Profiling

```
You are profiling the full Group A-D pipeline against production-scale
data volumes, to find the actual bottlenecks rather than the ones assumed
from prototype-scale experience.

GOAL: Produce real, measured performance data at a target scale several
orders of magnitude larger than anything tested so far (millions of
records), identifying exactly where time and memory are actually being
spent, as the factual foundation for every later Group F optimization
phase.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Target-scale dataset preparation
   - Acquire or construct a dataset at the target production scale
     (millions of records) — using a larger subset of the same named
     public corpus type from Phase 1, or, if available under the Phase 18
     agreement's terms, an appropriately scaled real-data sample.

2. Full-pipeline instrumentation
   - Instrument every major stage of the pipeline (embedding, k-NN graph
     construction, sparsified filtration, persistence computation,
     traversal query resolution) with detailed timing and memory
     profiling, not just start-to-end wall-clock time.

3. Bottleneck identification
   - Run the fully instrumented pipeline at target scale and identify,
     with actual profiler output (not assumption), which specific stages
     consume the most time and memory, and whether this matches or
     contradicts the assumptions carried over from prototype-scale work
     in Groups A-D.

4. Baseline recording
   - Record these numbers as the explicit baseline that Phases 28-31's
     optimization work will be measured against, in a format that makes
     before/after comparison straightforward later.

5. Scaling-curve estimation
   - Run the pipeline at several intermediate scales (e.g. 100k, 500k, 1M,
     several million records) and plot how each major stage's time and
     memory usage scales with data volume, to identify which stages scale
     linearly, superlinearly, or sublinearly.

CONSTRAINTS:
- All numbers must come from actually running the pipeline at each tested
  scale — do not extrapolate from small-scale numbers using an assumed
  scaling law without direct large-scale measurement to confirm it.
- Bottleneck identification must be based on actual profiler output,
  reviewed personally, not on which stage seemed likely to be slow based
  on its algorithmic complexity alone.

DELIVERABLE: A detailed profiling report with per-stage timing and memory
measurements across multiple scales, the identified bottlenecks ranked by
actual measured impact, and the scaling-curve analysis for each major
pipeline stage.
```

---

## Phase 28 — Incremental Persistence Updates

```
You are implementing incremental persistence computation, so that new
data arriving after the initial index build doesn't require a full,
expensive recomputation from scratch — directly targeting whichever
bottleneck Phase 27 identified as most costly in the filtration/
persistence stage.

GOAL: Prove that an incremental (vineyard-style) update approach produces
topologically equivalent results to full recomputation, while being
measurably cheaper for the common case of new data arriving into an
already-indexed dataset.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Incremental update algorithm implementation
   - Implement an incremental persistence update approach (vineyard
     algorithms, or an equivalent established technique for updating
     persistence diagrams as new points are added to a filtration), built
     on top of the Phase 4 sparsified pipeline.

2. Equivalence verification
   - On a fixed dataset, compute the persistence diagram via full
     recomputation (the Phase 4 approach) and via the new incremental
     approach (starting from an initial index and adding the same new
     points incrementally), and confirm the two approaches produce
     topologically equivalent results — document any discrepancies found
     and their cause.

3. Performance comparison
   - At the Phase 27 target scale, measure and directly compare: time and
     memory cost of a full recomputation after adding a batch of new
     points, versus the incremental update approach adding the same batch.
     Report this as a clear, direct comparison, not a theoretical
     complexity argument alone.

4. Rolling-window testing
   - Test the incremental approach under a rolling-window scenario:
     continuously adding new data over many successive batches (not just a
     single one-time update), and confirm correctness and performance hold
     up over many successive increments, not just the first one.

5. Failure-mode handling
   - Identify and test at least one scenario where incremental updates
     might degrade over time (e.g. accumulated approximation error across
     many increments) and implement a periodic full-recomputation fallback
     if needed, with the trigger condition for that fallback explicitly
     documented.

CONSTRAINTS:
- Topological equivalence between full and incremental approaches must be
  directly verified on real computed output, not assumed from the
  incremental algorithm's theoretical correctness alone.
- The rolling-window test must run over enough successive increments to
  reveal any degradation pattern — a single-batch test is not sufficient
  evidence this approach holds up in real, continuous operation.

DELIVERABLE: A repo with the incremental persistence update
implementation, the equivalence verification results, the direct
performance comparison against full recomputation at target scale, the
rolling-window degradation test results, and the documented fallback
mechanism if one was needed.
```

---

## Phase 29 — Multi-Tenant Deployment Isolation

```
You are building the deployment tooling and resource isolation that lets
ATLAS run multiple independent tenants' nodes concurrently without one
tenant's behavior affecting another's.

GOAL: Prove, with a deliberate stress test, that one tenant's resource
spike or failure cannot degrade another tenant's node performance or
availability, since this is a hard requirement before any multi-customer
deployment.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Multi-tenant deployment architecture
   - Design and implement deployment tooling (building on the Phase 16
     containerization work) that allows multiple tenants' ATLAS nodes to
     run concurrently on shared underlying infrastructure, with resource
     quotas (CPU, memory, storage) configurable per tenant.

2. Resource isolation enforcement
   - Implement enforcement of these per-tenant resource quotas at the
     orchestration layer (e.g. Kubernetes resource limits and namespaces,
     or an equivalent isolation mechanism), confirmed to actually restrict
     a tenant to its allocated resources rather than being advisory only.

3. Stress test — resource spike
   - Deliberately overload one simulated tenant's node with an artificial
     high-load workload (e.g. a flood of queries or an intentionally
     resource-heavy indexing job) and measure whether a second, unrelated
     tenant's node performance (query latency, availability) is affected.
     Report the measured impact (ideally none, but report honestly what
     you actually observe).

4. Stress test — tenant failure
   - Deliberately crash one simulated tenant's node entirely and confirm
     other tenants' nodes continue operating normally, unaffected by the
     failure.

5. Deployment portability verification
   - Confirm the multi-tenant deployment tooling works from a genuinely
     clean environment (not just the specific machine/cluster it was
     originally developed on), to verify it's actually portable
     infrastructure and not accidentally dependent on undocumented local
     configuration.

CONSTRAINTS:
- Both stress tests (resource spike and tenant failure) must be run and
  their actual measured impact on other tenants reported honestly — if
  some cross-tenant impact is observed, this must be documented and
  addressed, not glossed over.
- The clean-environment portability check is a required test, not an
  assumption — deployment tooling that only works on the machine it was
  built on is not actually production-ready tooling.

DELIVERABLE: A repo with the multi-tenant deployment tooling and resource-
quota enforcement, the resource-spike stress test results, the tenant-
failure stress test results, and the clean-environment portability
verification.
```

---

## Phase 30 — Observability & Alerting

```
You are building the monitoring, logging, and alerting infrastructure that
lets the team detect problems in a running ATLAS deployment before a
customer has to report them.

GOAL: Prove, via a deliberately injected failure, that the observability
system actually catches a real problem before it silently produces wrong
results downstream — not just that dashboards exist and look reasonable.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Metrics instrumentation
   - Instrument the running system (across Groups A-D's components) with
     metrics covering: index health (e.g. last successful update time,
     index size, error rate during indexing), query latency (p50/p99), and
     S-MCP sandbox resource usage (memory/fuel consumption trends over
     time, per Phase 9-11's logging).

2. Logging pipeline
   - Centralize logs from all node components (per Phase 15's per-node
     logging) into a queryable, searchable logging system, so incident
     investigation doesn't require manually gathering logs from individual
     containers.

3. Dashboard construction
   - Build dashboards visualizing the instrumented metrics, designed to be
     understandable by someone who did not build the underlying system —
     verify this by having a team member unfamiliar with the internals
     review the dashboard and correctly interpret what it shows.

4. Alerting rules
   - Define alerting rules for the metrics that matter most (e.g. index
     staleness beyond a threshold, error-rate spikes, sandbox resource
     usage anomalies), tuned to avoid both missing real problems and
     generating so many false alerts that real ones get ignored.

5. Injected-failure validation
   - Deliberately inject a realistic failure into a test deployment (e.g.
     corrupt part of an index, or introduce a bug that causes silently
     wrong query results) and confirm the alerting system catches this
     before — not after — a query returns an incorrect result to a
     hypothetical customer.

CONSTRAINTS:
- The injected-failure test is the actual bar for this phase being
  complete — dashboards that look comprehensive but fail to catch a real
  injected problem have not actually proven anything.
- Alert-threshold tuning must be based on some evidence of realistic
  operating ranges (from Phase 27's profiling data, for instance), not
  arbitrary round numbers picked without justification.

DELIVERABLE: A repo with the metrics instrumentation, the centralized
logging pipeline, the dashboards (reviewed for comprehensibility by
someone outside the build team), the alerting rule definitions, and the
injected-failure validation demonstrating the alerting actually catches a
real problem.
```

---

## Phase 31 — Cost Modeling at Scale

```
You are building a real, data-grounded cost model for running ATLAS at
production scale, using the actual measured resource usage from Phases
27-30 rather than prototype-scale guesses.

GOAL: Determine, with real numbers, whether the actual cost-per-query at
target production scale supports a viable business — this is a business-
critical calculation that needs to happen now, not be deferred until
after a sales team has already made promises based on assumed economics.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Resource cost baseline
   - Using the actual measured compute, memory, and storage requirements
     from Phase 27's profiling (post-Phase 28's incremental-update
     optimization), calculate the real infrastructure cost (cloud compute
     pricing, or equivalent) of running the pipeline at target production
     scale.

2. Per-query cost calculation
   - Combine the resource cost baseline with the Phase 27/30 measured
     query volume and latency figures to calculate a real cost-per-query
     figure, broken down by pipeline stage (indexing/maintenance cost
     amortized per query, query resolution cost, S-MCP execution cost per
     invocation).

3. Multi-tenant cost allocation
   - Using the Phase 29 multi-tenant isolation work, calculate how
     shared infrastructure costs are fairly allocated across tenants at
     varying usage levels, so per-customer economics can be reasoned about
     individually.

4. Price-point sensitivity analysis
   - Model gross margin at several realistic customer price points (based
     on what comparable enterprise infrastructure typically charges),
     using the real cost-per-query figure, and identify at what price
     point and what usage volume the economics become viable.

5. Honest reporting
   - Report the resulting margin analysis plainly, including the scenario
     where the current cost structure does not support a viable price
     point at realistic customer usage volumes, if that is what the
     numbers show.

CONSTRAINTS:
- Every cost figure must be derived from the actual measured numbers in
  Phases 27-30, not from prototype-scale extrapolation or industry rule-
  of-thumb estimates.
- If the margin analysis reveals the current architecture's cost structure
  doesn't support a viable business at realistic price points, this must
  be flagged explicitly as a business-model problem requiring attention
  now, not smoothed over in the reporting.

DELIVERABLE: A cost model document with the full resource-cost baseline,
the per-query cost breakdown by pipeline stage, the multi-tenant
allocation methodology, and the price-point sensitivity analysis with an
honest statement of whether current economics are viable.
```

---

# GROUP G — Productization

## Phase 32 — Customer-Facing API/SDK

```
You are building the API and SDK layer that a customer's own engineering
team will actually integrate against, distinct from the internal
interfaces used within Groups A-F.

GOAL: Produce an API that a developer unfamiliar with ATLAS's internals
can successfully integrate using only the public documentation, with
proper authentication, versioning, and customer-appropriate error
handling.

BUILD THE FOLLOWING, IN THIS ORDER:

1. API surface design
   - Design a clean, minimal public API surface covering the operations a
     customer actually needs (submitting data for indexing, issuing
     queries, initiating a TIP cross-organization request, retrieving
     results), deliberately hiding internal implementation details (raw
     persistence diagrams, internal region references, etc.) that a
     customer's integration should never need to touch directly.

2. Authentication and authorization
   - Implement a standard authentication mechanism (API keys, OAuth, or an
     equivalent) with proper authorization scoping, so a customer's
     credentials can only access their own tenant's data and operations
     (building on the Phase 29 multi-tenant isolation).

3. Versioning
   - Implement explicit API versioning from the start, so future changes
     to the internal Groups A-F implementation don't silently break
     existing customer integrations.

4. Error handling
   - Replace internal debug-level error messages and stack traces with
     clear, customer-appropriate error responses that explain what went
     wrong and, where possible, how to fix it — without exposing internal
     implementation details that could aid an attacker or simply confuse
     an external developer.

5. External integration test
   - Have a developer who was not involved in building the internal
     system attempt to integrate against the API using only the public
     documentation (produced alongside this phase), and confirm they
     succeed without needing help from the internal team.

CONSTRAINTS:
- The external integration test in step 5 is a required gate for this
  phase, not optional — an API that only the people who built it can use
  correctly has not actually achieved this phase's goal.
- No internal error detail (stack traces, internal identifiers, raw
  system state) should ever be exposed through the public API's error
  responses.

DELIVERABLE: A repo with the public API/SDK implementation, the
authentication/authorization system, the versioning scheme, the
customer-appropriate error handling, and the documented results of the
external integration test.
```

---

## Phase 33 — Deployment & Installer Tooling

```
You are building the deployment tooling that lets a customer's own
infrastructure team stand up an ATLAS node in their own environment
independently, without your team doing it manually on their behalf.

GOAL: Prove a person outside your team can successfully deploy a working
ATLAS node using only the provided tooling and documentation, across more
than one target environment.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Installer/deployment package
   - Build deployment tooling (Helm charts for Kubernetes, or an
     equivalent packaging approach for the customer's likely
     infrastructure) that packages the Group A-D node components (already
     containerized per Phase 16) into an installable unit with clear
     configuration points.

2. Configuration and environment handling
   - Ensure the deployment tooling clearly exposes the configuration
     points a customer will actually need to set (data sources, resource
     limits, tenant identity, network settings) with sensible defaults and
     clear documentation for each.

3. Misconfiguration handling
   - Test common misconfiguration scenarios (missing required config
     values, invalid network settings, insufficient allocated resources)
     and confirm the deployment tooling produces clear, actionable error
     messages rather than silent failures or opaque crash logs.

4. Multi-environment validation
   - Test the deployment tooling across at least two meaningfully
     different target environments (e.g. two different cloud providers,
     or a cloud environment and an on-premise Kubernetes cluster) to
     confirm it isn't accidentally dependent on one specific setup's
     undocumented quirks.

5. External installation test
   - Have a person outside the founding/build team (ideally someone with
     general infrastructure experience but no ATLAS-specific knowledge)
     attempt a full installation using only the deployment tooling and its
     documentation, and confirm they succeed without needing direct help.

CONSTRAINTS:
- The external installation test in step 5 is the actual bar for this
  phase's completion — deployment tooling that "should work" based on
  code review alone has not met the bar.
- The multi-environment validation must use genuinely different target
  environments, not two superficially different configurations of the
  same underlying setup.

DELIVERABLE: A repo with the deployment/installer tooling, documented
configuration options, the misconfiguration-handling test results, the
multi-environment validation results, and the documented outcome of the
external installation test.
```

---

## Phase 34 — Documentation Suite

```
You are writing the complete customer-facing documentation suite, using
the real failure modes discovered across Groups A-F as the actual basis
for the troubleshooting content, rather than writing from imagination.

GOAL: Produce documentation thorough enough that a new team member — or a
customer — can get a working test environment running and diagnose common
problems using only the written material, no live support needed.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Setup guide
   - Write a step-by-step setup guide covering installation (using the
     Phase 33 tooling) through to running a first successful query,
     written for someone with general technical background but no prior
     ATLAS-specific knowledge.

2. API reference
   - Write a complete reference for the Phase 32 public API/SDK, covering
     every endpoint/method, its parameters, expected responses, and error
     conditions.

3. Troubleshooting guide — grounded in real history
   - Compile every real failure mode encountered across Groups A-F during
     development (data-quality issues from Phase 19, sandbox resource
     limit errors from Phase 9, misconfiguration issues from Phase 33,
     etc.) into a troubleshooting guide, with each entry describing the
     symptom, the likely cause, and the resolution — grounded in actual
     historical incidents, not speculative "things that might go wrong."

4. Version control and maintenance process
   - Keep all documentation in version control alongside the code it
     describes, with a defined process for updating documentation whenever
     related code changes (so documentation doesn't silently drift out of
     date as the system evolves).

5. New-team-member validation
   - Have someone who recently joined the team (or, if unavailable,
     someone deliberately kept away from the relevant internals) attempt
     to get a full test environment running using only this documentation,
     and confirm they succeed without needing verbal help.

CONSTRAINTS:
- The troubleshooting guide must be built from actual historical failure
  incidents documented across prior phases, not written from guessing at
  plausible failure modes.
- The new-team-member validation in step 5 is a required test of the
  documentation's actual quality, not an optional nicety.

DELIVERABLE: The complete documentation suite (setup guide, API reference,
troubleshooting guide grounded in real incident history) in version
control, the documented maintenance process for keeping it current, and
the results of the new-team-member validation test.
```

---

## Phase 35 — Onboarding Flow

```
You are building the first-time onboarding experience for a new customer,
designed and tested to work for a non-technical stakeholder, not just an
engineer.

GOAL: Prove that a real, non-technical stakeholder from a design partner
can complete onboarding and reach a first successful, meaningful result
without engineering hand-holding — this is a meaningfully different bar
than an engineer successfully completing the same flow.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Onboarding flow design
   - Design a guided onboarding experience (a setup wizard, a sample-data
     walkthrough, or an equivalent structured first-use experience) that
     takes a new user from initial access through to seeing a first
     meaningful, understandable result, without requiring them to
     understand the underlying manifold/TIP/S-MCP mechanics.

2. Sample data and guided walkthrough
   - Provide a safe, pre-loaded sample dataset and a guided walkthrough
     that demonstrates a realistic use case end-to-end, so a new user can
     see the system work before connecting their own real data.

3. Time-to-first-success measurement
   - Instrument the onboarding flow to measure time-to-first-successful-
     query (or equivalent meaningful milestone), so this can be tracked
     and improved over time rather than assumed to be reasonable.

4. Non-technical stakeholder test
   - Working within the Phase 18 agreement's relationship with the design
     partner, have one real non-technical stakeholder from that
     organization go through the onboarding flow, with engineering staff
     observing but not actively assisting unless the stakeholder is
     genuinely stuck.

5. Friction-point remediation
   - Document every point where the non-technical stakeholder hesitated,
     asked a question, or got stuck, and fix the underlying friction in
     the onboarding flow itself — not just answer the question verbally
     and move on without changing the product.

CONSTRAINTS:
- The non-technical stakeholder test in step 4 must be a genuine,
  minimally-assisted test — an engineer narrating each step defeats the
  purpose of testing whether the flow itself is self-explanatory.
- Friction points identified in step 5 must result in actual product
  changes, not just be logged as "future work" without follow-through.

DELIVERABLE: The onboarding flow implementation, the sample dataset and
guided walkthrough, the time-to-first-success measurement instrumentation,
documented results of the non-technical stakeholder test, and the specific
product changes made in response to identified friction points.
```

---

## Phase 36 — Support Process

```
You are establishing a real, working support process for customers,
tested end-to-end before it's actually needed under pressure.

GOAL: Prove that a support request can move through your actual intake,
triage, and resolution process successfully, with a distinct, faster path
for security-related issues specifically — not just have a process
described in a document that's never been tested.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Support intake setup
   - Set up a support-ticket intake system (even a lightweight one at this
     stage — a shared inbox or ticketing tool is sufficient) with a clear,
     customer-facing channel for submitting issues.

2. Triage and escalation process
   - Define a triage process for incoming tickets: severity classification,
     assigned ownership, and a defined (even if currently informal)
     response-time expectation per severity level.

3. Security-specific escalation path
   - Define a distinct, faster escalation path specifically for security-
     related reports (e.g. a suspected data-leakage report or a suspected
     sandbox-escape attempt), routing these directly to the team members
     responsible for the Group E hardening work rather than through
     standard support triage.

4. End-to-end test
   - File a test support ticket (both a standard issue and a simulated
     security-related issue) through the actual intake channel, and follow
     it through the complete triage, ownership assignment, and resolution
     process exactly as a real customer's ticket would move, timing each
     stage.

5. Response-time reality check
   - Compare the actual measured response times from the end-to-end test
     against the response-time expectations defined in step 2, and adjust
     the stated expectations to be realistic given current team size and
     actual demonstrated capacity, rather than aspirational numbers picked
     without testing.

CONSTRAINTS:
- The end-to-end test in step 4 must be run as an actual test through the
  real intake channel, not evaluated only on paper.
- Stated response-time expectations must be grounded in the step 5 reality
  check, not set independently of what was actually demonstrated to be
  achievable.

DELIVERABLE: The support intake and triage process documentation, the
distinct security-escalation path, the results of the end-to-end test
tickets (standard and security-simulated), and the response-time
expectations reconciled against actual measured performance.
```

---

# GROUP H — Go-to-Market & Steady State

## Phase 37 — Commercial Terms & Legal Conversion

```
You are converting the Phase 18-21 pilot relationship into a formal,
paying commercial relationship, grounded in the pilot's real, measured
results rather than the original roadmap's projected numbers.

WORK THROUGH THE FOLLOWING, IN THIS ORDER:

1. Results-based commercial proposal
   - Prepare a commercial proposal for the design partner using the actual
     Phase 20-21 pilot results (real accuracy numbers, real detected
     value) as the basis for the value proposition, rather than the
     original pre-pilot projections.

2. Pricing alignment with cost model
   - Set pricing terms informed directly by the Phase 31 cost model,
     confirming a real, positive margin exists at the proposed price and
     expected usage volume for this specific customer.

3. Contract drafting and legal review
   - Draft the commercial contract, covering service terms, data handling
     (building on the Phase 18 agreement and Phase 26 compliance
     documentation), SLA commitments (to be formalized in Phase 38), and
     term/renewal conditions, with full legal review before signature.

4. Signature and transition
   - Execute the signed agreement, and formally transition the
     relationship from "pilot" to "paying customer" status, including
     updating the multi-tenant deployment (Phase 29) to reflect the
     customer's production tenant configuration.

CONSTRAINTS:
- Commercial terms must be checked against the Phase 31 cost model before
  signature — do not sign an agreement whose pricing was set independently
  of the actual measured cost-per-query economics.

DELIVERABLE: A signed commercial agreement with the design partner, with
pricing and terms explicitly reconciled against the Phase 31 cost model
and the Phase 20-21 real pilot results.
```

---

## Phase 38 — SLA Definition & Monitoring

```
You are defining concrete service-level agreements with the now-paying
customer, and wiring the Phase 30 observability system into automatic
compliance tracking against those commitments.

BUILD THE FOLLOWING, IN THIS ORDER:

1. SLA definition
   - Define specific, numerical SLA commitments: uptime percentage, query
     latency thresholds (e.g. p99 under a stated value), and incident
     response-time commitments, informed by what Phase 27-30's real
     measurements show is actually achievable — not aspirational numbers
     set independently of measured performance.

2. Automatic compliance tracking
   - Wire the Phase 30 observability/metrics system into automatic SLA
     compliance tracking, so uptime, latency, and incident response times
     are measured continuously and compared against the defined SLA
     thresholds without manual after-the-fact calculation.

3. Customer-facing reporting
   - Build a simple reporting view the customer can access showing actual
     SLA compliance over time, so this isn't just an internal metric but a
     transparent, customer-visible commitment.

4. Deliberate breach test
   - Deliberately induce a controlled SLA-threshold breach in a test
     environment (e.g. artificially degrade latency beyond the defined
     threshold) and confirm the compliance-tracking system correctly
     detects and reports it, rather than assuming the tracking logic works
     without having tested it against an actual breach condition.

CONSTRAINTS:
- SLA thresholds must be set based on real Phase 27-30 measured
  performance data, not chosen independently and hoped to be achievable.
- The deliberate breach test in step 4 must be run and its detection
  confirmed — an SLA-tracking system that has never been tested against
  an actual breach is unverified.

DELIVERABLE: The defined SLA document, the automatic compliance-tracking
implementation wired to the Phase 30 observability system, the customer-
facing compliance reporting view, and the results of the deliberate breach
detection test.
```

---

## Phase 39 — Second Design Partner (Same Vertical)

```
You are repeating the real-data pilot process with a second design
partner in the same vertical, to determine whether the first pilot's
results generalize or were partly a one-off fit to that specific partner's
data and circumstances.

WORK THROUGH THE FOLLOWING, IN THIS ORDER:

1. Second-partner agreement
   - Repeat Phase 18's process with a new design partner in the same
     vertical (financial compliance), with its own data-sharing agreement
     and defined success criteria.

2. Repeat ingestion, benchmark, and protocol validation
   - Repeat Phases 19-21's process (real-data ingestion adaptation,
     benchmark re-run, TIP/S-MCP real-scenario validation) against this
     second partner's data.

3. Cross-partner comparison
   - Directly compare the second partner's results against the first
     partner's Phase 20-21 results: is the accuracy improvement similar in
     magnitude? Are the same real-data issues from Phase 19 recurring, or
     are there new ones specific to this partner?

4. Onboarding efficiency comparison
   - Measure how long the full pilot process (agreement through validated
     results) took for the second partner compared to the first, as a
     direct indicator of whether the Group D-G productization work
     actually improved onboarding speed and repeatability.

5. Generalization assessment
   - Write an honest assessment: does the system's value proposition hold
     up across two independent real customers, or were aspects of the
     first result specific to that partner's particular data
     characteristics? Identify anything that appears to be partner-
     specific rather than generally true.

CONSTRAINTS:
- The comparison in step 3-5 must be reported honestly, including if the
  second partner's results are meaningfully weaker than the first's — this
  finding matters more than a comfortable narrative of consistent success.

DELIVERABLE: A report comparing the second design partner's pilot results
against the first's, an assessment of onboarding-speed improvement, and an
honest evaluation of whether the value proposition generalizes across
independent customers in the same vertical.
```

---

## Phase 40 — Recurring Security & Benchmark Cadence

```
You are establishing the ongoing, recurring processes that keep the
one-time Phase 6 benchmark and Phase 25 security audit from becoming
stale, outdated claims as the system and the external field both continue
to evolve.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Recurring benchmark process
   - Establish a calendared, recurring process (e.g. quarterly or semi-
     annually) for re-running the Phase 6-style external benchmark against
     newer versions of the external dataset or newer competing retrieval
     approaches, with explicit ownership assigned for who runs this and
     when.

2. Recurring security review process
   - Establish a calendared, recurring cadence for security review
     (distinct from, and more frequent than, a full external audit like
     Phase 25) — for example, a lighter internal red-team refresh (re-
     running the Phase 24 suite against any system changes) on a shorter
     cycle, with periodic full external re-audits on a longer cycle.

3. First recurring cycle execution
   - Actually run the first scheduled instance of both the recurring
     benchmark and the recurring security review, and compare the results
     against the original Phase 6 and Phase 25 baselines, documenting any
     meaningful drift (positive or negative) in either direction.

4. Compliance documentation update
   - Update the Phase 26 compliance documentation package to reflect the
     established recurring cadence, so customers and their compliance
     teams can see this isn't a one-time claim but an ongoing commitment.

CONSTRAINTS:
- The recurring cadence must have explicit ownership and a real calendar
  entry, not just be a stated intention without an assigned owner or
  scheduled date.
- The first cycle in step 3 must actually be executed as part of this
  phase, not left as a future task — this phase isn't complete until at
  least one real recurring cycle has been run and compared against
  baseline.

DELIVERABLE: The documented recurring benchmark and security-review
cadence with assigned ownership, the results of the first executed cycle
of each compared against original baselines, and the updated compliance
documentation reflecting the ongoing commitment.
```

---

# GROUP I — Future Feature Expansion

## Phase 41 — Multi-Modal Manifold Indexing

```
You are extending ATLAS's Manifold-Core beyond text to support images and
structured tabular data within the same unified manifold index, as a
genuinely new capability beyond the original scope.

GOAL: Prove that images and tabular records can be embedded into the same
manifold space as text, and that cross-modal queries (a text query
retrieving relevant image or tabular results, or vice versa) produce
meaningful results, benchmarked against a modality-appropriate baseline.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Multi-modal embedding
   - Integrate established multi-modal or modality-specific embedding
     models (e.g. an image encoder producing embeddings in a space
     compatible with, or mappable to, the text embedding space from
     Phase 1) so images and tabular records can be embedded alongside
     text documents.

2. Unified manifold construction
   - Extend the Group A indexing pipeline to build a single Vietoris-Rips
     filtration and persistence structure across the combined, multi-
     modal point cloud, rather than maintaining separate indices per
     modality.

3. Cross-modal query testing
   - Construct hand-crafted test cases where a text query should
     meaningfully retrieve a relevant image or tabular record (and vice
     versa), and confirm the traversal mechanism from Phase 5 correctly
     surfaces these cross-modal connections.

4. Modality-appropriate benchmarking
   - Benchmark the multi-modal system against an appropriate existing
     baseline for cross-modal retrieval (not just the original text-only
     Phase 6 benchmark, which doesn't test this capability), reporting
     results honestly.

CONSTRAINTS:
- Cross-modal test cases must be hand-verified as genuinely meaningful
  connections before being used to validate the system, the same
  discipline applied in Phase 5 for text-only multi-hop cases.

DELIVERABLE: A repo extension with multi-modal embedding integration, the
unified manifold construction, the cross-modal test case validation
results, and the modality-appropriate benchmark comparison.
```

---

## Phase 42 — Distilled-Module Marketplace

```
You are building a registry allowing different organizations to publish
and reuse distilled S-MCP inference modules (not data) with each other,
extending the Sovereign-MCP execution model into a shared ecosystem.

GOAL: Prove organizations can safely discover and run each other's
published distilled modules, with cryptographic provenance verification
preventing a malicious or tampered module from being trusted.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Module registry design
   - Design a registry service where organizations can publish distilled
     S-MCP modules (per Phase 7-8's format) for common task types (e.g.
     standard fraud patterns, common anomaly types), with metadata
     describing the module's purpose, training provenance, and measured
     accuracy characteristics.

2. Provenance and signature verification
   - Implement cryptographic signing of published modules by their
     publishing organization, and verification by any host node before
     executing a module from the registry, building on the Phase 11
     attestation infrastructure.

3. Malicious upload test
   - Attempt to publish a tampered or maliciously modified module to the
     registry (or tamper with a legitimately published module in transit)
     and confirm the signature verification correctly rejects it before
     any host would execute it.

4. Cross-organization real usage test
   - Have two genuinely separate organizations (or simulated equivalents)
     publish and consume at least one real module through the registry,
     confirming the end-to-end discovery, verification, and execution flow
     works across organizational boundaries.

CONSTRAINTS:
- The malicious-upload rejection test in step 3 must be run and confirmed
  — a registry that doesn't verify provenance is a significant new attack
  surface, not a convenience feature.

DELIVERABLE: A repo with the module registry implementation, the
provenance/signature verification system, the malicious-upload rejection
test results, and the cross-organization real usage test results.
```

---

## Phase 43 — Cross-Cloud / Multi-Region Federation

```
You are extending ATLAS's TIP transport to reliably handle nodes running
in different cloud providers and geographic regions, rather than only the
same-datacenter conditions tested in Group C.

GOAL: Prove the TIP handshake succeeds reliably under realistic cross-
region network conditions (higher latency, occasional packet loss,
intermittent connectivity), not just the low-latency conditions of the
original simulation environment.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Cross-region test environment
   - Deploy the Group C node simulation (Phase 16-17) across genuinely
     different cloud regions or providers, rather than co-located
     containers, to introduce real network latency and variability.

2. Latency and reliability testing
   - Measure TIP handshake success rate and completion time under this
     real cross-region latency, comparing against the original Phase 15/17
     same-region baseline numbers.

3. Intermittent connectivity handling
   - Implement and test retry/backoff logic for handshakes affected by
     intermittent connectivity drops, confirming the protocol recovers
     gracefully rather than treating temporary network issues as
     permanent failures.

4. Regression check against Group C guarantees
   - Re-run the Phase 17-style data-leakage and forensic-replay checks in
     this cross-region deployment, confirming the original security
     properties still hold under the new network conditions.

CONSTRAINTS:
- Testing must occur under genuinely different network conditions (real
  cross-region deployment), not simulated latency injection alone, to
  capture real-world variability that synthetic latency simulation might
  miss.

DELIVERABLE: A report on cross-region handshake success rate and timing
compared to the same-region baseline, the retry/backoff implementation and
its test results under intermittent connectivity, and confirmation that
Group C's security properties still hold in this deployment configuration.
```

---

## Phase 44 — Homomorphic Encryption Exploration

```
You are investigating, as an open research question rather than a
committed feature, whether homomorphic encryption could provide a
stronger, more formal privacy guarantee for TIP matching than the current
LSH-plus-differential-privacy approach.

GOAL: Produce an honest feasibility assessment — this phase may
legitimately conclude the approach isn't practical yet, and that is a
valid and useful outcome, not a failure to be hidden.

WORK THROUGH THE FOLLOWING, IN THIS ORDER:

1. Approach research
   - Research existing homomorphic-encryption-based approaches to private
     similarity comparison, and assess which (if any) could plausibly
     apply to comparing the Phase 12 persistence-landscape vectors between
     two organizations without either seeing the other's raw vector.

2. Prototype implementation
   - If a plausible approach is identified, build a small prototype
     implementing homomorphic comparison of landscape vectors between two
     simulated nodes.

3. Performance cost measurement
   - Measure the computational and latency cost of the homomorphic
     approach directly against the existing Phase 13 LSH approach for the
     same comparison task, at a realistic vector size and dimensionality.

4. Formal privacy bound comparison
   - Compare what privacy guarantee the homomorphic approach can formally
     prove against what the current LSH-plus-differential-privacy approach
     (Phase 23) provides, being explicit about the difference between a
     formally provable bound and an empirically measured one.

5. Honest feasibility conclusion
   - Report a clear conclusion: is this approach practical to adopt given
     its performance cost relative to its privacy benefit, at this stage
     of the project? "Not practical yet, here's why" is an acceptable and
     useful conclusion.

CONSTRAINTS:
- The feasibility conclusion must be reported honestly regardless of
  outcome — a negative result here (this doesn't work well enough yet) is
  exactly as valuable to know as a positive one.

DELIVERABLE: A research report covering the approaches investigated, the
prototype (if one was built) and its measured performance cost against the
existing LSH approach, the formal privacy bound comparison, and an honest
feasibility conclusion.
```

---

## Phase 45 — Vertical-Specific Packaging (Healthcare)

```
You are adapting the productized system (Groups D-G) to a second industry
vertical — healthcare — building on the financial-services-proven approach
but with genuinely vertical-specific compliance and validation work, not a
copy-paste relabeling.

GOAL: Prove the core ATLAS mechanisms generalize to a meaningfully
different regulated domain, with compliance documentation and pilot
validation specific to healthcare's actual regulatory requirements.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Healthcare-specific compliance research
   - Research the actual regulatory requirements relevant to a healthcare
     use case (e.g. HIPAA data-handling requirements in a US context, or
     the equivalent relevant framework), and identify how they differ from
     the financial-services compliance work already done in Phase 26.

2. Use-case adaptation
   - Adapt the Group D real-data pilot process to a healthcare scenario
     (e.g. the multi-provider diagnosis pattern described earlier in
     ATLAS's design documents), identifying what data types and structural
     patterns differ meaningfully from the financial-transaction data
     already validated.

3. Compliance documentation
   - Produce a healthcare-specific compliance documentation package,
     genuinely adapted (not just relabeled) from the Phase 26 template to
     reflect healthcare's actual regulatory requirements and privacy
     concerns.

4. Pilot validation
   - Working with a real (or, if unavailable, a carefully constructed
     realistic simulated) healthcare design partner, repeat the Phase 18-21
     pilot process end-to-end for this new vertical.

CONSTRAINTS:
- The compliance documentation must be genuinely researched and adapted to
  healthcare-specific requirements — reusing financial-services compliance
  language without verifying it actually satisfies healthcare regulations
  would be a meaningful compliance risk, not just an aesthetic shortcut.

DELIVERABLE: The healthcare-specific compliance documentation package, the
adapted real-data pilot process and its results, and an assessment of
which core ATLAS mechanisms generalized directly versus which required
meaningful adaptation for this new vertical.
```

---

## Phase 46 — Self-Improving Manifold (Continual Index Learning)

```
You are prototyping a mechanism where the manifold's query-traversal
behavior improves over time based on real usage patterns, rather than
remaining static after the initial indexing in Group A.

GOAL: Prove that feeding real traversal-outcome feedback back into the
potential-field weighting genuinely improves retrieval quality over time,
measured against a fixed benchmark, without degrading performance on
unrelated queries.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Feedback signal design
   - Design a mechanism for capturing which traversal paths (from Phase 5)
     led to genuinely useful results, based on some measurable proxy for
     usefulness (e.g. explicit user feedback, or downstream task success
     if available).

2. Incremental weighting update
   - Implement a mechanism that adjusts the potential-field weighting
     (density and persistence-weight parameters from Phase 5) based on
     accumulated feedback signal, without requiring a full reindex of the
     underlying manifold structure.

3. Improvement measurement over time
   - Using the Phase 6 external benchmark as a fixed, stable measurement
     tool, track whether retrieval accuracy genuinely improves over
     successive rounds of simulated feedback, reporting the actual
     measured trend rather than assuming improvement occurs.

4. Regression testing on unrelated queries
   - Confirm that feedback-driven adjustments targeted at improving one
     category of query don't degrade performance on unrelated query
     categories, using a broad regression test set covering diverse query
     types.

CONSTRAINTS:
- Improvement must be measured against the fixed Phase 6 benchmark over
  time, not simply asserted based on the feedback mechanism's intuitive
  design — a feedback loop that doesn't demonstrably improve measured
  accuracy has not proven its value yet.

DELIVERABLE: A repo with the feedback-capture and incremental-weighting-
update implementation, the measured accuracy trend over successive
feedback rounds against the fixed benchmark, and the regression test
results confirming no degradation on unrelated query categories.
```

---

## Phase 47 — Edge/Mobile-Scale Node Deployment

```
You are investigating whether a lightweight version of the ATLAS node
stack can run on significantly more constrained hardware than a
datacenter environment, for use cases like an on-premise appliance for
smaller institutions.

GOAL: Produce an honest report on which components of the ATLAS stack can
run within a constrained resource envelope and which cannot, based on real
measurement on actual constrained hardware — not an estimate.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Constrained hardware target definition
   - Define a specific, concrete target hardware profile (e.g. a
     particular class of edge appliance or a specific consumer-grade
     device), rather than a vague "small footprint" goal.

2. Component-by-component profiling
   - Attempt to run each major component of the node stack (Group A
     indexing, Group B S-MCP sandbox, Group C TIP transport) on the actual
     target hardware, measuring real resource consumption and identifying
     which components fit comfortably, which require significant
     adaptation, and which don't fit at all within this profile.

3. Adaptation attempts
   - For components that don't fit as-is, attempt reasonable adaptations
     (further model compression, reduced index scope, simplified protocol
     handling) and re-measure whether the adapted version fits the target
     hardware profile.

4. Honest capability report
   - Report clearly which capabilities are preserved at edge scale, which
     are degraded, and which are not feasible at all on this hardware
     profile, so any future decision to pursue this direction is based on
     real evidence rather than an assumption that "smaller should just
     work."

CONSTRAINTS:
- All measurements must be taken on actual target hardware, not
  extrapolated from datacenter-scale measurements or theoretical resource
  requirement calculations.

DELIVERABLE: A report detailing real, measured resource usage of each
major node component on the defined constrained-hardware target, the
adaptation attempts and their results, and an honest assessment of which
capabilities are and are not feasible at edge scale.
```

---

## Phase 48 — Developer Plugin SDK

```
You are building a plugin SDK that lets third-party developers extend
ATLAS with custom distilled S-MCP modules or custom traversal strategies,
without requiring changes from your core team for every extension.

GOAL: Prove a genuinely external, third-party developer can build and run
a working plugin using only the SDK's public documentation, with the
plugin properly sandboxed so it cannot compromise the host system.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Plugin interface design
   - Design a stable, documented internal API surface that a third-party
     plugin can build against — for custom S-MCP inference modules (per
     Group B's format) or custom traversal-strategy logic (extending
     Phase 5's potential-field approach) — without needing access to
     ATLAS's full internal codebase.

2. Plugin sandboxing
   - Ensure third-party plugins run under the same category of resource
     capping and scoped access enforced in Phase 9-10 for S-MCP modules
     generally, so a poorly-built or malicious third-party plugin cannot
     exceed its intended boundaries or compromise the host.

3. SDK documentation
   - Write complete SDK documentation and at least one worked example
     plugin, sufficient for a developer with no prior ATLAS internals
     knowledge to build a new plugin from scratch.

4. External developer test
   - Have a genuinely external developer (not someone from your core
     team) attempt to build and run a working plugin using only the SDK
     documentation, and confirm they succeed without needing direct help
     from your team.

5. Adversarial plugin test
   - Write a deliberately poorly-behaved or malicious test plugin and
     confirm the sandboxing from step 2 correctly contains it, the same
     way Phase 9-10's adversarial tests confirmed containment for core
     S-MCP modules.

CONSTRAINTS:
- The external developer test in step 4 is the real bar for whether the
  SDK documentation succeeded — internal team members testing their own
  documentation are not a sufficient substitute.
- The adversarial plugin test in step 5 must be run and confirmed
  contained — this is a new attack surface (third-party code) and must
  meet the same containment bar as the core system.

DELIVERABLE: The plugin SDK and its interface design, the plugin
sandboxing implementation, the SDK documentation and worked example, the
results of the external developer test, and the adversarial plugin
containment test results.
```

---

## Phase 49 — Autonomous Multi-Agent Orchestration Layer

```
You are prototyping an orchestration layer allowing multiple AI agents to
issue coordinated, dependent queries across several ATLAS nodes
automatically, rather than one agent issuing one isolated query at a time.

GOAL: Prove multi-agent coordination can be handled with full auditability
end-to-end, and that a failure in one agent within a coordinated chain
doesn't silently corrupt another agent's results.

BUILD THE FOLLOWING, IN THIS ORDER:

1. Coordination model design
   - Design a model for expressing dependent, multi-step agent workflows
     (e.g. agent A's TIP query result informs the parameters of agent B's
     subsequent query), including how intermediate results are passed
     between coordinated agents.

2. Orchestration implementation
   - Implement the orchestration layer managing this coordinated
     execution, building on the existing Group C TIP protocol and Group B
     S-MCP execution as the underlying primitives each agent's individual
     actions use.

3. End-to-end audit logging
   - Ensure the full coordinated chain — not just each agent's individual
     actions in isolation — is logged in a way that allows reconstructing
     the entire multi-agent workflow after the fact: which agent triggered
     which subsequent action, and why.

4. Failure isolation test
   - Deliberately cause one agent within a coordinated chain to fail
     (crash, return invalid results, or time out) and confirm this failure
     is handled explicitly (the chain halts safely, or clearly reports the
     partial failure) rather than silently corrupting or being ignored by
     the other agents' subsequent actions.

CONSTRAINTS:
- The failure isolation test must be run and confirmed — coordinated
  multi-agent systems are particularly prone to silent failure propagation,
  and this must be explicitly tested, not assumed to be handled gracefully
  by the underlying components alone.

DELIVERABLE: The orchestration layer implementation, the end-to-end audit
logging covering the full coordinated workflow, and the failure isolation
test results confirming a failed agent doesn't silently corrupt the chain.
```

---

## Phase 50 — Continuous Roadmap Review

```
You are establishing the recurring process that replaces a fixed,
one-time roadmap with an ongoing, evidence-based review of what to build
next — this is a team process, not a coding task.

GOAL: Prove the team has a real, working process for evaluating proposed
future features against actual evidence before committing engineering
time to them, with at least one proposal genuinely rejected as proof the
process isn't just a rubber stamp.

WORK THROUGH THE FOLLOWING, IN THIS ORDER:

1. Review cadence establishment
   - Establish a recurring (e.g. quarterly) review meeting with clear
     ownership, where every proposed future feature or extension (in the
     spirit of Group I's phases) is evaluated before being greenlit as a
     committed phase.

2. Evaluation criteria
   - Define explicit evaluation criteria for proposed features, consistent
     with the discipline used throughout this roadmap: what evidence
     supports the proposed feature's value, what would disprove it, and
     what the minimal viable test of the idea would look like before full
     commitment.

3. First review cycle execution
   - Run the first actual review cycle against a real set of proposed
     future ideas (potentially including phases from Group I not yet
     built, or entirely new proposals from the team).

4. Documented rejection
   - Ensure at least one proposal is genuinely evaluated and rejected (or
     sent back for more evidence) based on the criteria from step 2, and
     document the reasoning, as concrete proof the review process has real
     teeth and isn't simply approving everything proposed.

CONSTRAINTS:
- The documented rejection in step 4 must be a genuine outcome of applying
  the evaluation criteria, not staged for appearance — if every single
  proposal in the first cycle happens to pass, that is worth questioning
  rather than treating as a coincidence.

DELIVERABLE: The documented recurring review cadence and its ownership,
the evaluation criteria, the results of the first review cycle, and the
documented reasoning behind at least one rejected or deferred proposal.
```
