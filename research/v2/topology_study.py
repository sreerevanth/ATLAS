import subprocess
import sys
import time

import gudhi
import numpy as np
import psutil
from persim import wasserstein
from ripser import ripser
from scipy.spatial.distance import cdist

from .common import CACHE, OUT, ROOT, SEED, finite, intervals_json, manifest, read, write


def witness(points, landmarks):
    selected = [0]
    nearest = cdist(points, points[:1], metric="sqeuclidean")[:, 0]
    for _ in range(1, min(landmarks, len(points))):
        node = int(np.argmax(nearest))
        selected.append(node)
        nearest = np.minimum(nearest, cdist(points, points[node:node+1], metric="sqeuclidean")[:, 0])
    distances = cdist(points, points[selected], metric="sqeuclidean")
    order = np.argsort(distances, axis=1)
    table = [[(int(index), float(row[index])) for index in indices]
             for row, indices in zip(distances, order, strict=True)]
    tree = gudhi.WitnessComplex(nearest_landmark_table=table).create_simplex_tree(max_alpha_square=2., limit_dimension=2)
    tree.persistence()
    return {"dgms": [tree.persistence_intervals_in_dimension(dimension) for dimension in (0, 1)],
            "simplex_count": tree.num_simplices(), "landmark_indices": selected,
            "filtration": "squared-distance relaxation alpha^2; NOT VR radius"}


def gate():
    info = manifest(".venv-release/Scripts/python -m research.v2.run gate")
    rng = np.random.default_rng(SEED)
    angles = np.linspace(0, 2*np.pi, 96, endpoint=False)
    circle = np.column_stack((np.cos(angles), np.sin(angles)))
    clusters = np.concatenate((rng.normal(0, .015, (40, 2)), rng.normal(3, .015, (40, 2))))
    rows = []
    for name, points in [("circle", circle), ("noisy_circle", circle + rng.normal(0, .01, circle.shape)), ("clusters", clusters)]:
        result = ripser(cdist(points, points), distance_matrix=True, maxdim=1)
        lifetimes = [np.sort(finite(diagram)[:, 1] - finite(diagram)[:, 0])[::-1] for diagram in result["dgms"]]
        passed = (lifetimes[1][0] > 1.3 and np.sum(lifetimes[1] > .3) == 1) if name != "clusters" else (lifetimes[0][0] > 3 and lifetimes[0][1] < .1)
        rows.append({"dataset": name, "method": "VR", "passed": bool(passed), "diagrams": intervals_json(result["dgms"])})
        weak = witness(points, 32)
        bars = finite(weak["dgms"][1])
        lifetimes_w = bars[:, 1] - bars[:, 0]
        if name != "clusters":
            witness_passed = bool(np.sum(lifetimes_w > .3) == 1)
        else:
            witness_passed = bool(np.sum(~np.isfinite(weak["dgms"][0][:, 1])) == 2)
        rows.append({"dataset": name, "method": "weak_witness", "passed": witness_passed,
                     "diagrams": intervals_json(weak["dgms"]), "simplex_count": weak["simplex_count"]})
    info["rows"] = rows
    info["vr_passed"] = all(row["passed"] for row in rows if row["method"] == "VR")
    info["witness_passed"] = all(row["passed"] for row in rows if row["method"] == "weak_witness")
    write(OUT / "topology-gate.json", info)
    assert info["vr_passed"], "STOP downstream VR: mathematical gate failed"
    print({key: info[key] for key in ("vr_passed", "witness_passed")}, flush=True)


def worker(count, landmarks, method, destination):
    points = np.load(CACHE / "hotpot/documents.npy")[:count]
    start = time.perf_counter()
    if method == "witness":
        result = witness(points, landmarks)
    else:
        if landmarks:
            result = ripser(points, maxdim=1, n_perm=landmarks)
        else:
            result = ripser(cdist(points, points), distance_matrix=True, maxdim=1)
    write(destination, {"count": count, "landmarks": landmarks, "method": method,
                        "seconds": time.perf_counter() - start, "diagrams": intervals_json(result["dgms"]),
                        "edges": result.get("num_edges"), "simplex_count": result.get("simplex_count"),
                        "cover_radius": float(result.get("r_cover", 0)),
                        "filtration": result.get("filtration", "Euclidean VR distance")})


