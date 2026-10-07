"""Post-run verification and corrected process-tree resource measurement.

Does not evaluate held-out retrieval queries or change frozen experiment code.
"""

import argparse
import json
import subprocess
import sys
import time
import psutil

from research.v2.common import CACHE, OUT, ROOT, digest, manifest, protected, read, write


def provenance(stage):
    result = manifest(f".venv-release/Scripts/python -m tools.verify_v2_release {stage}")
    result["verification_tool_sha256"] = digest(__file__)
    return result


def measure():
    info = provenance("measure")
    previous = read(OUT / "scaling.json")
    info["supersedes_memory_only"] = "scaling.json monitored Windows venv launcher, not its interpreter child; original RSS values invalid"
    info["sampling_seconds"] = .01
    rows = []
    write(OUT / "resource-corrected-started.json", info)
    for original in previous["rows"]:
        count, landmarks, method = original["count"], original["landmarks"], original["method"]
        filename = OUT / f"scaling-process-tree/{method}-{count}-{landmarks}.json"
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.with_suffix(".log").open("w", encoding="utf8") as output:
            process = subprocess.Popen([sys.executable, "-m", "research.v2.topology_study", str(count), str(landmarks), method, str(filename)],
                                       cwd=ROOT, stdout=output, stderr=output)
            parent = psutil.Process(process.pid)
            started = time.monotonic()
            peak, peak_members, stopped = 0, 0, None
            while process.poll() is None:
                try:
                    members = [parent] + parent.children(recursive=True)
                except psutil.NoSuchProcess:
                    break
                rss, alive = 0, 0
                for member in members:
                    try:
                        rss += member.memory_info().rss
                        alive += 1
                    except psutil.NoSuchProcess:
                        pass
                peak = max(peak, rss)
                peak_members = max(peak_members, alive)
                if rss > 1536*1024**2 or psutil.virtual_memory().available < 1024**3:
                    stopped = "memory_guard"
                if time.monotonic() - started > 120:
                    stopped = "timeout_120s"
                if stopped:
                    for member in reversed(members):
                        try:
                            member.kill()
                        except psutil.NoSuchProcess:
                            pass
                    break
                time.sleep(.01)
            process.wait()
        row = read(filename) if filename.exists() else {"count": count, "landmarks": landmarks, "method": method}
        row.update(peak_sampled_rss_bytes=peak, maximum_process_tree_members=peak_members,
                   stopped=stopped, exit_code=process.returncode,
                   rss_definition="sum of process-tree resident sets, includes launcher and native interpreter; shared pages may be double-counted")
        if process.returncode and not stopped:
            raise RuntimeError(f"Worker failed: {filename}")
        if not stopped:
            assert row["diagrams"] == original["diagrams"], "Topology changed on instrumentation-only rerun"
            row["diagrams_equal_previous_run"] = True
            if "fidelity" in original:
                row["fidelity"] = original["fidelity"]
        write(filename, row)
        rows.append(row)
        print(f"{method} N={count} L={landmarks}: RSS {peak/1024**2:.1f}MiB; processes={peak_members}; stop={stopped}", flush=True)
    info.update(rows=rows, omitted=previous["omitted"], source_diagram_analysis_sha256=digest(OUT / "scaling.json"))
    write(OUT / "scaling-resource-corrected.json", info)


def verify():
    info = provenance("verify")
    clone = ROOT / "artifacts/local/v2-clone-check"
    executable = clone / ".venv-release/Scripts/python.exe"
    commands = [[str(executable), "-m", "pip", "check"],
                [str(executable), "-m", "pytest", "tests", "research/v2/tests", "-q"],
                [str(executable), "-m", "ruff", "check", "src", "tests", "research/v2"],
                ["git", "status", "--porcelain"]]
    observations = []
    for command in commands:
        result = subprocess.run(command, cwd=clone, text=True, capture_output=True, timeout=180)
        observations.append({"command": command, "cwd": str(clone), "exit_code": result.returncode,
                             "stdout": result.stdout, "stderr": result.stderr})
        assert result.returncode == 0, observations[-1]
    assert observations[-1]["stdout"].strip() == "", "Clean-clone working tree changed"
    clone_out = clone / "artifacts/local/smoke-evidence"
    split_equal = {name: read(OUT / name) == read(clone_out / name) for name in ("hotpot-split.json", "musique-split.json")}
    assert all(split_equal.values())
    clone_prepare = read(clone_out / "prepare-manifest.json")
    clone_gate = read(clone_out / "topology-gate.json")
    assert clone_gate["vr_passed"] and clone_gate["witness_passed"]
    old = read(ROOT / "artifacts/local/research/questions.json")
    hotpot = read(CACHE / "hotpot/questions.json")
    musique = read(CACHE / "musique/questions.json")
    music_docs = {doc["key"]: doc for doc in read(CACHE / "musique/documents.json")}
    old_ids = {query["id"] for query in old}
    old_support = {title for query in old for title in query["support_titles"]}
    hotpot_support = {title for query in hotpot for title in query["support_keys"]}
    music_support = {music_docs[key]["title"] for query in musique for key in query["support_keys"]}
    from research.v2.data import normalize
    def normalized(rows):
        return {normalize(query["question"]).casefold() for query in rows}
    overlaps = {"hotpot_v1_ids": len({query["id"] for query in hotpot} & old_ids),
                "hotpot_v1_support_titles": len(hotpot_support & old_support),
                "musique_v1_or_hotpot_support_titles": len(music_support & (old_support | hotpot_support)),
                "hotpot_v1_question_text": len(normalized(hotpot) & normalized(old)),
                "musique_v1_or_hotpot_question_text": len(normalized(musique) & (normalized(hotpot) | normalized(old)))}
    assert not any(overlaps.values())
    info.update(commands=observations, clone_commit=clone_prepare["git_commit"],
                clone_python=clone_prepare["python"], clone_dependencies=clone_prepare["dependencies"],
                clone_environment=(clone / ".venv-release/pyvenv.cfg").read_text(),
                clone_protected=clone_prepare["protected"], cloned_splits_identical=split_equal,
                clone_topology_gate={key: clone_gate[key] for key in ("vr_passed", "witness_passed")},
                overlap_counts=overlaps, protected=protected(),
                installation_logs={name: (ROOT / "artifacts/local/manifold-v2" / name).read_text(encoding="utf8", errors="replace")
                                   for name in ("clone.log", "clean-install.log", "clean-editable.log")},
                final_evaluation_rerun=False)
    write(OUT / "release-verification.json", info)
    print("Fresh clone, isolated environment, tests, identical splits, gates and protected bytes verified", flush=True)


