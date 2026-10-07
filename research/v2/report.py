import json

import matplotlib
import numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .common import CACHE, OUT, ROOT, digest, manifest, protected, read, write
from .experiment import read_rows
from .retriever import metrics


def generate():
    info = manifest(".venv-release/Scripts/python -m research.v2.run report")
    locked = read(OUT / "frozen-config.json")
    final = read(OUT / "final-results.json")
    diagnostics = read(OUT / "diagnostics.json")
    scale = read(OUT / "scaling.json")
    v1 = read(OUT / "v1-failure-analysis.json")
    development = read(OUT / "hotpot-dev-summary.json")
    validation = read(OUT / "hotpot-validation-summary.json")
    signals = read(OUT / "topology-signals.json")
    selected = locked["selected"]
    groups = read(OUT / "hotpot-split.json")
    split_audit = {}
    for first, second in [("dev", "validation"), ("dev", "test"), ("validation", "test")]:
        left = [query for query in groups if query["split"] == first]
        right = [query for query in groups if query["split"] == second]
        split_audit[first + "_vs_" + second] = {
            "ids": len({query["id"] for query in left} & {query["id"] for query in right}),
            "groups": len({query["group"] for query in left} & {query["group"] for query in right}),
            "support_keys": len({key for query in left for key in query["support_keys"]} &
                                {key for query in right for key in query["support_keys"]})}
    assert all(value == 0 for row in split_audit.values() for value in row.values())
    verified = {}
    for name, split in [("hotpot", "dev"), ("hotpot", "validation"), ("hotpot", "test"), ("musique", "test")]:
        rows = read_rows(OUT / f"{name}-{split}-rows.json.gz")
        summary = read(OUT / f"{name}-{split}-summary.json")
        assert digest(OUT / f"{name}-{split}-rows.json.gz") == summary["raw_sha256"]
        assert len(rows) == summary["n"] * len(summary["methods"])
        assert len({(row["id"], row["method"]) for row in rows}) == len(rows)
        for row in rows:
            assert metrics(row["ranking"], row["support"]) == row["metrics"]
        for method in summary["methods"]:
            expected = np.mean([row["metrics"]["all@5"] for row in rows if row["method"] == method["id"]])
            assert abs(expected - summary["summary"][method["id"]]["all@5"]["mean"]) < 1e-12
        verified[f"{name}-{split}"] = {"rows": len(rows), "methods": len(summary["methods"]), "metrics_recomputed": True}
    for name, expected in locked["inputs"].items():
        assert digest(OUT / name) == expected
    assert final["source_sha256"] == locked["source_sha256"]
    started = read(OUT / "final-started.json")
    assert final["git_commit"] == started["git_commit"]
    assert final["frozen_config_sha256"] == digest(OUT / "frozen-config.json")
    data_integrity = {}
    for name, records in read(OUT / "embed-manifest.json")["results"].items():
        data_integrity[name] = {filename: digest(CACHE / name / filename) == checksum
                                for filename, checksum in records["files"].items()}
    assert all(all(row.values()) for row in data_integrity.values())
    info.update(split_overlap=split_audit, verified=verified, data_integrity=data_integrity,
                protected=protected(), final_sentinel_present=True,
                final_source_matches_frozen=True, final_inputs_match_frozen=True,
                limitations=["Same operator implemented and audited the experiment; not an independent external audit.",
                             "Transductive pooled distractor corpora, not fullwiki or official hidden test.",
                             "Encoder pretraining contamination and semantic near-duplicate leakage are not excluded.",
                             "Question/support grouping does not prove independence of all Wikipedia topics.",
                             "Final test exclusion is procedural and guarded by code, not a cryptographic access boundary.",
                             "Bootstrap intervals can be degenerate with no discordant outcomes; they do not prove equivalence.",
                             "One encoder, fixed corpus sample and limited held-out sizes; no universal negative conclusion."])
    write(OUT / "hostile-audit.json", info)
    topology_confirmed = all(result["topology_vs_graph"]["ci"][0] > 0 for result in final["results"].values())
    graph_confirmed = all(result["graph_vs_cosine"]["ci"][0] > 0 for result in final["results"].values())
    status = "B — PROMISING BUT MORE VALIDATION REQUIRED" if topology_confirmed else "C — CENTRAL HYPOTHESIS PARTIALLY SUPPORTED" if graph_confirmed else "D — CENTRAL HYPOTHESIS NOT SUPPORTED"
    lines = ["# Manifold-Core V2 evidence report", "", f"STATUS: {status}", "",
             "Generated exclusively from versioned raw rankings, manifests and measured topology artifacts.", "",
             "## Boundaries", "",
             "No replicated confirmatory topology improvement is established unless the adjusted intervals below exclude zero on both datasets. Failure to establish benefit is not proof of equivalence or impossibility. The selected primary path is `" + locked["primary"]["id"] + "`.", "",
             "Internal splits use held-out questions from public development data. This is not an official hidden-test or fullwiki score, and no answer generation was evaluated.", "",
             "## Provenance", "", "- Preregistered protocol: `research/v2/PROTOCOL.md`.",
             f"- Final experiment code commit: `{final['git_commit']}`.",
             f"- Frozen configuration SHA256: `{final['frozen_config_sha256']}`.",
             f"- Protected V1 files verified: {info['protected']['checked']}; changed: {len(info['protected']['changed'])}.",
             "- PR closure evidence: `docs/PR_CLOSURE.json`; accepted triage: `docs/PR_TRIAGE.md`.",
             "- Every result below links by file name into `research/v2/evidence/`.", "",
             "## Frozen V1 (diagnostic only)", "", "```json", json.dumps(v1["original_paired_result"], indent=2), "```", "",
             v1["mechanism"], "", "Per-question changes, including losses, are in `v1-failure-analysis.json`. V1 labels were not used for V2 parameter selection.", "",
             "## Development, validation, and final all-support@5", "",
             "| Dataset / split | n | Cosine | Selected graph | Topology only | Graph + topology |",
             "|---|---:|---:|---:|---:|---:|"]
    for label, summary in [("Hotpot dev", development), ("Hotpot validation", validation)] + [(name + " final", result["summary"]) for name, result in final["results"].items()]:
        values = [summary["summary"][selected[key]["id"]]["all@5"]["mean"] for key in ("cosine", "graph", "topology_only", "topology")]
        lines.append(f"| {label} | {summary['n']} | " + " | ".join(f"{value:.4f}" for value in values) + " |")
    lines += ["", "All support-recall@2/5/10, all-support@2/5/10, MRR@10 and question SDs are in the corresponding `*-summary.json`. Raw question IDs, retrieved document identities, support sets and metrics are in `*-rows.json.gz`.", "",
              "## Final uncertainty (paired shared-support-cluster bootstrap)", "",
              "Four confirmatory comparisons use Bonferroni 98.75% intervals. Question-bootstrap sensitivity intervals and exact McNemar p-values are recorded; the latter assume independent questions.", "",
              "| Dataset | Contrast | Delta | Adjusted CI | Wins / losses / ties | Clusters |", "|---|---|---:|---|---|---:|"]
    for name, result in final["results"].items():
        for key in ("graph_vs_cosine", "topology_vs_graph"):
            comparison = result[key]
            lines.append(f"| {name} | {key} | {comparison['delta']:.4f} | [{comparison['ci'][0]:.4f}, {comparison['ci'][1]:.4f}] | {comparison['wins']} / {comparison['losses']} / {comparison['ties']} | {comparison['clusters']} |")
    lines += ["", "Predefined difficulty subsets and topology-versus-cosine contrasts are exploratory, not additional confirmatory successes. Full subset counts and intervals: `final-results.json`.", "",
              "## Frozen architecture", "", "```json", json.dumps(locked["selected"], indent=2), "```", "",
              "Exact semantic seeds → one-hop similarity graph → standardized reranking → optional local H1 feature. Selection holds graph parameters fixed when assessing added topology. The primary API bypasses graph and topology entirely when cosine is selected; experimental modules remain available.", "",
              "## Complete development ablation matrix", "", "Every preregistered cell is included; development winners are not confirmatory evidence.", "",
              "| Method | All-support@5 | Support recall@5 | MRR@10 |", "|---|---:|---:|---:|"]
    for method, summary in sorted(development["summary"].items()):
        lines.append(f"| `{method}` | {summary['all@5']['mean']:.4f} | {summary['recall@5']['mean']:.4f} | {summary['mrr@10']['mean']:.4f} |")
    lines += ["", "## Query-local topology signal (development only)", "",
              "AUC is averaged within query where both classes exist; it is descriptive, not an independent causal effect. Correlation with semantic score diagnoses confounding. All candidate features and labels are retained in `dev-features.npz`; per-query statistics in `topology-signals.json`.", "",
              "| Feature | Mean candidate AUC | Mean cosine correlation | Mean zero fraction |", "|---|---:|---:|---:|"]
    for feature in sorted({row["feature"] for row in signals}):
        rows = [row for row in signals if row["feature"] == feature]
        auc = [row["auc"] for row in rows if row["auc"] is not None]
        correlation = [row["correlation_with_cosine"] for row in rows if row["correlation_with_cosine"] is not None]
        lines.append(f"| {feature} | {np.mean(auc):.4f} | {np.mean(correlation) if correlation else 0:.4f} | {np.mean([row['zero_fraction'] for row in rows]):.4f} |")
    lines += ["", "## HNSW isolation", "", "All primary V2 retrieval uses exact search; ANN cannot explain its held-out effect. This separate development-only diagnostic isolates approximation at fixed graph degree32, weight0.1. `diagnostics.json` retains every query outcome.", "",
              "| Seed | efSearch | Query recall@100 | Graph-neighbor recall@32 | Semantic all@5 delta | Graph all@5 delta |", "|---:|---:|---:|---:|---:|---:|"]
    for row in diagnostics["ann"]:
        lines.append(f"| {row['seed']} | {row['ef_search']} | {row['query_recall@100']:.4f} | {row['neighborhood_recall@32']:.4f} | {row['cosine_delta']:.4f} | {row['graph_delta']:.4f} |")
    lines += ["", "## Local topology fidelity", "", "| Neighborhood | Landmarks | Mean finite H1 bottleneck | Exact / approximate mean H1 count |", "|---:|---:|---:|---|"]
    for local, landmarks in ((16, 8), (32, 8), (32, 16)):
        rows = [row for row in diagnostics["local_fidelity"] if row["local"] == local and row["landmarks"] == landmarks]
        lines.append(f"| {local} | {landmarks} | {np.mean([row['h1_bottleneck'] for row in rows]):.5f} | {np.mean([row['reference_h1_count'] for row in rows]):.3f} / {np.mean([row['approximate_h1_count'] for row in rows]):.3f} |")
    lines += ["", "## Scaling and genuine witness investigation", "",
              "VR and greedy-landmark VR share a filtration axis; reported distances discard essential bars, whose counts are separately recorded. Weak witness uses GUDHI's squared-distance relaxation; its lifetimes are NOT compared numerically to VR lifetimes. It is a genuine complex with simplex counts, not a renamed landmark subsample. Passing synthetic gates does not establish retrieval usefulness.", "",
              "| Method | N | Landmarks | Seconds | Peak sampled RSS MiB | Simplices (if known) | Finite H1 bottleneck |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in scale["rows"]:
        distance = next((value["bottleneck_finite"] for value in row.get("fidelity", []) if value["dimension"] == 1), None)
        lines.append(f"| {row['method']} | {row['count']} | {row['landmarks']} | {row.get('seconds', 'stopped')} | {row['peak_sampled_rss_bytes']/1024**2:.1f} | {row.get('simplex_count')} | {distance} |")
    lines += ["", "Resource omissions: `" + json.dumps(scale["omitted"]) + "`.", "",
              "![Measured topology scaling](../research/v2/evidence/scaling.png)", "",
              "## Hostile audit / unsupported claims", ""]
    lines += ["- " + finding for finding in info["limitations"]]
    lines += ["- Do not claim general multi-hop superiority, useful topology signal, production readiness, clinical validation, FDA authorization, differential privacy, zero leakage, audited security, post-quantum security or zero knowledge from this work.",
              "- Supported: these implementations execute on the recorded CPU environment; synthetic topology gates pass; fixed, public-data, paired retrieval and fidelity measurements are reproducible within the stated setting.",
              "- Validation-selected fallback and final outcomes must remain visible even when development cells win.", "",
              "## Reproduction", "", "See `research/v2/README.md` for fixed-config replay and full pipeline commands. Do not remove the original final-test sentinel or overwrite frozen V1 artifacts.", ""]
    (ROOT / "docs/MANIFOLD_V2_REPORT.md").write_text("\n".join(lines), encoding="utf8")
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    for method in ("vr", "witness"):
        for landmarks in sorted({row["landmarks"] for row in scale["rows"] if row["method"] == method}):
            rows = sorted([row for row in scale["rows"] if row["method"] == method and row["landmarks"] == landmarks and not row["stopped"]], key=lambda row: row["count"])
            if not rows:
                continue
            label = f"{method} L={landmarks or 'exact'}"
            axes[0].plot([row["count"] for row in rows], [row["seconds"] for row in rows], "o-", label=label)
            axes[1].plot([row["count"] for row in rows], [row["peak_sampled_rss_bytes"]/1024**2 for row in rows], "o-", label=label)
    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("Input documents")
        axis.grid(alpha=.2)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Measured seconds")
    axes[1].set_ylabel("Peak sampled process RSS (MiB)")
    axes[1].legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(OUT / "scaling.png", dpi=160)
    plt.close(figure)
    write(OUT / "artifact-index.json", {str(path.relative_to(ROOT)): digest(path) for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "artifact-index.json" and path.suffix != ".log"})
    print(status, flush=True)
