"""Cosine baseline, HNSW measurements, and inspectable potential traversal."""

import time
import threading

import faiss
import numpy as np
import psutil

from atlas.topology import finite, persistence


def recall_at_k(expected, actual) -> float:
    if not len(expected):
        raise ValueError("Empty reference")
    return len(set(expected) & set(actual)) / len(set(expected))


def ann_benchmark(documents, queries, output, neighbors: int = 15):
    faiss.omp_set_num_threads(1)
    exact = faiss.IndexFlatIP(documents.shape[1])
    exact.add(documents)
    _, reference = exact.search(queries, neighbors)
    observations = []
    for links in (8, 16, 32):
        for construction in (40, 100):
            index = faiss.IndexHNSWFlat(documents.shape[1], links, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efConstruction = construction
            process = psutil.Process()
            baseline_rss = process.memory_info().rss
            peak_rss = [baseline_rss]
            stop = threading.Event()

            def sample_memory():
                while not stop.is_set():
                    try:
                        peak_rss[0] = max(peak_rss[0], process.memory_info().rss)
                    except psutil.NoSuchProcess:
                        return
                    stop.wait(0.002)

            monitor = threading.Thread(target=sample_memory, daemon=True)
            monitor.start()
            start = time.perf_counter()
            index.add(documents)
            duration = time.perf_counter() - start
            stop.set()
            monitor.join()
            peak_rss[0] = max(peak_rss[0], process.memory_info().rss)
            filename = output / f"hnsw-{links}-{construction}.index"
            faiss.write_index(index, str(filename))
            loaded = faiss.read_index(str(filename))
            for search in (16, 32, 64, 128):
                loaded.hnsw.efSearch = search
                loaded.search(queries[:1], neighbors)
                latency, recalls, retrieved = [], [], []
                for query, truth in zip(queries, reference, strict=True):
                    started = time.perf_counter()
                    _, found = loaded.search(query[None, :], neighbors)
                    latency.append((time.perf_counter() - started) * 1000)
                    recalls.append(recall_at_k(truth, found[0]))
                    retrieved.append(found[0].tolist())
                observations.append({
                    "M": links, "ef_construction": construction, "ef_search": search,
                    "k": neighbors, "recall": float(np.mean(recalls)),
                    "build_seconds": duration, "serialized_bytes": filename.stat().st_size,
                    "build_baseline_rss_bytes": baseline_rss,
                    "build_peak_rss_bytes": peak_rss[0],
                    "build_peak_rss_delta_bytes": max(0, peak_rss[0] - baseline_rss),
                    "latency_ms_quantiles": dict(zip(["p50", "p95", "p99"], np.percentile(latency, [50, 95, 99]).tolist(), strict=True)),
                    "query_latency_ms": latency, "per_query_recall": recalls,
                    "retrieved": retrieved,
                })
    return {"reference_neighbors": reference.tolist(), "observations": observations, "threads": 1}


class ManifoldIndex:
    def __init__(self, vectors, neighbors: int = 15, local_size: int = 24, landmarks=None):
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        self.neighbors = min(neighbors, len(vectors) - 1)
        self.local_size = min(local_size, len(vectors))
        self.index = faiss.IndexHNSWFlat(vectors.shape[1], 16, faiss.METRIC_INNER_PRODUCT)
        self.index.hnsw.efConstruction = 100
        self.index.hnsw.efSearch = 128
        self.index.add(self.vectors)
        self.exact = faiss.IndexFlatIP(vectors.shape[1])
        self.exact.add(self.vectors)
        scores, adjacency = self.index.search(self.vectors, self.neighbors + 1)
        self.graph = [row[row != position][:self.neighbors] for position, row in enumerate(adjacency)]
        self.density = scores[:, 1:].mean(axis=1)
        self.landmarks = landmarks
        self.weights = {}

    def topology_weight(self, node: int) -> float:
        if node not in self.weights:
            _, region = self.index.search(self.vectors[node:node + 1], self.local_size)
            diagram = persistence(self.vectors[region[0]], self.landmarks)["diagrams"][1]
            intervals = finite(diagram)
            self.weights[node] = float(np.max(intervals[:, 1] - intervals[:, 0], initial=0))
        return self.weights[node]

    def retrieve(self, query, count: int, alpha: float = 0, beta: float = 0, steps: int = 2,
                 titles=None):
        candidate_count = min(len(self.vectors), max(count * (4 if titles is not None else 1), 4))
        _, seeds = self.exact.search(query[None, :], candidate_count)
        candidates = set(map(int, seeds[0]))
        frontier = set(candidates)
        trace = []
        for step in range(steps):
            expanded = {int(neighbor) for node in frontier for neighbor in self.graph[node]}
            expanded -= candidates
            candidates |= expanded
            frontier = expanded
            trace.append({"step": step, "expanded": sorted(expanded)})
        scored = []
        for node in candidates:
            cosine = float(self.vectors[node] @ query)
            weight = self.topology_weight(node) if beta else 0.0
            potential = -(cosine + alpha * float(self.density[node]) + beta * weight)
            scored.append((potential, node, cosine, weight))
        scored.sort()
        selected = []
        seen_titles = set()
        for row in scored:
            if titles is not None:
                title = titles[row[1]]
                if title in seen_titles:
                    continue
                seen_titles.add(title)
            selected.append(row)
            if len(selected) == count:
                break
        return [row[1] for row in selected], {
            "expansion": trace,
            "ranking": [{"node": node, "potential": potential, "cosine": cosine, "persistence": weight}
                        for potential, node, cosine, weight in selected],
        }


def evaluate(documents, questions, vectors, queries, config):
    index = ManifoldIndex(vectors, local_size=config["local_size"])
    titles = [document["title"] for document in documents]
    modes = [("cosine", 0.0, 0.0, 0), ("graph_only", 0.1, 0.0, 2),
             ("topology_only", 0.0, 0.1, 0), ("atlas", 0.1, 0.1, 2),
             ("atlas_low_weight", 0.05, 0.05, 1), ("atlas_high_weight", 0.2, 0.2, 3)]
    rows = []
    for mode, alpha, beta, steps in modes:
        for question, query in zip(questions, queries, strict=True):
            started = time.perf_counter()
            retrieved, trace = index.retrieve(query, 10, alpha, beta, steps, titles=titles)
            latency = time.perf_counter() - started
            retrieved_titles = [documents[node]["title"] for node in retrieved]
            truth = set(question["support_titles"])
            metrics = {}
            for cutoff in (2, 5, 10):
                hits = truth & set(retrieved_titles[:cutoff])
                metrics[f"support_recall@{cutoff}"] = len(hits) / len(truth)
                metrics[f"all_support@{cutoff}"] = float(hits == truth)
            metrics["mrr@10"] = next((1 / rank for rank, title in enumerate(retrieved_titles, 1) if title in truth), 0)
            rows.append({"mode": mode, "question_id": question["id"], "type": question["type"],
                         "level": question["level"], "metrics": metrics, "retrieved": retrieved,
                         "support_titles": sorted(truth), "latency_seconds": latency, "trace": trace})
    summaries = {}
    for mode, *_ in modes:
        selected = [row for row in rows if row["mode"] == mode]
        summaries[mode] = {
            key: {"mean": float(np.mean([row["metrics"][key] for row in selected])),
                  "std_across_questions": float(np.std([row["metrics"][key] for row in selected], ddof=1))}
            for key in selected[0]["metrics"]
        }
    baseline = [row for row in rows if row["mode"] == "cosine"]
    compared = [row for row in rows if row["mode"] == "atlas"]
    differences = np.array([left["metrics"]["all_support@5"] - right["metrics"]["all_support@5"]
                            for left, right in zip(compared, baseline, strict=True)])
    rng = np.random.default_rng(config["seed"])
    means = np.array([rng.choice(differences, len(differences), replace=True).mean() for _ in range(2000)])
    groups = {}
    for key in sorted({(row["type"], row["level"]) for row in rows if row["mode"] == "cosine"}):
        for mode, *_ in modes:
            selected = [row for row in rows if row["mode"] == mode and (row["type"], row["level"]) == key]
            if selected:
                groups[f"{key[0]}::{key[1]}::{mode}"] = {
                    "n": len(selected),
                    "all_support@5": float(np.mean([row["metrics"]["all_support@5"] for row in selected])),
                    "support_recall@5": float(np.mean([row["metrics"]["support_recall@5"] for row in selected])),
                }
    return {"rows": rows, "summary": summaries, "breakdown_by_type_level": groups, "paired_primary": {
        "metric": "all_support@5", "delta": float(differences.mean()),
        "bootstrap_ci95": np.percentile(means, [2.5, 97.5]).tolist(),
        "bootstrap_unit": "question; shared source documents may induce dependence",
        "go": bool(np.percentile(means, 2.5) > 0),
    }, "topology_cache_nodes": len(index.weights)}
