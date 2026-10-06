"""A synthetic relational anomaly baseline with feature-only controls."""

import numpy as np
from sklearn.metrics import average_precision_score, precision_recall_fscore_support, roc_auc_score


def experiment(config):
    rng = np.random.default_rng(config["seed"])
    repetitions, group_size, anomaly_count = 40, 40, 6
    graph_scores, feature_scores, labels = [], [], []
    for _ in range(repetitions):
        count = 2 * group_size + anomaly_count
        groups = np.repeat([0, 1], group_size)
        adjacency = np.zeros((count, count), dtype=np.uint8)
        for left in range(2 * group_size):
            for right in range(left + 1, 2 * group_size):
                if groups[left] == groups[right] and rng.random() < 0.12:
                    adjacency[left, right] = adjacency[right, left] = 1
        anomalous = np.arange(2 * group_size, count)
        ring = np.roll(anomalous, -1)
        adjacency[anomalous, ring] = adjacency[ring, anomalous] = 1
        for offset, node in enumerate(anomalous):
            partner = group_size - 1 - offset % group_size if offset % 2 == 0 else offset % group_size
            adjacency[node, partner] = adjacency[partner, node] = 1
        degree = adjacency.sum(axis=1)
        triangles = np.diag(adjacency @ adjacency @ adjacency) / 2
        possible = degree * (degree - 1) / 2
        clustering = np.divide(triangles, possible, out=np.zeros(count, dtype=float), where=possible > 0)
        graph_scores.extend((1 - clustering).tolist())
        features = rng.normal(size=(count, 8))
        feature_scores.extend(np.linalg.norm(features - features.mean(axis=0), axis=1).tolist())
        labels.extend(([0] * (2 * group_size) + [1] * anomaly_count))
    y = np.asarray(labels)
    graph = np.asarray(graph_scores)
    feature = np.asarray(feature_scores)
    threshold = float(np.quantile(graph[y == 0], 0.95))
    predicted = graph >= threshold
    precision, recall, f1, _ = precision_recall_fscore_support(y, predicted, average="binary", zero_division=0)
    return {
        "synthetic": True,
        "seed": config["seed"],
        "repetitions": repetitions,
        "normal_nodes": 2 * group_size,
        "anomaly_nodes": anomaly_count,
        "construction": "two internally connected random blocks; planted cross-block cycle nodes with matched random features",
        "structural_score": "one minus local clustering coefficient",
        "threshold": threshold,
        "structural": {"precision": float(precision), "recall": float(recall), "f1": float(f1),
                       "auroc": float(roc_auc_score(y, graph)), "auprc": float(average_precision_score(y, graph))},
        "feature_only_random_control": {"auroc": float(roc_auc_score(y, feature)),
                                        "auprc": float(average_precision_score(y, feature))},
        "labels": y.tolist(), "structural_scores": graph.tolist(), "feature_scores": feature.tolist(),
        "warning": "Synthetic motif experiment only. It does not establish real-world fraud or anomaly detection capability.",
    }
