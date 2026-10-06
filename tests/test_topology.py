import numpy as np
import pytest

from atlas.topology import agreement, ground_truth, landscape, persistence, signature


def test_known_topology():
    ground_truth()


def test_landscape_analytic_triangle_and_order():
    diagrams = [np.array([[0.0, 2.0], [0.5, 1.5]])]
    actual = landscape(diagrams, resolution=5, layers=2)
    np.testing.assert_allclose(actual, [0, 0.5, 1, 0.5, 0, 0, 0, 0.5, 0, 0])
    np.testing.assert_array_equal(actual, landscape([diagrams[0][::-1]], 5, 2))


def test_degenerate_hash_and_malformed_messages():
    with pytest.raises(ValueError):
        signature(np.zeros(10))
    for left, right in [("0", "00"), ("a", "b"), ("", "")]:
        with pytest.raises(ValueError):
            agreement(left, right)


def test_local_rng_does_not_modify_global_state():
    np.random.seed(123)
    expected = np.random.random(3)
    np.random.seed(123)
    signature(np.ones(10))
    np.testing.assert_array_equal(np.random.random(3), expected)


def test_landmark_full_size_equivalence():
    cloud = np.random.default_rng(42).normal(size=(30, 2))
    for exact, sampled in zip(
        persistence(cloud)["diagrams"], persistence(cloud, 30)["diagrams"], strict=True
    ):
        np.testing.assert_array_equal(exact, sampled)
