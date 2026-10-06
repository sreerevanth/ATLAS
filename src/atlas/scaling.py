"""Resource-aware isolated topology workers and exact-overlap comparisons."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil
from persim import bottleneck, wasserstein

from atlas.evidence import manifest, write_json
from atlas.topology import finite, persistence


def worker(source, count, landmarks, destination, config):
    vectors = np.load(source, mmap_mode="r")[:count]
    started = time.perf_counter()
    result = persistence(vectors, landmarks or None)
    elapsed = time.perf_counter() - started
    write_json(destination, {
        "manifest": manifest(source.resolve().parents[2], config),
        "seconds": elapsed, "edges": result["edges"], "cover_radius": result["cover_radius"],
        "diagrams": [
            [[float(birth), float(death) if np.isfinite(death) else None]
             for birth, death in np.asarray(diagram).reshape(-1, 2)]
            for diagram in result["diagrams"]
        ],
        "essential_counts": [int(np.isinf(diagram[:, 1]).sum()) for diagram in result["diagrams"]],
        "landmark_indices": result["landmark_indices"],
        "simplex_count": None, "simplex_count_reason": "Ripser exposes edge count, not full simplex count",
    })


def run_scaling(source, output, config):
    rows = []
    available_count = len(np.load(source, mmap_mode="r"))
    exact_failed = False
    for count in config["scales"]:
        if count > available_count:
            rows.append({"n": count, "status": "skipped_insufficient_data"})
            continue
        exact = None
        methods = [0] + config["landmarks"]
        for landmarks in methods:
            row = {"n": count, "landmarks": landmarks, "method": "exact_vr" if landmarks == 0 else "greedy_landmark_vr"}
            if landmarks == 0 and (count > config["exact_limit"] or exact_failed):
                rows.append({**row, "status": "skipped_resource_policy"})
                continue
            cap = min(config["worker_memory_mb"] * 1024**2, psutil.virtual_memory().available // 3)
            if cap < 300 * 1024**2:
                rows.append({**row, "status": "skipped_low_available_memory"})
                continue
            destination = output / f"topology-{count}-{landmarks}.json"
            command = [sys.executable, "-m", "atlas", "topology-worker", str(source), str(count), str(landmarks), str(destination), "--config", str(Path("configs/research.json").resolve())]
            started = time.perf_counter()
            environment = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
            with destination.with_suffix(".stdout.txt").open("w") as stdout, destination.with_suffix(".stderr.txt").open("w") as stderr:
                process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment)
                monitor = psutil.Process(process.pid)
                peak = 0
                status = "ok"
                while process.poll() is None:
                    try:
                        process_tree = [monitor, *monitor.children(recursive=True)]
                        current_rss = sum(child.memory_info().rss for child in process_tree)
                        peak = max(peak, current_rss)
                    except psutil.NoSuchProcess:
                        break
                    if peak > cap or time.perf_counter() - started > config["worker_timeout_seconds"]:
                        status = "memory_limit" if peak > cap else "timeout"
                        for child in reversed(process_tree[1:]):
                            try:
                                child.kill()
                            except psutil.NoSuchProcess:
                                pass
                        process.kill()
                        process.wait()
                        break
                    time.sleep(0.025)
                process.wait()
            row.update(status=status if process.returncode == 0 or status != "ok" else "error",
                       peak_sampled_rss_bytes=peak, memory_cap_bytes=cap,
                       memory_measurement="aggregate psutil RSS of launcher and descendants sampled every 25 ms; transient peaks may be missed",
                       subprocess_seconds=time.perf_counter() - started, command=command,
                       returncode=process.returncode)
            if row["status"] == "ok":
                artifact = json.loads(destination.read_text())
                row.update({key: value for key, value in artifact.items() if key != "manifest"})
                row["worker_manifest"] = artifact["manifest"]
                result = row
                if landmarks == 0:
                    exact = result
                elif exact is not None:
                    row["bottleneck"] = [float(bottleneck(_diagram(left), _diagram(right)))
                                         for left, right in zip(exact["diagrams"], result["diagrams"], strict=True)]
                    row["wasserstein"] = [float(wasserstein(_diagram(left), _diagram(right)))
                                          for left, right in zip(exact["diagrams"], result["diagrams"], strict=True)]
                    row["dominant_lifetimes"] = {
                        method: [float(np.max(np.diff(finite(_diagram(diagram)), axis=1), initial=0)) for diagram in value["diagrams"]]
                        for method, value in [("exact", exact), ("approximate", result)]
                    }
            elif landmarks == 0:
                exact_failed = True
            rows.append(row)
            write_json(output / "scaling.json", rows)
    plot_scaling(rows, output / "scaling.png")
    return rows


def _diagram(rows):
    diagram = np.asarray([[birth, np.inf if death is None else death] for birth, death in rows], dtype=float)
    return diagram.reshape(-1, 2)


def plot_scaling(rows, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    successful = [row for row in rows if row.get("status") == "ok"]
    if not successful:
        return
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    methods = sorted({row["method"] for row in successful})
    for method in methods:
        selected = sorted((row for row in successful if row["method"] == method), key=lambda row: row["n"])
        sizes = [row["n"] for row in selected]
        axes[0].plot(sizes, [row["subprocess_seconds"] for row in selected], marker="o", label=method)
        axes[1].plot(sizes, [row["peak_sampled_rss_bytes"] / 1024**2 for row in selected], marker="o", label=method)
    for axis, ylabel in zip(axes, ("Wall time (seconds)", "Sampled peak RSS (MiB)"), strict=True):
        axis.set_xlabel("Point count")
        axis.set_ylabel(ylabel)
        axis.set_yscale("log")
        axis.grid(True, alpha=0.25)
    axes[0].legend(fontsize="small")
    figure.suptitle("Observed Ripser scaling (only completed runs)")
    figure.tight_layout()
    figure.savefig(destination, dpi=160)
    plt.close(figure)