def publish():
    from research.v2.report import generate
    generate()
    corrected = read(OUT / "scaling-resource-corrected.json")
    rows = corrected["rows"]
    path = ROOT / "docs/MANIFOLD_V2_REPORT.md"
    text = path.read_text(encoding="utf8")
    start = text.index("| Method | N | Landmarks | Seconds | Peak sampled RSS MiB")
    end = text.index("\nResource omissions:", start)
    replacement = ["**Instrumentation correction:** the original `scaling.json` RSS values measured only a Windows launcher and are invalid. The table and figure below use a complete process-tree rerun in `scaling-resource-corrected.json`. All persistence diagrams were checked equal to the original run; no held-out retrieval query was re-evaluated. Process-tree RSS includes shared pages and is not exclusive private memory.", "",
                   "| Method | N | Landmarks | Seconds | Peak process-tree RSS MiB | Simplices | H1 bottleneck |",
                   "|---|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        distance = next((item["bottleneck_finite"] for item in row.get("fidelity", []) if item["dimension"] == 1), None)
        replacement.append(f"| {row['method']} | {row['count']} | {row['landmarks']} | {row.get('seconds')} | {row['peak_sampled_rss_bytes']/1024**2:.1f} | {row.get('simplex_count')} | {distance} |")
    text = text[:start] + "\n".join(replacement) + "\n" + text[end:]
    verified = read(OUT / "release-verification.json")
    text += "\n## Clean-clone execution and extended leakage checks\n\n"
    text += f"Independent checkout `{verified['clone_commit']}` installed the complete pinned dependencies into a new non-system-site-packages virtual environment. Tests, lint and pip check succeeded; raw stdout is in `release-verification.json`. Reconstructed V1 exclusions yielded identical V2 question splits. No final retrieval was rerun.\n\n"
    text += "Exact normalized-question and supporting-title overlap counts with V1 and across datasets: `" + json.dumps(verified["overlap_counts"]) + "`. This does not exclude semantic near-duplicates or encoder pretraining exposure.\n"
    text += "\nRegenerate this corrected report with `.venv-release/Scripts/python -m tools.verify_v2_release publish`, not the archival uncorrected report stage alone.\n"
    path.write_text(text, encoding="utf8")
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    for method, landmarks in sorted({(row["method"], row["landmarks"]) for row in rows}):
        selected = sorted([row for row in rows if row["method"] == method and row["landmarks"] == landmarks and not row["stopped"]], key=lambda row: row["count"])
        axes[0].plot([row["count"] for row in selected], [row["seconds"] for row in selected], "o-", label=f"{method} L={landmarks or 'exact'}")
        axes[1].plot([row["count"] for row in selected], [row["peak_sampled_rss_bytes"]/1024**2 for row in selected], "o-", label=f"{method} L={landmarks or 'exact'}")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("Input documents")
        axis.grid(alpha=.2)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Measured seconds")
    axes[1].set_ylabel("Peak sampled process-tree RSS (MiB)")
    axes[1].legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(OUT / "scaling.png", dpi=160)
    plt.close(figure)
    write(OUT / "publication-manifest.json", provenance("publish"))
    write(OUT / "artifact-index.json", {str(item.relative_to(ROOT)): digest(item) for item in sorted(OUT.rglob("*"))
                                        if item.is_file() and item.name != "artifact-index.json" and item.suffix != ".log"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["measure", "verify", "publish"])
    stage = parser.parse_args().stage
    {"measure": measure, "verify": verify, "publish": publish}[stage]()
