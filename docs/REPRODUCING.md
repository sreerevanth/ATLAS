# Reproduction and verification

The sprint is complete. Reproduction means executing the published fixed
configuration—not choosing a new method using final-test outcomes. See the root
README for clone/install and fixed-config replay commands, and
`research/v2/PROTOCOL.md` for the unchanged scientific protocol.

## Environment

The recorded reference is CPython3.12 on Windows, CPU only. Install
`research/v2/requirements-lock.txt` for V2, including GUDHI; the core package alone
does not install every research dependency. The wheel provides `atlas` and its
CLI. V2 and repository verification modules run from a full checkout.

Cross-platform execution is not validated by the Windows results. On Unix-like
systems use an available Python3.12 interpreter, `.venv/bin/python`, and `export`
instead of PowerShell environment-variable assignments. Check native-library
wheel availability and preserve the same source, model, dataset and configuration.

## Small smoke tests (no held-out retrieval)

From an installed checkout, with a NEW output directory:

```powershell
.venv/Scripts/python -m pytest tests research/v2/tests -q
.venv/Scripts/python -m ruff check src tests research/v2 tools
.venv/Scripts/python -m atlas --help
.venv/Scripts/python -m atlas validate --output artifacts/local/check-core
.venv/Scripts/python -m atlas integration --output artifacts/local/check-integration
$env:ATLAS_V2_EVIDENCE = "$PWD/artifacts/local/check-v2"
$env:ATLAS_V2_ALLOW_MISSING_V1_ARTIFACTS = "1"
.venv/Scripts/python -m research.v2.run gate
```

The integration command is a synthetic loopback QUIC/Wasm demonstration with
certificate verification disabled; it is not deployment or privacy validation.
No type checker is configured for the current research package. Passing tests
and lint is not a substitute for the preserved scientific results.

## Frozen bytes, line endings and manifests

`docs/FINALIZATION_FREEZE.json` snapshots the protected V1 files and all tracked
V2 files before presentation cleanup. `docs/MANIFOLD_V1_NO_GO.sha256.json` remains
unchanged. `.gitattributes` disables text conversion for evidence so Git preserves
the exact bytes recorded in the manifests; protected source uses LF endings.
This fixes a checkout reproducibility hazard without changing measured values.

On the original research machine, including its ignored V1 artifacts:

```powershell
.venv/Scripts/python -m tools.finalization_checks verify --git-blobs
```

On a fresh clone, ignored V1 data, embeddings, indexes and generated egg-info may
be absent. The strict finalization checker reports missing files rather than
pretending to verify them. V2 replay's explicit missing-cache allowance covers
that case; it never permits a changed protected file. Dataset preparation can
reconstruct V1 question exclusions from the pinned public data and original seed.

`research/v2/evidence/artifact-index.json` enumerates the versioned V2 artifacts.
The artifact files and numeric results are not regenerated during cleanup.
`docs/README_PROVENANCE.json` connects README tables to those frozen inputs.

## Build and wheel verification

Do not build over the original protected generated egg-info. Build from a clean
temporary checkout or exported source tree instead:

```powershell
python -m build --no-isolation
python -m venv .wheel-check
.wheel-check/Scripts/python -m pip install -r research/v2/requirements-lock.txt
.wheel-check/Scripts/python -m pip install --no-deps dist/atlas_research-0.1.0-py3-none-any.whl
.wheel-check/Scripts/atlas --help
```

The finalization verification record captures actual commands, return codes,
outputs, installed package path, wheel checksum and smoke results. No wheel was
uploaded to PyPI and no GitHub Release was created.

The original research virtual environment has stale editable-package requirement
metadata. That diagnostic is recorded explicitly, not treated as a clean package
installation. Its frozen generated state is left intact. Release verification
uses a newly created environment, the current lock file and the built wheel,
and requires its dependency check and complete test suite to pass.

## Historical measurement corrections

Use `research/v2/evidence/scaling-resource-corrected.json`, not the original
launcher-only RSS measurements. The source comparison preserved all diagrams
while correcting process-tree monitoring. Frozen reports and instrumentation
incidents remain available. Finalization does not repeat scaling, retrieval,
hyperparameter search or final-test evaluation.

## Dataset and reuse terms

Downloads are pinned and checksum-verified by the data preparation code. MuSiQue
comes from a pinned mirror; its bytes were not independently checked against the
original Google Drive distribution. See `research/v2/README.md` for dataset/model
provenance. Dataset and dependency licenses do not grant a license to the ATLAS
repository itself; no repository-wide software license is currently present.
