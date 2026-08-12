# EXP-003: Hyperparameter Sensitivity

## Objective
Determine whether the performance difference between representations observed in EXP-002 was simply an artifact of suboptimal default parameters. We need to compare the *best* Landscape against the *best* Image.

## Methodology
- **Grid Search:** Sweep resolutions, layers, sigmas, and bin sizes for each representation.
- **Noise Level:** Fixed at a challenging 20% noise to amplify performance differences.
- **Seeds:** 3 independent random seeds per configuration.
- **Target Metric:** Maximize Hash Agreement under noise.

## Goal
Give science a fair trial. If Landscapes still lose after being mathematically optimized, we can confidently update our ADR.
