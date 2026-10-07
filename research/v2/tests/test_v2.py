import numpy as np
import pytest

from research.v2.data import components
from research.v2.retriever import Retriever, landscape, matrix, metrics, topology, zscore
from research.v2.statistics import paired


def test_group_transitivity():
    records = [{"question": str(index), "support_keys": keys} for index, keys in
               enumerate([["a"], ["a", "b"], ["b"], ["c"]])]
    groups = components(records)
    assert groups[0] == groups[1] == groups[2]
    assert groups[3] != groups[0]


def test_metrics_not_title_count_or_duplicate_sensitive():
    assert metrics(["a", "a", "b"], ["a", "b"])["all@2"] == 0
    assert metrics(["a", "a", "b"], ["a", "b"])["recall@5"] == 1
    with pytest.raises(ValueError):
        metrics([], [])


def test_topology_circle_and_landscape():
    angles = np.linspace(0, 2*np.pi, 96, endpoint=False)
    points = np.column_stack((np.cos(angles), np.sin(angles))).astype(np.float32)
    assert topology(points)[0] > 1.3
    assert landscape(np.empty((0, 2))).shape == (64,)
    assert np.all(zscore(np.ones(10)) == 0)


def test_cosine_and_graph_zero_no_topology(monkeypatch):
    rng = np.random.default_rng(19)
    vectors = rng.normal(size=(150, 8)).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    index = Retriever(vectors, [{"key": str(node)} for node in range(len(vectors))])
    monkeypatch.setattr(index, "local_topology", lambda *args: pytest.fail("Unexpected topology"))
    methods = matrix()[:2]
    features = index.features(vectors[3], methods)
    expected = np.argsort(-(vectors @ vectors[3]))[:10].tolist()
    assert index.rank(features, methods[0])[1] == expected
    assert index.rank(features, methods[1])[1] == expected


def test_cluster_bootstrap_and_matrix():
    result = paired([1, 1, 0, 0], [0, 0, 0, 0], ["a", "a", "b", "b"])
    assert result["clusters"] == 2
    assert result["delta"] == .5
    assert result["ci"] == [0, 1]
    assert len({method["id"] for method in matrix()}) == len(matrix())


def test_primary_api_bypasses_experimental_modules(monkeypatch):
    from research.v2 import api
    monkeypatch.setattr(api, "Retriever", lambda *args: pytest.fail("Experimental path invoked"))
    vectors = np.eye(4, dtype=np.float32)
    documents = [{"key": str(node)} for node in range(4)]
    assert api.retrieve(vectors, documents, vectors[2], {"primary": matrix()[0]}, 1) == [2]
