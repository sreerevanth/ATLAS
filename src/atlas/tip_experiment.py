"""Empirical error rates for local landscape signatures on synthetic neighborhoods."""

import itertools

import numpy as np

from atlas.topology import agreement, landscape, persistence, signature


def _summary(truth, predicted):
    truth = np.asarray(truth, dtype=bool)
    predicted = np.asarray(predicted, dtype=bool)
    tp = int(np.sum(truth & predicted))
    fp = int(np.sum(~truth & predicted))
    tn = int(np.sum(~truth & ~predicted))
    fn = int(np.sum(truth & ~predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "fpr": fp / (fp + tn) if fp + tn else 0.0,
        "fnr": fn / (fn + tp) if fn + tp else 0.0,
    }


def experiment(config):
    rng = np.random.default_rng(config["seed"])
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    reference = np.column_stack((np.cos(angles), np.sin(angles)))
    unrelated = rng.uniform(-1, 1, reference.shape)
    noise_levels = (0.0, 0.03, 0.08, 0.15, 0.3)
    repeats = 20
    resolutions = (32, 64)
    bit_counts = (16, 32, 64)
    thresholds = (0.55, 0.65, 0.75, 0.85, 0.95)
    rows = []
    for resolution, bits, noise in itertools.product(resolutions, bit_counts, noise_levels):
        reference_vector = landscape(persistence(reference)["diagrams"], resolution=resolution)
        reference_hash = signature(reference_vector, bits=bits, seed=config["seed"])
        pairs = []
        for _ in range(repeats):
            positive = reference + rng.normal(0, noise, reference.shape)
            negative = unrelated + rng.normal(0, noise, unrelated.shape)
            positive_hash = signature(landscape(persistence(positive)["diagrams"], resolution=resolution), bits, config["seed"])
            negative_hash = signature(landscape(persistence(negative)["diagrams"], resolution=resolution), bits, config["seed"])
            pairs.extend(((True, agreement(reference_hash, positive_hash)),
                          (False, agreement(reference_hash, negative_hash))))
        for threshold in thresholds:
            rows.append({"resolution": resolution, "hyperplanes": bits, "noise_sigma": noise,
                         "threshold": threshold,
                         **_summary([same for same, _ in pairs], [score >= threshold for _, score in pairs]),
                         "positive_similarity": [score for same, score in pairs if same],
                         "negative_similarity": [score for same, score in pairs if not same]})
    return {"synthetic": True, "seed": config["seed"], "pairs_per_setting": repeats,
            "comparison": "same unit circle with additive isotropic Gaussian noise vs unrelated uniform square cloud",
            "warning": "Controlled synthetic signature characterization only; not privacy evidence or real-network TIP performance.",
            "rows": rows}
