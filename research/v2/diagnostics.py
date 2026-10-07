import time

import numpy as np
from persim import bottleneck
from ripser import ripser
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits

from .common import OUT, ROOT, finite, intervals_json, manifest, read, write
from .experiment import load
from .retriever import Retriever, matrix, metrics
from .statistics import paired


def run_diagnostics():
    info = manifest(".venv-release/Scripts/python -m research.v2.run diagnostics")
    frozen = read(ROOT / "artifacts/local/research/retrieval.json")
    baseline = {row["question_id"]: row for row in frozen["rows"] if row["mode"] == "cosine"}
    findings = {}
    differences = []
    for mode in sorted({row["mode"] for row in frozen["rows"]}):
        rows = [row for row in frozen["rows"] if row["mode"] == mode]
        findings[mode] = paired([row["metrics"]["all_support@5"] for row in rows],
                                [baseline[row["question_id"]]["metrics"]["all_support@5"] for row in rows],
                                [row["question_id"] for row in rows])
        for row in rows:
            if mode == "atlas":
                expected = baseline[row["question_id"]]
                differences.append({"id": row["question_id"], "type": row["type"], "level": row["level"],
                                    "delta": row["metrics"]["all_support@5"] - expected["metrics"]["all_support@5"],
                                    "baseline_nodes": expected["retrieved"][:5], "atlas_nodes": row["retrieved"][:5],
                                    "ranking_trace": row["trace"]["ranking"][:5]})
    write(OUT / "v1-failure-analysis.json", {"original_paired_result": frozen["paired_primary"],
          "diagnostic_only": True, "mode_comparisons": findings, "query_differences": differences,
          "mechanism": "Exact cosine seeds already include semantic top10. Expansion alone cannot improve cosine ranking. Density and maximum H1 lifetime are query-independent additive bonuses, with no scale calibration or answer-generation evidence."})
    del frozen
    docs, questions, vectors, queries = load("hotpot", "dev")
    ann_rows, fidelity = [], []
    with threadpool_limits(limits=1):
        exact = Retriever(vectors, docs)
        _, truth = exact.exact.search(queries, 100)
        graph_method = next(method for method in matrix() if method["id"] == "graph_d32_w0.1")
        cosine = matrix()[0]
        reference = []
        for question, query in zip(questions, queries, strict=True):
            features = exact.features(query, [graph_method, cosine])
            reference.append({"cosine": metrics(exact.rank(features, cosine)[0], question["support_keys"]),
                              "graph": metrics(exact.rank(features, graph_method)[0], question["support_keys"])})
        for seed in (17, 29, 43):
            for search in (16, 64, 128):
                start = time.perf_counter()
                approx = Retriever(vectors, docs, ann=True, search=search, seed=seed)
                build = time.perf_counter() - start
                _, predicted = approx.index.search(queries, 100)
                observations = []
                for position, (question, query) in enumerate(zip(questions, queries, strict=True)):
                    features = approx.features(query, [graph_method, cosine])
                    observations.append({"id": question["id"], "neighbor_recall@100": len(set(predicted[position]) & set(truth[position])) / 100,
                                         "cosine": metrics(approx.rank(features, cosine)[0], question["support_keys"]),
                                         "graph": metrics(approx.rank(features, graph_method)[0], question["support_keys"]),
                                         "exact": reference[position]})
                ann_rows.append({"seed": seed, "ef_search": search, "build_and_graph_seconds": build,
                                 "neighborhood_recall@32": float(np.mean([len(set(first) & set(second)) / 32 for first, second in zip(exact.graph, approx.graph, strict=True)])),
                                 "query_recall@100": float(np.mean([row["neighbor_recall@100"] for row in observations])),
                                 "cosine_delta": float(np.mean([row["cosine"]["all@5"] - row["exact"]["cosine"]["all@5"] for row in observations])),
                                 "graph_delta": float(np.mean([row["graph"]["all@5"] - row["exact"]["graph"]["all@5"] for row in observations])),
                                 "observations": observations})
                print(f"HNSW seed={seed} ef={search} recall={ann_rows[-1]['query_recall@100']:.4f}", flush=True)
        for position in range(min(64, len(queries))):
            _, nodes = exact.exact.search(queries[position:position+1], 32)
            for local in (16, 32):
                points = vectors[nodes[0, :local]]
                distances = cdist(points, points)
                reference_topology = ripser(distances, distance_matrix=True, maxdim=1)
                for landmarks in (8, 16):
                    if landmarks >= local:
                        continue
                    approximate = ripser(distances, distance_matrix=True, maxdim=1, n_perm=landmarks)
                    fidelity.append({"id": questions[position]["id"], "local": local, "landmarks": landmarks,
                                     "reference": intervals_json(reference_topology["dgms"]), "approximate": intervals_json(approximate["dgms"]),
                                     "cover_radius": float(approximate["r_cover"]),
                                     "h1_bottleneck": float(bottleneck(finite(reference_topology["dgms"][1]), finite(approximate["dgms"][1]))),
                                     "reference_h1_count": len(reference_topology["dgms"][1]), "approximate_h1_count": len(approximate["dgms"][1])})
    info.update(ann=ann_rows, local_fidelity=fidelity)
    write(OUT / "diagnostics.json", info)
