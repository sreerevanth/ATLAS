import gzip
import hashlib
import json
import time

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

from .common import CACHE, OUT, ROOT, digest, git, manifest, read, write
from .retriever import Retriever, matrix, metrics
from .statistics import paired, summaries


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            compressed.write(json.dumps(rows, separators=(",", ":"), allow_nan=False).encode())


def read_rows(path):
    with gzip.open(path, "rt", encoding="utf8") as stream:
        return json.load(stream)


def load(name, split):
    expected = read(OUT / "embed-manifest.json")["results"][name]["files"]
    for filename, checksum in expected.items():
        assert digest(CACHE / name / filename) == checksum, filename
    docs = read(CACHE / name / "documents.json")
    questions = read(CACHE / name / "questions.json")
    vectors = np.load(CACHE / name / "documents.npy")
    queries = np.load(CACHE / name / "queries.npy")
    indices = [index for index, query in enumerate(questions) if query["split"] == split]
    return docs, [questions[index] for index in indices], vectors, queries[indices]


def compare(rows, left, right, confidence=.95, subset=False):
    first = {row["id"]: row for row in rows if row["method"] == left and (not subset or row["difficult"])}
    second = {row["id"]: row for row in rows if row["method"] == right and (not subset or row["difficult"])}
    assert first.keys() == second.keys()
    if not first:
        return {"n": 0, "not_estimable": True}
    return paired([first[key]["metrics"]["all@5"] for key in first],
                  [second[key]["metrics"]["all@5"] for key in first],
                  [first[key]["group"] for key in first], confidence)


def evaluate(name, split, methods):
    assert read(OUT / "topology-gate.json")["vr_passed"]
    docs, questions, vectors, queries = load(name, split)
    started = time.perf_counter()
    index = Retriever(vectors, docs)
    rows, signals, feature_archive = [], [], {}
    for position, (question, query) in enumerate(zip(questions, queries, strict=True)):
        query_seed = int(hashlib.sha256(question["id"].encode()).hexdigest()[:8], 16)
        features = index.features(query, methods, query_seed)
        difficult = (question["type"] == "bridge" and features["margin"] < .10) if name == "hotpot" else int(question["level"]) >= 3
        for method in methods:
            ranking, nodes = index.rank(features, method)
            rows.append({"id": question["id"], "group": question["group"], "method": method["id"],
                         "type": question["type"], "level": question["level"], "difficult": difficult,
                         "metrics": metrics(ranking, question["support_keys"]), "ranking": ranking,
                         "nodes": nodes, "support": question["support_keys"],
                         "shared_feature_seconds": features["seconds"]})
        if split == "dev":
            labels = np.asarray([index.keys[node] in question["support_keys"] for node in features["nodes"]], dtype=int)
            feature_archive[f"{position}_nodes"] = features["nodes"]
            feature_archive[f"{position}_labels"] = labels
            for key, values in features.items():
                if key.startswith(("peak_", "landscape_")) or key in ("semantic", "density", "graph_32"):
                    feature_archive[f"{position}_{key}"] = values
                    has_variance = np.std(values) > 1e-8
                    signals.append({"id": question["id"], "feature": key,
                                    "auc": float(roc_auc_score(labels, values)) if len(set(labels)) == 2 else None,
                                    "correlation_with_cosine": float(spearmanr(values, features["semantic"]).statistic)
                                    if has_variance else None,
                                    "std": float(np.std(values)), "zero_fraction": float(np.mean(values == 0)),
                                    "candidate_support_recall": float(len(set(question["support_keys"]) &
                                                                          {index.keys[node] for node in features["nodes"]}) / len(set(question["support_keys"])))})
        if position % 25 == 0:
            print(f"{name} {split}: {position}/{len(questions)}, topology cache {len(index.cache)}", flush=True)
    filename = OUT / f"{name}-{split}-rows.json.gz"
    write_rows(filename, rows)
    result = {"dataset": name, "split": split, "n": len(questions), "methods": methods,
              "summary": summaries(rows), "wall_seconds": time.perf_counter() - started,
              "raw": str(filename.relative_to(ROOT)), "raw_sha256": digest(filename),
              "topology_cached_regions": len(index.cache), "ids": [question["id"] for question in questions]}
    write(OUT / f"{name}-{split}-summary.json", result)
    if split == "dev":
        write(OUT / "topology-signals.json", signals)
        np.savez_compressed(OUT / "dev-features.npz", **feature_archive)
    return rows, result


