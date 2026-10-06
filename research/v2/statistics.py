import numpy as np
from scipy.stats import binomtest

from .common import SEED


def paired(left, right, groups, confidence=.95):
    differences = np.asarray(left) - np.asarray(right)
    groups = np.asarray(groups)
    unique = sorted(set(groups))
    sums = np.asarray([differences[groups == group].sum() for group in unique])
    sizes = np.asarray([np.sum(groups == group) for group in unique])
    rng = np.random.default_rng(SEED)
    selections = rng.integers(0, len(unique), size=(5000, len(unique)))
    draws = sums[selections].sum(axis=1) / sizes[selections].sum(axis=1)
    question_draws = differences[rng.integers(0, len(differences), size=(5000, len(differences)))].mean(axis=1)
    tail = 100 * (1 - confidence) / 2
    wins, losses = int(np.sum(differences > 0)), int(np.sum(differences < 0))
    return {"n": len(differences), "clusters": len(unique), "delta": float(differences.mean()),
            "ci": np.percentile(draws, [tail, 100-tail]).tolist(), "confidence": confidence,
            "question_ci": np.percentile(question_draws, [tail, 100-tail]).tolist(),
            "wins": wins, "losses": losses, "ties": int(np.sum(differences == 0)),
            "mcnemar_exact_p_independent_questions": float(binomtest(wins, wins + losses).pvalue)
            if wins + losses else 1., "bootstrap_draws": 5000, "seed": SEED}


def summaries(rows):
    result = {}
    for method in sorted({row["method"] for row in rows}):
        selected = [row for row in rows if row["method"] == method]
        result[method] = {metric: {"mean": float(np.mean([row["metrics"][metric] for row in selected])),
                                   "std": float(np.std([row["metrics"][metric] for row in selected], ddof=1))}
                          for metric in selected[0]["metrics"]}
    return result
