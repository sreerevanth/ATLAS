"""Pre-benchmark chained retrieval fixtures required by the research protocol."""

import numpy as np

from atlas.retrieval import ManifoldIndex


def validate_chains(seed: int = 42):
    rng = np.random.default_rng(seed)
    results = []
    for case in range(5):
        angle = case * 0.17
        query = np.zeros(16, dtype=np.float32)
        query[:2] = (np.cos(angle), np.sin(angle))
        documents, vectors = [], []
        for title, offset, size in (("source", 0.0, 1), ("bridge", 0.42, 5), ("answer", 0.84, 20)):
            for item in range(size):
                direction = angle + offset + rng.normal(0, 0.006)
                vector = np.zeros(16, dtype=np.float32)
                vector[:2] = (np.cos(direction), np.sin(direction))
                vectors.append(vector)
                documents.append({"title": title, "text": f"Case {case} {title} record {item}"})
        basis = np.eye(16, dtype=np.float32)
        for item in range(16):
            vector = 0.9 * query + np.sqrt(1 - 0.9**2) * basis[2 + item % 14]
            vectors.append(vector)
            documents.append({"title": f"distractor-{item}", "text": f"Unrelated record {item}"})
        vectors = np.asarray(vectors)
        index = ManifoldIndex(vectors, neighbors=15, local_size=8)
        titles = [document["title"] for document in documents]
        baseline, _ = index.retrieve(query, count=3, steps=0, titles=titles)
        found, trace = index.retrieve(query, count=3, alpha=10.0, beta=0.0, steps=2, titles=titles)
        baseline_titles = {titles[node] for node in baseline}
        retrieved_titles = {titles[node] for node in found}
        expected = {"source", "bridge", "answer"}
        results.append({"case": case + 1, "expected_chain": ["source", "bridge", "answer"],
                        "cosine_titles": sorted(baseline_titles),
                        "traversal_titles": sorted(retrieved_titles),
                        "cosine_pass": baseline_titles == expected,
                        "traversal_pass": retrieved_titles == expected,
                        "retrieved_indices": found, "trace": trace})
    return {"seed": seed, "synthetic": True, "potential": "cosine + 10 * local mean neighbor cosine; two graph expansion steps",
            "cases": results, "all_pass": all(row["traversal_pass"] for row in results)}


def require_all_chains(seed: int = 42):
    result = validate_chains(seed)
    if not result["all_pass"]:
        failures = [row["case"] for row in result["cases"] if not row["traversal_pass"]]
        raise RuntimeError(f"Handcrafted retrieval gate failed in cases {failures}; external retrieval was not run")
    return result
