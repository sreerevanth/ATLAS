"""Render public numeric claims directly from frozen, measured evidence."""

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/v2/evidence"
INPUTS = ["final-results.json", "frozen-config.json", "topology-signals.json",
          "diagnostics.json", "scaling-resource-corrected.json"]


def render():
    data = {name: json.loads((EVIDENCE / name).read_text(encoding="utf8")) for name in INPUTS}
    final = data["final-results.json"]
    locked = data["frozen-config.json"]
    selected = locked["selected"]
    scores = []
    for label, key in [("Cosine", "cosine"), ("Graph", "graph"), ("Topology only", "topology_only"), ("Graph + topology", "topology")]:
        values = [final["results"][dataset]["summary"]["summary"][selected[key]["id"]]["all@5"]["mean"] for dataset in ("hotpot", "musique")]
        scores.append(f"| {label} | {values[0]:.4f} | {values[1]:.4f} |")
    intervals = []
    for dataset, label in [("hotpot", "HotpotQA"), ("musique", "MuSiQue")]:
        for contrast, title in [("graph_vs_cosine", "Graph − cosine"), ("topology_vs_graph", "Added topology over graph")]:
            result = final["results"][dataset][contrast]
            intervals.append(f"| {label} | {title} | {result['delta']:+.4f} | [{result['ci'][0]:.4f}, {result['ci'][1]:.4f}] |")
    signals = data["topology-signals.json"]
    chosen = selected["topology"]
    feature = f"{chosen['feature']}_{chosen['local']}_{chosen['landmarks']}"
    semantic_auc = statistics.mean(row["auc"] for row in signals if row["feature"] == "semantic" and row["auc"] is not None)
    selected_auc = statistics.mean(row["auc"] for row in signals if row["feature"] == feature and row["auc"] is not None)
    selected_zero = statistics.mean(row["zero_fraction"] for row in signals if row["feature"] == feature)
    scales = data["scaling-resource-corrected.json"]["rows"]
    scale_table = []
    for method, count, landmarks, title in [("vr", 1000, 0, "Exact VR"), ("vr", 1000, 128, "Landmark VR"), ("vr", 5000, 128, "Landmark VR"), ("witness", 1000, 64, "Weak witness complex")]:
        row = next(row for row in scales if (row["method"], row["count"], row["landmarks"]) == (method, count, landmarks))
        scale_table.append(f"| {title} | {count:,} | {landmarks or '—'} | {row['seconds']:.2f} | {row['peak_sampled_rss_bytes']/1024**2:.1f} |")
    fidelity = next(row for row in scales if row["method"] == "vr" and row["count"] == 1000 and row["landmarks"] == 128)["fidelity"][1]
    ann = [row["query_recall@100"] for row in data["diagnostics.json"]["ann"] if row["ef_search"] == 128]
    text = f"""# ATLAS

**Experimental geometry-aware retrieval and privacy-oriented cross-organization computation.**

> **Research status · D — Central hypothesis not supported**
>
> The tested ATLAS graph/topology retrieval formulations did not establish an
> improvement over semantic retrieval on held-out multi-hop evaluation.
> This repository preserves the implementation, experiments, negative results,
> and reproducibility artifacts—not a claim that topology never works.

[Results](#results) · [Reproduce](#reproducibility) · [Full report](docs/MANIFOLD_V2_REPORT.md) · [Claims and limits](docs/CLAIMS.md)

## Why ATLAS?

Semantic similarity captures proximity, but not necessarily the relationships
needed to connect multiple pieces of evidence. ATLAS investigated whether graph
structure and persistent topology add useful signal beyond embedding similarity.

The research explored multi-hop retrieval, structural anomaly analysis,
privacy-oriented cross-organization matching, and sandboxed compute-to-data
workflows. These are research directions and executable prototypes, not solved
production capabilities. A useful outcome is knowing which measured additions
did **not** justify their complexity.

## Research question

**Can geometry, graph structure, or persistent topology improve retrieval beyond
semantic similarity?** The study implemented the hypothesis, tested controlled
ablations, and retained the negative held-out result.

## Architecture

```text
Documents → Embeddings → Semantic retrieval
                              ↓
                       Graph neighborhood
                              ↓
                       Topological features
                              ↓
                       Structural reranking
```

| Component | Research role | Current evidence boundary |
|---|---|---|
| **Manifold-Core** | Semantic candidates with optional graph/topology reranking | Held-out experiments did not establish improvement. Validation selected **cosine-only** as the primary V2 path. |
| **TIP** | Query-local topology signatures and organization-local region matching | Synthetic signature experiments and local QUIC integration; no privacy guarantee. |
| **S-MCP** | Signed, resource-constrained WebAssembly over a local region | Local Wasmtime execution and rejection tests; no independent security audit. |

The diagram is the investigated pipeline, not a requirement to retain every
stage. The [V2 API](research/v2/api.py) bypasses graph construction and persistent
homology when using its frozen cosine-only configuration. Experimental rerankers
remain available for inspection. [Architecture decision](adrs/ADR-004-v2-evidence-gated-retrieval.md)

## Experimental method

- **Data:** [HotpotQA](https://hotpotqa.github.io/) and
  [MuSiQue](https://github.com/stonybrooknlp/musique), with pinned downloads and checksums.
- **Separation:** HotpotQA internal development/validation/test sets are separated
  by shared-support components. Previously sampled V1 questions and supporting
  titles are excluded. MuSiQue is a transfer evaluation with no dataset-specific tuning.
- **Controls:** Identical corpora, embeddings, queries and metrics for cosine,
  graph, topology-only, and graph-plus-topology retrieval. All development cells
  are reported, including losing configurations and shuffled-feature controls.
- **Metric:** **all-support@5** is the fraction of questions for which all gold
  supporting documents occur in the first five results. HotpotQA uses supporting
  titles; MuSiQue uses normalized paragraph identities. No answer generation is evaluated.
- **Selection:** Development selects candidates; validation decides whether the
  added complexity is justified. Configuration is committed before a single
  final evaluation invocation. Paired uncertainty uses shared-support clusters.

These are pooled distractor-context corpora and **internal held-out subsets of
public development data**, not official hidden-test or fullwiki scores. The
unsupervised index sees the pooled corpus, including held-out context text.
Encoder pretraining contamination and semantic near-duplicates cannot be excluded.
See the [preregistered protocol](research/v2/PROTOCOL.md) for the exact boundaries.

## Results

**Held-out all-support@5** (higher is better):

| Method | HotpotQA (n={final['results']['hotpot']['summary']['n']}) | MuSiQue transfer (n={final['results']['musique']['summary']['n']}) |
|---|---:|---:|
{chr(10).join(scores)}

Development showed small apparent gains that did not generalize. The slightly
higher MuSiQue topology-only point estimate is not a replicated, established
advantage. The primary configuration remained the simpler semantic baseline.

**Paired differences and Bonferroni-adjusted 98.75% cluster-bootstrap intervals**
for the four confirmatory contrasts:

| Dataset | Contrast | Delta | Confidence interval |
|---|---|---:|---|
{chr(10).join(intervals)}

The predefined difficult subsets also did not establish replicated benefit.
Intervals that include zero are not evidence of equivalence. Full metrics,
question-level outcomes, standard deviations, sensitivity analyses, and all
ablations are in the [V2 report](docs/MANIFOLD_V2_REPORT.md).
The earlier **MANIFOLD_V1_NO_GO** experiment is preserved separately and was not
used as a V2 optimization target.

## Why didn't it work?

Measured development diagnostics help explain this particular formulation:

| Diagnostic | Measured value |
|---|---:|
| Semantic candidate AUC | {semantic_auc:.4f} |
| Selected persistence-feature candidate AUC | {selected_auc:.4f} |
| Selected persistence feature equal to zero | {selected_zero:.1%} |

AUC is averaged within queries having both classes; the zero rate is the mean
per-query candidate fraction. These are descriptive diagnostics, not independent
causal effects. The selected landmark-based persistence feature was mostly zero
and carried little discriminative signal in this setting. Query-independent
bonuses can displace semantically useful documents, while graph expansion alone
cannot improve an exact cosine ranking without changing the scoring rule.

Exact landscape features and other neighborhood/landmark settings were also
tested. Their inclusion in the full ablation matrix prevents the selected
representation's failure from being mistaken for a universal result about TDA.
[Raw signal diagnostics](research/v2/evidence/topology-signals.json)

## Topology scaling

Synthetic circle/noisy-circle and separated-cluster gates precede real embedding
topology. Exact and landmark VR were compared on identical inputs at overlapping
sizes; approximation scaling extended farther under explicit resource bounds.

| Method | Documents | Landmarks | Compute seconds | Peak process-tree RSS (MiB) |
|---|---:|---:|---:|---:|
{chr(10).join(scale_table)}

The speedup has a fidelity cost: at the matched VR comparison above, the largest
finite H1 lifetime changed from **{fidelity['exact_dominant']:.4f}** to **{fidelity['approx_dominant']:.4f}**.
Greedy landmark VR is **not** a witness complex. Genuine GUDHI weak-witness
measurements are separate: their squared-distance relaxation filtration is not
the VR distance filtration, so cross-axis diagram distances are not claimed.

![Measured topology runtime and process-tree memory](research/v2/evidence/scaling.png)

These are CPU measurements, not production-scale topology or hardware-acceleration
claims. RSS samples include the complete launcher/interpreter process tree and
may double-count shared pages or miss brief peaks. Earlier launcher-only RSS
measurements were invalidated; only the
[corrected measurements](research/v2/evidence/scaling-resource-corrected.json)
are used here. [Instrumentation record](research/v2/evidence/INCIDENTS.md)

## ANN validation

HNSW recall@100 was **{min(ann):.4f}–{max(ann):.4f}** at `efSearch=128` across
the recorded seeds. Lower search effort had larger approximation losses.
**Primary V2 experiments used exact retrieval**, isolating the negative result
from ANN approximation. [Per-query ANN evidence](research/v2/evidence/diagnostics.json)

## TIP: experimental topology interchange

TIP explores query → local neighborhood → persistent topology → landscape/vector
→ random-hyperplane hash → matching → organization-local region reference.
The prototype implements serialized messages, bounded in-memory protocol state,
replay rejection, scoped region grants and a local QUIC demonstration.

Executed tests include synthetic circle/noise signature comparisons and a local
OFFER → MATCH → EXECUTE → RESULT integration. These do **not** establish real-world
matching accuracy or privacy. Hashing is not zero knowledge. No differential
privacy mechanism or zero-leakage guarantee is implemented. Adaptive-query
leakage and membership inference remain uncharacterized.

The loopback demonstration disables TLS certificate verification and uses shared
HMAC credentials; it is not an authenticated institutional deployment.
[Threat model](docs/THREAT_MODEL.md)

## S-MCP: experimental compute-to-data

S-MCP executes an Ed25519-signed Wasm module against a copied, scoped local region
using Wasmtime. The implementation rejects imports/WASI and applies memory and
fuel limits; the local demonstration returns a bounded integer result.

Unit tests and local execution exercise these controls. They are not an
independent security audit and do not establish resistance to all side channels,
malicious authorized code, runtime vulnerabilities or deployment mistakes.
**Do not use these demonstrations with sensitive data.**

## Reproducibility

Reference environment: **CPython 3.12, Windows, CPU only**. Dependencies and model
revision are pinned. A fresh clone and isolated environment were tested. The
wheel contains the core `atlas` package; V2 research commands run from the checkout.

```powershell
git clone https://github.com/sreerevanth/ATLAS.git
cd ATLAS
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r research/v2/requirements-lock.txt
.venv/Scripts/python -m pip install --no-deps --no-build-isolation -e .
.venv/Scripts/python -m pytest tests research/v2/tests -q
.venv/Scripts/python -m atlas validate --output artifacts/local/readme-smoke
```

Replay the **published fixed configuration**, without tuning or replacing evidence:

```powershell
$env:ATLAS_V2_EVIDENCE = "$PWD/artifacts/local/readme-replay-evidence"
$env:ATLAS_V2_CACHE = "$PWD/artifacts/local/readme-replay-cache"
$env:ATLAS_V2_ALLOW_MISSING_V1_ARTIFACTS = "1"
.venv/Scripts/python -m research.v2.run prepare
.venv/Scripts/python -m research.v2.run embed
.venv/Scripts/python -m research.v2.run gate
.venv/Scripts/python -m research.v2.run reproduce
```

Use a new output directory for each independent reproduction. The missing-V1
option permits absent ignored historical caches on a fresh clone; it does not
permit changed protected files. The final-test sentinel prevents a second
evaluation in the same run directory. Never delete it to tune against test scores.

For non-Windows environments, use the appropriate Python 3.12 launcher,
`.venv/bin/python`, and shell environment-variable syntax. Native dependency and
platform availability must be checked; this snapshot does not claim validated
Linux/macOS execution. Full protocol, data provenance, resource corrections and
verification commands: [reproduction guide](docs/REPRODUCING.md).

## Repository structure

| Path | Purpose |
|---|---|
| `src/atlas/` | Frozen core library, CLI, local TIP and Wasm experiments |
| `research/v2/` | Preregistered V2 pipeline, optional rerankers and primary API |
| `research/v2/evidence/` | Versioned raw rankings, manifests, decisions and analyses |
| `tests/`, `research/v2/tests/` | Core and V2 regression tests |
| `configs/` | Core experiment configuration |
| `docs/` | Evidence reports, audits, claim boundaries and reproduction |
| `tools/` | Verification, publication and repository-integrity utilities |
| `.github/workflows/` | Automated research-package verification |

Older phase plans, specifications and paper drafts are preserved for attribution,
not promoted as current findings. [Historical-material index](docs/HISTORICAL_MATERIAL.md)

## Research artifacts

- [Manifold-Core V2 report](docs/MANIFOLD_V2_REPORT.md)
- [Implementation audit](docs/IMPLEMENTATION_AUDIT.md)
- [V1 research record](docs/RESEARCH_REPORT.md) — historical execution snapshot; its remaining-work list predates V2
- [Claims and limitations](docs/CLAIMS.md)
- [Accepted historical PR triage](docs/PR_TRIAGE.md)
- [Frozen configuration](research/v2/evidence/frozen-config.json)
- [Final results and experiment commit](research/v2/evidence/final-results.json)
- [Artifact/checksum index](research/v2/evidence/artifact-index.json)
- [Clean-clone and leakage checks](research/v2/evidence/release-verification.json)
- [Final repository verification](docs/FINALIZATION_VERIFICATION.json)

README numbers are generated from frozen artifacts by `python -m tools.render_readme`.
[Numeric provenance](docs/README_PROVENANCE.json) records the source hashes.

## What ATLAS established

- Reproducible graph/topology retrieval experimentation with controlled ablations.
- Synthetic topology validation and measured exact/approximate trade-offs.
- ANN validation against exact search.
- Held-out HotpotQA and MuSiQue transfer evaluation within the stated setting.
- Executable TIP/S-MCP prototypes with explicitly bounded local evidence.
- A negative retrieval result preserved rather than hidden.

## What ATLAS did not establish

- General retrieval superiority or production readiness.
- Differential privacy, zero knowledge, or zero leakage.
- Clinical validation or FDA/regulatory authorization.
- Real institutional deployment or an independent security audit.
- Production-scale topology, post-quantum security or measured accelerator benefit.

## Research conclusion

Within the tested ATLAS formulation, semantic similarity remained the strongest
general retrieval signal. Graph and persistent-topology reranking did not produce
a replicated held-out improvement. This does not establish that topology is
universally ineffective for retrieval; it establishes that **these tested
formulations did not support the original ATLAS hypothesis**.

## Citation

Cite the repository and the exact commit used. This is a research software
snapshot, not a claimed paper publication or DOI:

```bibtex
@misc{{atlas_research_2026,
  author = {{ATLAS contributors}},
  title = {{ATLAS: Geometry-Aware Retrieval Research}},
  year = {{2026}},
  howpublished = {{GitHub repository}},
  url = {{https://github.com/sreerevanth/ATLAS}}
}}
```

## License

**No repository-wide license file is present in this snapshot.** No new software
license or redistribution permission is asserted here; clarify licensing with
the repository owner before reuse. Third-party dependencies, models and datasets
retain their own terms. Dataset provenance and recorded licenses are documented
in the [V2 data notes](research/v2/README.md#data-provenance).
"""
    (ROOT / "README.md").write_text(text, encoding="utf8", newline="\n")
    provenance = {"generator": "tools/render_readme.py", "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "command": "python -m tools.render_readme", "experiment_commit": final["git_commit"],
                  "sources": {f"research/v2/evidence/{name}": hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() for name in INPUTS},
                  "readme_sha256": hashlib.sha256((ROOT / "README.md").read_bytes()).hexdigest()}
    (ROOT / "docs/README_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    render()
