# EXP-011: DP Layer Evaluation

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](../../../docs/HISTORICAL_MATERIAL.md).

| Mechanism | Parameter | Retrieval | Leakage (MI, nats) |
| --- | --- | --- | --- |
| Baseline | N/A | 97.19% | 0.5964 |
| Noise | 0.1 | 95.94% | 0.5791 |
| Noise | 0.5 | 83.44% | 0.5946 |
| Noise | 1.0 | 73.12% | 0.6016 |
| Noise | 2.0 | 56.25% | 0.5439 |
| Dropout | 0.1 | 89.38% | 0.5615 |
| Dropout | 0.3 | 75.94% | 0.5070 |
| Dropout | 0.5 | 68.44% | 0.4610 |
| Dropout | 0.8 | 55.94% | 0.5305 |
