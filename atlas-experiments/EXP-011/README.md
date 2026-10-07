# EXP-011: Differential Privacy Layer

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](../../docs/HISTORICAL_MATERIAL.md).

## Objective
Evaluate the impact of an independent privacy mechanism inserted between the Topological Representation (Persistence Image) and the Signature Layer (LSH).

## Threat Mitigated
As shown in EXP-007, macroscopic dataset properties (clusters, size, density) inherently leak into the LSH hash. This privacy layer aims to decouple the `Leakage(b) vs Retrieval(b)` trade-off by engineering privacy at the representation level.

## Mechanisms Tested
1. **Additive Noise:** Injecting Gaussian noise ($\sigma_{dp}$) directly into the Persistence Image matrix before hashing.
2. **Feature Dropout:** Randomly zeroing out a percentage of the Persistence Image pixels before hashing.

## Metrics
- **Retrieval:** Hash agreement on noisy datasets ($\sigma = 0.05$).
- **Leakage (MI):** Mutual Information (nats) between the 64-bit hash and the underlying number of clusters.
