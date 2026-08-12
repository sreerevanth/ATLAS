# EXP-002: Noise Robustness

## Objective
Determine how much perturbation each topological representation can tolerate before locality breaks.

## Methodology
- Noise levels: 0%, 1%, 2%, 5%, 10%, 20%, 30%, 50%
- Independent runs: 10
- Datasets: 5 synthetic topologies
- Metrics: Hash Stability, Runtime

## Goal
Try to break the EXP-001 preliminary evidence. If Landscapes survive this sweep, they are robust. If they break early, we need a new representation.