def dev():
    info = manifest(".venv-release/Scripts/python -m research.v2.run dev")
    methods = matrix()
    write(OUT / "matrix.json", methods)
    with threadpool_limits(limits=1):
        rows, result = evaluate("hotpot", "dev", methods)
    graph_options = [method for method in methods if method["id"].startswith("graph_d")]
    graph = min(graph_options, key=lambda method: (-result["summary"][method["id"]]["all@5"]["mean"], method["id"]))
    topology_options = [method for method in methods if method["id"].startswith("g") and method["topology"] > 0
                        and method["graph"] == graph["graph"] and method["degree"] == graph["degree"]]
    topology_method = min(topology_options, key=lambda method: (-result["summary"][method["id"]]["all@5"]["mean"], method["id"]))
    topology_only = next(method for method in methods if method["graph"] == 0 and method["topology"] == topology_method["topology"]
                         and all(method.get(key) == topology_method[key] for key in ("feature", "local", "landmarks")))
    selected = {"cosine": methods[0], "graph": graph, "topology_only": topology_only, "topology": topology_method}
    info.update(selected=selected, comparisons={method["id"]: compare(rows, method["id"], "cosine") for method in methods},
                raw_sha256=result["raw_sha256"])
    write(OUT / "dev-selection.json", info)
    print({"selected": selected}, flush=True)


def validation():
    info = manifest(".venv-release/Scripts/python -m research.v2.run validation")
    selected = read(OUT / "dev-selection.json")["selected"]
    with threadpool_limits(limits=1):
        rows, result = evaluate("hotpot", "validation", list(selected.values()))
    info.update(summary=result, graph_vs_cosine=compare(rows, selected["graph"]["id"], "cosine"),
                topology_vs_graph=compare(rows, selected["topology"]["id"], selected["graph"]["id"]))
    write(OUT / "validation-decision.json", info)
    print({key: info[key] for key in ("graph_vs_cosine", "topology_vs_graph")}, flush=True)


def freeze():
    info = manifest(".venv-release/Scripts/python -m research.v2.run freeze")
    if (OUT / "final-started.json").exists() or (OUT / "frozen-config.json").exists():
        raise RuntimeError("Refuse to replace frozen configuration")
    decision = read(OUT / "validation-decision.json")
    selected = read(OUT / "dev-selection.json")["selected"]
    graph_accepted = decision["graph_vs_cosine"]["ci"][0] > 0 and decision["graph_vs_cosine"]["delta"] >= .02
    topology_accepted = graph_accepted and decision["topology_vs_graph"]["ci"][0] > 0 and decision["topology_vs_graph"]["delta"] >= .02
    primary = selected["topology"] if topology_accepted else selected["graph"] if graph_accepted else selected["cosine"]
    info.update(selected=selected, primary=primary, graph_accepted=graph_accepted, topology_accepted=topology_accepted,
                inputs={name: digest(OUT / name) for name in ("dev-selection.json", "validation-decision.json", "hotpot-split.json", "musique-split.json", "embed-manifest.json", "matrix.json")})
    write(OUT / "frozen-config.json", info)
    print({"primary": primary, "graph_accepted": graph_accepted, "topology_accepted": topology_accepted}, flush=True)


def final(replica=False):
    info = manifest(".venv-release/Scripts/python -m research.v2.run " + ("reproduce" if replica else "final"))
    published = ROOT / "research/v2/evidence"
    if replica:
        assert OUT != published.resolve(), "Replay must not overwrite published evidence"
        locked = read(published / "frozen-config.json")
        for name in ("hotpot-split.json", "musique-split.json"):
            assert read(OUT / name) == read(published / name), "Replay dataset/split drift"
        write(OUT / "frozen-config.json", locked)
    else:
        locked = read(OUT / "frozen-config.json")
    tracked = git("ls-files", "--error-unmatch", "research/v2/evidence/frozen-config.json")
    assert tracked and not git("status", "--porcelain", "--", "research/v2/evidence/frozen-config.json")
    assert info["source_sha256"] == locked["source_sha256"], "Post-freeze source change"
    if not replica:
        for name, expected in locked["inputs"].items():
            assert digest(OUT / name) == expected, name
    info["independent_fixed_config_replay"] = replica
    info["frozen_config_sha256"] = digest(OUT / "frozen-config.json")
    with (OUT / "final-started.json").open("x", encoding="utf8") as stream:
        json.dump(info, stream, indent=2)
    selected = locked["selected"]
    results = {}
    with threadpool_limits(limits=1):
        for name in ("hotpot", "musique"):
            rows, summary = evaluate(name, "test", list(selected.values()))
            results[name] = {"summary": summary,
                             "graph_vs_cosine": compare(rows, selected["graph"]["id"], "cosine", .9875),
                             "topology_vs_graph": compare(rows, selected["topology"]["id"], selected["graph"]["id"], .9875),
                             "topology_vs_cosine_exploratory": compare(rows, selected["topology"]["id"], "cosine"),
                             "difficult_topology_vs_graph_exploratory": compare(rows, selected["topology"]["id"], selected["graph"]["id"], subset=True)}
            print({"dataset": name, "graph_vs_cosine": results[name]["graph_vs_cosine"],
                   "topology_vs_graph": results[name]["topology_vs_graph"]}, flush=True)
    info["results"] = results
    write(OUT / "final-results.json", info)


def reproduce():
    final(replica=True)


def diagnostics():
    from .diagnostics import run_diagnostics
    run_diagnostics()


def report():
    from .report import generate
    generate()
