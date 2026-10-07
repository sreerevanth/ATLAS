# ADR 002: Independent Privacy Layer

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](../docs/HISTORICAL_MATERIAL.md).

## Context
Initial iterations of the Topology Interchange Protocol (TIP) implicitly coupled topological representations (e.g., Persistence Images) directly to Locality-Sensitive Hashing (LSH). The assumption was that the lossy compression of LSH naturally provided sufficient privacy obfuscation.

However, EXP-007 (Information Leakage) demonstrated a fundamental **Privacy-Retrieval Trade-off**. A 256-bit LSH array generated from a Persistence Image allowed simple linear models (Logistic Regression) to infer underlying dataset properties (number of clusters) with 52% accuracy. While shorter hashes (64-bit) mitigated this, relying purely on hash truncation couples retrieval utility directly to privacy loss.

## Decision
We formally separate the **Representation Layer** from the **Privacy Layer**. 

The new architectural flow for TIP signatures is:
1. **Topology** (e.g., Vietoris-Rips Complex)
2. **Representation** (e.g., Persistence Image)
3. **Privacy Layer** (e.g., Feature Selection, Randomized Projection, Differential Privacy)
4. **Signature Layer** (e.g., LSH)
5. **TIP Transmission**

## Rationale
- **Decoupling Concerns:** Privacy should be an engineered, mathematical guarantee (e.g., Differential Privacy bounds $\epsilon, \delta$), not an accidental side-effect of hash truncation.
- **Optimization:** This allows us to formally frame ATLAS as an optimization problem: `maximize Retrieval(b)` subject to `Leakage(b) <= epsilon`.
- **Future-Proofing:** Future research can improve any one layer independently. If a better topological representation or a stronger privacy mechanism is discovered, it can be swapped without invalidating the architecture.

## Consequences
- Requires designing and testing specific privacy mechanisms (e.g., Feature Dropout, Random Rotation, Laplace Noise) prior to LSH.
- Demands new experiments (EXP-011) to quantify the exact trade-off: How much retrieval utility is lost per unit of privacy gained?
- Leakage must now be measured via **Mutual Information** $MI(Hash; Property)$ rather than just attack accuracy, to provide model-agnostic security guarantees.
