# ADR-004: Evidence-gated V2 retrieval and genuine witness research

Status: accepted for the V2 research run; no production-readiness implication.

V1 is immutable. V2 lives in `research/v2`, with independent data splits and
manifests. Its exact semantic baseline avoids conflating HNSW approximation with
the value of graph or topology scores. Graph-conditioned topology ablations hold
graph parameters fixed. A committed preregistration and frozen configuration,
not the original TDA-centered roadmap, determine the primary retrieval path.

The preregistered validation gate did not admit graph or persistent topology.
The primary API therefore permits an exact cosine path with no graph construction
or PH computation. Optional graph and topology rerankers remain experimental.
Negative results do not justify keeping expensive machinery on a primary path.
Final outcomes do not retroactively change validation-based selection.

Greedy landmark VR is not a witness complex. V2 separately constructs GUDHI weak
witness complexes, validates them on deterministic synthetic data, and measures
their cost on real embedding prefixes. Their squared-relaxation filtration is not
directly comparable with VR radius, so no cross-axis bottleneck claim is made.
This investigation is not used to retune retrieval after validation.

Consequences: topology usefulness is an empirical question, not an architectural
axiom. Generalization beyond the fixed encoder, pooled distractor corpora and
internal public-dev splits requires further evidence. See the generated
`docs/MANIFOLD_V2_REPORT.md` and `research/v2/evidence/frozen-config.json`.
