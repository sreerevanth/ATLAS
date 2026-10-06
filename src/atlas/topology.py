"""Validated H0/H1 persistence and fixed-grid landscapes."""

import numpy as np
from ripser import ripser


def persistence(points, landmarks: int | None = None) -> dict:
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or len(points) < 2 or not np.isfinite(points).all():
        raise ValueError("Expected at least two finite points")
    if landmarks is not None and not 2 <= landmarks <= len(points):
        raise ValueError("Invalid landmark count")
    result = ripser(points, maxdim=1, n_perm=landmarks)
    return {
        "diagrams": result["dgms"],
        "edges": int(result["num_edges"]),
        "cover_radius": float(result["r_cover"]),
        "landmark_indices": result["idx_perm"].tolist(),
    }


def finite(diagram):
    diagram = np.asarray(diagram).reshape(-1, 2)
    return diagram[np.isfinite(diagram).all(axis=1)]


def landscape(diagrams, resolution: int = 64, layers: int = 3, maximum: float = 2.0):
    if resolution < 2 or layers < 1 or maximum <= 0:
        raise ValueError("Invalid landscape grid")
    grid = np.linspace(0, maximum, resolution)
    output = []
    for diagram in diagrams:
        intervals = finite(diagram)
        if len(intervals) and (intervals[:, 0].min() < 0 or intervals[:, 1].max() > maximum):
            raise ValueError("Persistence diagram exceeds shared grid")
        tents = np.maximum(
            0, np.minimum(grid[None, :] - intervals[:, :1], intervals[:, 1:] - grid[None, :])
        )
        ordered = np.sort(tents, axis=0)[::-1]
        padded = np.zeros((layers, resolution))
        padded[: min(layers, len(ordered))] = ordered[:layers]
        output.append(padded.ravel())
    return np.concatenate(output)


def signature(vector, bits: int = 64, seed: int = 42) -> str:
    vector = np.asarray(vector, dtype=float)
    if vector.ndim != 1 or not np.isfinite(vector).all() or np.linalg.norm(vector) == 0:
        raise ValueError("Cannot hash a zero or invalid landscape")
    if bits < 1:
        raise ValueError("Hash length must be positive")
    projection = np.random.default_rng(seed).normal(size=(len(vector), bits))
    return "".join((vector @ projection > 0).astype(int).astype(str))


def agreement(first: str, second: str) -> float:
    if not first or len(first) != len(second) or set(first + second) - {"0", "1"}:
        raise ValueError("Expected equal-length binary signatures")
    return sum(left == right for left, right in zip(first, second, strict=True)) / len(first)


def ground_truth(seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    angles = np.linspace(0, 2 * np.pi, 100, endpoint=False)
    circle = np.column_stack((np.cos(angles), np.sin(angles)))
    cases = {"circle": circle, "noisy_circle": circle + rng.normal(0, 0.015, circle.shape)}
    observations = {}
    for name, cloud in cases.items():
        diagram = persistence(cloud)["diagrams"][1]
        lifetimes = diagram[:, 1] - diagram[:, 0]
        count = int((lifetimes > 0.5).sum())
        observations[name] = {"dominant_h1": count, "diagram": diagram.tolist()}
        if count != 1:
            raise AssertionError(f"Topology gate failed: {name}: {count}")
    clusters = np.vstack((rng.normal(0, 0.03, (40, 2)), rng.normal(3, 0.03, (40, 2))))
    diagram = persistence(clusters)["diagrams"][0]
    essential = int(np.isinf(diagram[:, 1]).sum())
    separated = int((finite(diagram)[:, 1] > 1).sum())
    observations["two_clusters"] = {
        "essential_h0": essential,
        "long_finite_h0": separated,
        "finite_diagram": finite(diagram).tolist(),
    }
    if (essential, separated) != (1, 1):
        raise AssertionError("Topology gate failed: two clusters")
    return observations
