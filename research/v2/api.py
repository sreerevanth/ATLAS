import faiss
import numpy as np

from .retriever import Retriever


def retrieve(vectors, documents, query, frozen_configuration, count=10):
    if not 1 <= count <= 10:
        raise ValueError("This research API supports cutoffs 1 through 10")
    method = frozen_configuration["primary"]
    if not method["graph"] and not method["topology"] and not method.get("density"):
        faiss.omp_set_num_threads(1)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(np.ascontiguousarray(vectors, dtype=np.float32))
        _, candidates = index.search(np.asarray(query, dtype=np.float32)[None, :], len(vectors))
        selected, seen = [], set()
        for node in candidates[0]:
            key = documents[int(node)]["key"]
            if key not in seen:
                selected.append(int(node))
                seen.add(key)
            if len(selected) == count:
                break
        return selected
    index = Retriever(vectors, documents)
    features = index.features(query, [method])
    return index.rank(features, method)[1][:count]
