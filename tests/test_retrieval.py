import numpy as np

from atlas.retrieval import ManifoldIndex, recall_at_k


def test_recall_accounts_for_missing_and_duplicate_results():
    assert recall_at_k([1, 2, 3], [1, 1, 9]) == 1 / 3


def test_zero_weight_traversal_equals_cosine():
    vectors = np.random.default_rng(42).normal(size=(50, 8)).astype("float32")
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    index = ManifoldIndex(vectors)
    query = vectors[4]
    expected = np.argsort(-(vectors @ query))[:5]
    found, trace = index.retrieve(query, 5, steps=2)
    np.testing.assert_array_equal(found, expected)
    assert trace["expansion"]
