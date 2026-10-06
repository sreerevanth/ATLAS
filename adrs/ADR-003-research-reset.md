# ADR-003: Evidence reset and research implementation

Status: accepted for research, 2026-10-06.

Restore corrected query-local TIP and fixed-grid landscapes. Historical image
comparisons refitted coordinate grids independently and cannot justify rejecting
landscapes. This supersedes ADR-001's representation decision and MASTER_PLAN's
sandbox deletion. ADR-002's representation/privacy separation remains useful;
its empirical MI and epsilon language is not an established bound.

Use a root Python package with Ripser, FAISS, Wasmtime and aioquic. Python hosts
deviate from proposed Rust hosts, not from actual QUIC or Wasm. Measure overhead.

Use Ripser's greedy furthest-point landmark VR as the first established
approximation. It is neither a witness complex nor truncated-radius exact VR.
Record covering radius and compare finite H0/H1 diagrams on identical inputs.
The additive bound can be uninformative in high-dimensional embeddings.
Speed does not imply preservation of useful features.

Reference: https://ripser.scikit-tda.org/en/latest/notebooks/Greedy%20Subsampling%20for%20Fast%20Approximate%20Computation.html

A failed retrieval comparison blocks a superiority claim, not publication of
a reproducible negative experiment. Release gates still require execution.
