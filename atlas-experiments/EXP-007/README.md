# EXP-007: Information Leakage

> **Historical material — not current validation evidence.** Retained for design
> context, contributor attribution and provenance. Phase labels, figures and
> capability statements below are not current ATLAS claims. See the
> [current evidence and historical-material guide](../../docs/HISTORICAL_MATERIAL.md).

## Objective
Evaluate if the TIP hash leaks sensitive dataset properties to adversaries, starting with weak statistical attackers before progressing to ML models.

## Sub-Experiments Covered
- **EXP-007C (Property Inference):** Can an attacker predict the number of clusters from the hash?
- **EXP-007G (Signature-Length Trade-off):** Does increasing hash length from 32 to 128 bits increase privacy leakage?

## Threat Model (Attacker A1)
Attacker intercepts the hash and knows TIP uses Persistence Images. They train supervised models (Logistic Regression, Random Forest) on synthetic data to predict hidden properties (number of clusters).