def scaling():
    info = manifest(".venv-release/Scripts/python -m research.v2.run scaling")
    info["bottleneck_implementation"] = "GUDHI exact e=0; finite diagrams only"
    write(OUT / "scaling-started.json", info)
    mathematical = read(OUT / "topology-gate.json")
    assert mathematical["vr_passed"]
    total = len(np.load(CACHE / "hotpot/documents.npy", mmap_mode="r"))
    cells = [(count, landmarks, "vr") for count in (250, 500, 1000, 2000, 5000, 10000)
             if count <= total for landmarks in ((0, 32, 64, 128) if count <= 1000 else (32, 64, 128))]
    if mathematical["witness_passed"]:
        cells += [(count, landmarks, "witness") for count in (250, 500, 1000) for landmarks in (32, 64)]
    rows = []
    for count, landmarks, method in cells:
        filename = OUT / f"scaling-gudhi/{method}-{count}-{landmarks}.json"
        filename.parent.mkdir(parents=True, exist_ok=True)
        log = filename.with_suffix(".log")
        with log.open("w", encoding="utf8") as stream:
            process = subprocess.Popen([sys.executable, "-m", "research.v2.topology_study", str(count), str(landmarks), method, str(filename)],
                                       cwd=ROOT, stdout=stream, stderr=stream)
            monitored = psutil.Process(process.pid)
            peak, started, stopped = 0, time.monotonic(), None
            while process.poll() is None:
                try:
                    peak = max(peak, monitored.memory_info().rss)
                except psutil.NoSuchProcess:
                    break
                if peak > 1536*1024**2 or psutil.virtual_memory().available < 1024**3:
                    stopped = "memory_guard"
                if time.monotonic() - started > 120:
                    stopped = "timeout_120s"
                if stopped:
                    process.kill()
                    break
                time.sleep(.02)
            process.wait()
        row = read(filename) if filename.exists() else {"count": count, "landmarks": landmarks, "method": method}
        row.update(peak_sampled_rss_bytes=peak, exit_code=process.returncode, stopped=stopped)
        if process.returncode and not stopped:
            raise RuntimeError(f"Topology worker failed: {log}")
        write(filename, row)
        rows.append(row)
        print({key: row.get(key) for key in ("count", "landmarks", "method", "seconds", "stopped")}, flush=True)
    for row in rows:
        if row["method"] != "vr" or row.get("stopped"):
            continue
        exact = next((item for item in rows if item["count"] == row["count"] and item["landmarks"] == 0 and item["method"] == "vr" and not item.get("stopped")), None)
        if exact:
            distances = []
            for dimension in (0, 1):
                reference = np.asarray([[birth, death if death is not None else np.inf] for birth, death in exact["diagrams"][dimension]]).reshape(-1, 2)
                approximate = np.asarray([[birth, death if death is not None else np.inf] for birth, death in row["diagrams"][dimension]]).reshape(-1, 2)
                ref, approx = finite(reference), finite(approximate)
                distances.append({"dimension": dimension, "bottleneck_finite": float(gudhi.bottleneck_distance(ref, approx, e=0)),
                                  "wasserstein_finite": float(wasserstein(ref, approx)),
                                  "exact_essential": int(np.sum(~np.isfinite(reference[:, 1]))),
                                  "approx_essential": int(np.sum(~np.isfinite(approximate[:, 1]))),
                                  "exact_dominant": float(np.max(ref[:, 1]-ref[:, 0], initial=0)),
                                  "approx_dominant": float(np.max(approx[:, 1]-approx[:, 0], initial=0))})
            row["fidelity"] = distances
    info["rows"] = rows
    info["omitted"] = {"exact_above_1000": "preregistered resource bound", "n10000": "corpus smaller than 10000" if total < 10000 else None,
                       "witness": None if mathematical["witness_passed"] else "synthetic witness gate failed; no downstream witness"}
    write(OUT / "scaling.json", info)


if __name__ == "__main__":
    worker(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4])
