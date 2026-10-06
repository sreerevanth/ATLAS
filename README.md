# Project ATLAS

ATLAS v0.1.0 is a reproducible research implementation of topology-aware
retrieval, query-local topology matching, and constrained WebAssembly execution.
It is not a production, clinical, or privacy-certified system. Previous claims
about benchmark gains, pilots, audits, zero leakage, differential privacy, and
production readiness are withdrawn because no reproducible evidence supports them.

Start with the [forensic audit](docs/IMPLEMENTATION_AUDIT.md),
[research record](docs/RESEARCH_REPORT.md), and
[threat model](docs/THREAT_MODEL.md). Legacy code and reports are unverified
historical material. The requested PDF specifications are absent from this checkout;
Markdown substitutes are present.

## Reproduction

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
.venv/Scripts/python -m atlas corpus --output artifacts/local/research
.venv/Scripts/python -m atlas ann --output artifacts/local/research
.venv/Scripts/python -m atlas scaling --output artifacts/local/research
.venv/Scripts/python -m atlas handcrafted --output artifacts/local/handcrafted
.venv/Scripts/python -m atlas retrieval --output artifacts/local/research
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
