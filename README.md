# Project ATLAS

ATLAS is a research implementation targeting v0.1.0, not a validated release candidate.
It investigates retrieval, query-local topology matching, and constrained WebAssembly execution.
It is not a production, clinical, or privacy-certified system. Previous claims
about benchmark gains, pilots, audits, zero leakage, differential privacy, and
production readiness are withdrawn because no reproducible evidence supports them.

The evidence-driven [Manifold-Core V2 report](docs/MANIFOLD_V2_REPORT.md) and
[fixed-configuration reproduction instructions](research/v2/README.md) supersede
the historical phase roadmap. The frozen V1 NO-GO result remains unchanged.
V2 defaults to the simpler method selected by validation, not to topology by design.
Do not overwrite the protected V1 artifacts or rerun parameter selection on final tests.

Start with the [forensic audit](docs/IMPLEMENTATION_AUDIT.md),
[research record](docs/RESEARCH_REPORT.md), and
[threat model](docs/THREAT_MODEL.md). Legacy code and reports are unverified
historical material. The requested PDF specifications are absent from this checkout;
Markdown substitutes are present.

## Archival V1 reproduction (use a new output directory)

The package lives in `src/atlas`. Python 3.12 is pinned as the reference minor
version. The checked-in `requirements-lock.txt` records exact installed versions.
Dataset, model and run artifacts are downloaded/generated locally and excluded
from Git.

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt
.venv/Scripts/python -m pip install --no-build-isolation -e .
.venv/Scripts/python -m pytest -q
.venv/Scripts/ruff.exe check src tests
.venv/Scripts/python -m atlas validate --output artifacts/local/validate
.venv/Scripts/python -m atlas corpus --output artifacts/local/v1-reproduction
.venv/Scripts/python -m atlas ann --output artifacts/local/v1-reproduction
.venv/Scripts/python -m atlas scaling --output artifacts/local/v1-reproduction
.venv/Scripts/python -m atlas handcrafted --output artifacts/local/handcrafted
.venv/Scripts/python -m atlas retrieval --output artifacts/local/v1-reproduction
.venv/Scripts/python -m atlas tip --output artifacts/local/tip
.venv/Scripts/python -m atlas integration --output artifacts/local/integration
.venv/Scripts/python -m atlas anomaly --output artifacts/local/anomaly
```

`corpus` downloads the pinned HotpotQA distractor validation split and a pinned
Sentence Transformers model. It samples questions with seed 42, records cleaning
decisions, creates embeddings, and checks repeatability on a fixed subsample.
Later commands consume its generated files. The retrieval evaluation uses pooled
distractor contexts and supporting-title retrieval; it is not the official fullwiki
setting and does not evaluate answer generation.

`scaling` compares Ripser exact Vietoris-Rips with its greedy landmark
approximation under time and memory limits. Landmark approximation is not a
witness complex. Read measured diagram errors and skipped runs before drawing
conclusions. `integration` is a synthetic loopback smoke test; certificate
verification is disabled in that demonstration. Hashes and signatures are not
privacy guarantees, and no differential privacy mechanism is implemented.

Do not use this research code with sensitive data. See the [threat model](docs/THREAT_MODEL.md).
