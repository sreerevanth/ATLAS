# Manifold-Core V2

Experimental namespace separate from byte-protected V1. Read `PROTOCOL.md`,
`../../docs/MANIFOLD_V2_REPORT.md`, and all limitations before using a score.
Persistent topology is an experimental optional reranker, not an assumed benefit.
`api.retrieve(vectors, documents, query, frozen_configuration)` consumes normalized
float32 embeddings and document keys. It bypasses both graph and topology if the
locked primary configuration selects cosine. V1 CLI remains archival research;
do not overwrite `artifacts/local/research` or delete a final-test sentinel.

## Reference installation

Windows, Python3.12, CPU. Use a checkout with LF text (`core.autocrlf=false`) to
validate the original protected source-file byte inventory. Large ignored V1
artifacts are absent from a fresh clone; this is reported, not called verified.

```powershell
py -3.12 -m venv .venv-release
.venv-release/Scripts/python -m pip install -r research/v2/requirements-lock.txt
.venv-release/Scripts/python -m pip install --no-build-isolation -e .
.venv-release/Scripts/python -m pytest tests research/v2/tests -q
.venv-release/Scripts/ruff check src tests research/v2
```

## Reproduce the fixed final configuration, without retuning

Published evidence is already sealed. Use a NEW ignored output and cache directory;
do not regenerate files over published evidence. Missing V1 *artifacts* may be
allowed explicitly on a fresh clone; changed or missing tracked V1 source is
never accepted. The 1,500 V1 question exclusions are regenerated from pinned raw
HotpotQA and its original seed42 when its ignored questions cache is absent.

```powershell
$env:ATLAS_V2_EVIDENCE = "$PWD/artifacts/local/v2-replay-evidence"
$env:ATLAS_V2_CACHE = "$PWD/artifacts/local/v2-replay-cache"
$env:ATLAS_V2_ALLOW_MISSING_V1_ARTIFACTS = "1"
.venv-release/Scripts/python -m research.v2.run prepare
.venv-release/Scripts/python -m research.v2.run embed
.venv-release/Scripts/python -m research.v2.run gate
.venv-release/Scripts/python -m research.v2.run reproduce
```

Replay uses the published frozen methods, verifies identical question IDs and
splits, and permits one evaluation invocation in the new directory. It records
new environment, timings, vector hashes and outputs. Byte-identical numerical
embeddings across hardware/BLAS versions are not promised. `reproduce` is for
independent verification, NOT permission to select parameters using final scores.

## Original research sequence

The original commands below were run once through final in the default output
directory. The code and protocol were committed before runs, and
`evidence/frozen-config.json` was committed before `final`.

```powershell
.venv-release/Scripts/python -m research.v2.run prepare
.venv-release/Scripts/python -m research.v2.run gate
.venv-release/Scripts/python -m research.v2.run embed
.venv-release/Scripts/python -m research.v2.run dev
.venv-release/Scripts/python -m research.v2.run validation
.venv-release/Scripts/python -m research.v2.run diagnostics
.venv-release/Scripts/python -m research.v2.run scaling
.venv-release/Scripts/python -m research.v2.run freeze
git add research/v2/evidence/frozen-config.json
git commit -m "research: lock V2 configuration before held-out evaluation"
.venv-release/Scripts/python -m research.v2.run final
.venv-release/Scripts/python -m research.v2.run report
```

`report` recomputes metrics from raw rankings, checks split overlaps and provenance,
and generates tables and the scaling figure. It never retrieves or scores a new
test question. All110 development cells are reported, including controls and
losing cells. No post-validation method edits are part of this run. Before the
final freeze, source-only amendments added independent replay, stronger integrity
checks, reporting, and the primary API; these did not change ranking functions,
selection rules, or already executed development/validation results.

### Resource instrumentation correction

The original frozen scaling monitor missed the interpreter child of the Windows
virtualenv launcher. Its RSS values are invalid. Use the corrected process-tree
runner and publisher; the original source remains frozen for retrieval replay:

```powershell
.venv-release/Scripts/python -m tools.verify_v2_release measure
.venv-release/Scripts/python -m tools.verify_v2_release publish
```

The publisher consumes tracked `release-verification.json`; refreshing that
clean-clone verification uses `python -m tools.verify_v2_release verify` after preparing
an independent checkout at `artifacts/local/v2-clone-check`. No final retrieval
is executed by these three verification commands. See `evidence/INCIDENTS.md`.

## Data provenance

- HotpotQA: pinned Hugging Face `hotpotqa/hotpot_qa` revision and raw checksum in
  `evidence/prepare-manifest.json`; official dataset documentation:
  https://hotpotqa.github.io/ . Internal held-out split of public dev distractor,
  not official hidden test or fullwiki. License recorded as CC BY-SA4.0.
- MuSiQue: https://github.com/stonybrooknlp/musique (official project, CC BY4.0),
  answerable v1.0 dev file from pinned `bdsaglam/musique` mirror. Mirror SHA256 is
  checked. Bytes were not independently compared to the original Google Drive
  distribution; this provenance limitation is explicit.
- GUDHI weak witness construction:
  https://gudhi.inria.fr/python/3.12.0/witness_complex_ref.html . Squared-distance
  relaxation filtration is not the same as VR radius. Genuine witness results
  do not justify retrofitting the final retrieval configuration after selection.

Neither source-provided answer nor question decomposition text is embedded in
retrieval inputs. Decomposition length is used only for predefined MuSiQue
difficulty reporting. Text truncation at256 tokens, pretrained encoder exposure,
transductive corpus access and title/paragraph identity assumptions limit claims.
