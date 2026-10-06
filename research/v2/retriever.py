import time

import faiss
import numpy as np
from ripser import ripser

from .common import SEED, finite


def zscore(values):
    deviation = float(np.std(values))
    return (values - np.mean(values)) / deviation if deviation > 1e-8 else np.zeros_like(values)


def landscape(diagram):
    bars = finite(diagram)
    grid = np.linspace(0, 2, 32)
    if not len(bars):
        return np.zeros(64, dtype=np.float32)
    tents = np.maximum(0, np.minimum(grid[None, :] - bars[:, :1], bars[:, 1:] - grid[None, :]))
    ordered = np.sort(tents, axis=0)[::-1][:2]
    return np.pad(ordered, ((0, 2 - len(ordered)), (0, 0))).ravel().astype(np.float32)


def topology(points, landmarks=0):
    distances = np.sqrt(np.maximum(0, 2 - 2 * np.clip(points @ points.T, -1, 1)))
    np.fill_diagonal(distances, 0)
    result = ripser(distances, distance_matrix=True, maxdim=1,
                    n_perm=landmarks if 0 < landmarks < len(points) else None)
    bars = finite(result["dgms"][1])
    return (float(np.max(bars[:, 1] - bars[:, 0], initial=0)), landscape(result["dgms"][1]))


def matrix():
    methods = [{"id": "cosine", "graph": 0, "degree": 32, "topology": 0},
               {"id": "graph_zero", "graph": 0, "degree": 32, "topology": 0},
               {"id": "density", "graph": 0, "degree": 32, "topology": 0, "density": .1},
               {"id": "v1_raw_control", "graph": 0, "degree": 32, "topology": .1,
                "feature": "peak", "local": 32, "landmarks": 0, "raw": True, "density": .1}]
    graphs = [(degree, weight) for degree in (16, 32) for weight in (.1, .3)]
    for degree, weight in graphs:
        methods.append({"id": f"graph_d{degree}_w{weight}", "graph": weight,
                        "degree": degree, "topology": 0})
    for local, landmarks in ((16, 0), (16, 8), (32, 0), (32, 8), (32, 16)):
        for feature in ("peak", "landscape"):
            for topo_weight in (.05, .15):
                for degree, graph_weight in [(32, 0)] + graphs:
                    methods.append({"id": f"g{degree}_{graph_weight}_t{local}_{landmarks}_{feature}_{topo_weight}",
                                    "graph": graph_weight, "degree": degree, "topology": topo_weight,
                                    "feature": feature, "local": local, "landmarks": landmarks})
    for control in ("negative", "shuffled"):
        methods.append({"id": control, "graph": .1, "degree": 32, "topology": -.15 if control == "negative" else .15,
                        "feature": "landscape", "local": 32, "landmarks": 0, "shuffle": control == "shuffled"})
    return methods


class Retriever:
    def __init__(self, vectors, documents, ann=False, search=128, seed=17):
        faiss.omp_set_num_threads(1)
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        self.keys = [doc["key"] for doc in documents]
        self.exact = faiss.IndexFlatIP(vectors.shape[1])
        self.exact.add(self.vectors)
        self.index = self.exact
        if ann:
            self.index = faiss.IndexHNSWFlat(vectors.shape[1], 16, faiss.METRIC_INNER_PRODUCT)
            self.index.hnsw.rng = faiss.RandomGenerator(seed)
            self.index.hnsw.efConstruction = 100
            self.index.hnsw.efSearch = search
            self.index.add(self.vectors)
        _, found = self.index.search(self.vectors, 33)
        self.regions = found[:, :32]
        self.graph = np.asarray([row[row != node][:32] for node, row in enumerate(found)])
        self.density = np.mean(np.stack([np.sum(self.vectors * self.vectors[self.graph[:, index]], axis=1)
                                        for index in range(16)]), axis=0)
        self.cache = {}

    def local_topology(self, node, local, landmarks):
        key = (int(node), local, landmarks)
        if key not in self.cache:
            self.cache[key] = topology(self.vectors[self.regions[node, :local]], landmarks)
        return self.cache[key]

    def features(self, query, methods, query_seed=SEED):
        start = time.perf_counter()
        semantic_scores, top = self.index.search(query[None, :], 100)
        seeds = top[0, :5]
        candidates = np.unique(np.concatenate((top[0], self.graph[seeds].ravel())))
        semantic = self.vectors[candidates] @ query
        features = {"nodes": candidates, "semantic": semantic, "semantic_z": zscore(semantic),
                    "density": self.density[candidates],
                    "margin": float(semantic_scores[0, 0] - semantic_scores[0, 4])}
        seed_similarity = self.vectors[seeds] @ query
        for degree in (16, 32):
            graph = np.zeros(len(candidates), dtype=np.float32)
            for seed_node, relevance in zip(seeds, seed_similarity, strict=True):
                neighbors = set(self.graph[seed_node, :degree].tolist())
                edges = np.asarray([int(node) in neighbors and node != seed_node for node in candidates])
                values = np.maximum(0, self.vectors[candidates] @ self.vectors[seed_node]) * max(0, relevance)
                graph = np.maximum(graph, values * edges)
            features[f"graph_{degree}"] = zscore(graph)
        for local, landmarks in sorted({(method["local"], method["landmarks"])
                                       for method in methods if method["topology"]}):
            query_peak, query_landscape = topology(self.vectors[top[0, :local]], landmarks)
            values = [self.local_topology(node, local, landmarks) for node in candidates]
            peak = np.asarray([value[0] for value in values])
            similarity = -np.linalg.norm(np.stack([value[1] for value in values]) - query_landscape, axis=1)
            features[f"peak_{local}_{landmarks}"] = peak
            features[f"landscape_{local}_{landmarks}"] = similarity
            features[f"query_peak_{local}_{landmarks}"] = query_peak
        features["shuffle"] = np.random.default_rng(query_seed).permutation(len(candidates))
        features["seconds"] = time.perf_counter() - start
        return features

    def rank(self, features, method):
        scores = features["semantic"].copy() if method.get("raw") else features["semantic_z"].copy()
        scores += method["graph"] * features[f"graph_{method['degree']}"]
        if method.get("density"):
            values = features["density"]
            scores += method["density"] * (values if method.get("raw") else zscore(values))
        if method["topology"]:
            values = features[f"{method['feature']}_{method['local']}_{method['landmarks']}"]
            if method.get("shuffle"):
                values = values[features["shuffle"]]
            scores += method["topology"] * (values if method.get("raw") else zscore(values))
        ordered = np.lexsort((features["nodes"], -scores))
        keys, nodes, seen = [], [], set()
        for index in ordered:
            node = int(features["nodes"][index])
            key = self.keys[node]
            if key not in seen:
                seen.add(key)
                keys.append(key)
                nodes.append(node)
            if len(keys) == 10:
                break
        return keys, nodes


def metrics(ranking, support):
    truth = set(support)
    if not truth:
        raise ValueError("Empty support set")
    result = {}
    for cutoff in (2, 5, 10):
        hits = len(truth & set(ranking[:cutoff]))
        result[f"recall@{cutoff}"] = hits / len(truth)
        result[f"all@{cutoff}"] = float(hits == len(truth))
    result["mrr@10"] = next((1 / rank for rank, key in enumerate(ranking, 1) if key in truth), 0.)
    return result
