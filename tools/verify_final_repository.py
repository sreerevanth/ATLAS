"""Verify packaging and small fixtures without rerunning frozen research."""

import json
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from tools.finalization_checks import ROOT, checksum, command, verify, write


def main():
    commit = command("git", "rev-parse", "HEAD")
    output = ROOT / "artifacts/local/finalization" / commit[:12]
    output.mkdir(parents=True, exist_ok=False)
    evidence = {"started_utc": datetime.now(timezone.utc).isoformat(), "source_commit": commit,
                "python": sys.version, "verification_tool_sha256": checksum(Path(__file__)),
                "commands": [], "typing": "not configured for current research package",
                "retrieval_or_architecture_search_executed": False, "freeze_before": verify(git_blobs=True)}

    def run(label, arguments, cwd=ROOT, environment=None, timeout=300):
        started = time.perf_counter()
        result = subprocess.run([str(argument) for argument in arguments], cwd=cwd,
                                env=environment, text=True, encoding="utf8", errors="replace",
                                capture_output=True, timeout=timeout)
        observation = {"label": label, "command": [str(argument) for argument in arguments],
                       "cwd": str(cwd), "exit_code": result.returncode,
                       "seconds": time.perf_counter()-started, "stdout": result.stdout, "stderr": result.stderr}
        evidence["commands"].append(observation)
        write(output / "progress.json", evidence)
        print(f"{label}: exit {result.returncode}", flush=True)
        if result.returncode:
            raise RuntimeError(json.dumps(observation, indent=2))
        return result.stdout

    run("tests", [sys.executable, "-m", "pytest", "tests", "research/v2/tests", "-q"])
    run("ruff", [sys.executable, "-m", "ruff", "check", "src", "tests", "research/v2", "tools"])
    run("reference_dependencies", [sys.executable, "-m", "pip", "check"])
    run("compile_current_package", [sys.executable, "-m", "compileall", "-q", "src/atlas", "research/v2", "tools"])
    provenance = json.loads((ROOT / "docs/README_PROVENANCE.json").read_text())
    assert checksum(ROOT / "README.md") == provenance["readme_sha256"]
    assert checksum(ROOT / provenance["generator"]) == provenance["generator_sha256"]
    for name, expected in provenance["sources"].items():
        assert checksum(ROOT / name) == expected, name
    links = re.findall(r"\]\(([^)]+)\)", (ROOT / "README.md").read_text(encoding="utf8"))
    missing = [link for link in links if not link.startswith(("http:", "https:", "#"))
               and link.split("#")[0] != "docs/FINALIZATION_VERIFICATION.json"
               and not (ROOT / link.split("#")[0]).exists()]
    assert not missing, missing
    evidence["readme"] = {"numeric_provenance_verified": True, "missing_local_links": missing,
                          "verification_record_link_created_by_this_run": True}
    artifact_index = json.loads((ROOT / "research/v2/evidence/artifact-index.json").read_text())
    mismatches = [name for name, value in artifact_index.items() if checksum(ROOT / name.replace("\\", "/")) != value]
    assert not mismatches, mismatches
    evidence["v2_artifact_index"] = {"checked": len(artifact_index), "mismatches": mismatches}
    archive = output / "source.zip"
    run("export_committed_source", ["git", "archive", "--format=zip", f"--output={archive}", "HEAD"])
    source = output / "source"
    with zipfile.ZipFile(archive) as zipped:
        for name in zipped.namelist():
            destination = (source / name).resolve()
            if not destination.is_relative_to(source.resolve()):
                raise ValueError("Unsafe archive path")
        zipped.extractall(source)
    run("build_sdist_and_wheel", [sys.executable, "-m", "build", "--no-isolation"], cwd=source)
    wheel = source / "dist/atlas_research-0.1.0-py3-none-any.whl"
    sdist = source / "dist/atlas_research-0.1.0.tar.gz"
    assert wheel.exists() and sdist.exists()
    evidence["build"] = {"wheel_sha256": checksum(wheel), "sdist_sha256": checksum(sdist),
                         "wheel_bytes": wheel.stat().st_size, "sdist_bytes": sdist.stat().st_size}
    environment_root = output / "wheel-environment"
    run("create_clean_environment", [sys.executable, "-m", "venv", environment_root])
    executable = environment_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    cli = environment_root / ("Scripts/atlas.exe" if os.name == "nt" else "bin/atlas")
    run("clean_locked_dependencies", [executable, "-m", "pip", "install", "-r", source / "research/v2/requirements-lock.txt"], timeout=1200)
    run("wheel_install", [executable, "-m", "pip", "install", "--no-deps", wheel])
    run("clean_pip_check", [executable, "-m", "pip", "check"])
    wheel_cwd = output / "wheel-cwd"
    wheel_cwd.mkdir()
    import_result = run("wheel_import", [executable, "-c", "import atlas,json,importlib.metadata; print(json.dumps({'file':atlas.__file__,'version':importlib.metadata.version('atlas-research')}))"], cwd=wheel_cwd)
    installed = json.loads(import_result)
    assert Path(installed["file"]).resolve().is_relative_to(environment_root.resolve()), installed
    evidence["installed_package"] = installed
    evidence["clean_environment"] = (environment_root / "pyvenv.cfg").read_text()
    run("installed_cli_help", [cli, "--help"], cwd=wheel_cwd)
    run("installed_module_help", [executable, "-m", "atlas", "--help"], cwd=wheel_cwd)
    run("wheel_topology_smoke", [executable, "-m", "atlas", "validate", "--config", source / "configs/research.json", "--output", output / "wheel-validate"], cwd=wheel_cwd)
    run("wheel_local_quic_wasm_smoke", [executable, "-m", "atlas", "integration", "--config", source / "configs/research.json", "--output", output / "wheel-integration"], cwd=wheel_cwd)
    integration = json.loads((output / "wheel-integration/integration.json").read_text())
    assert integration["synthetic"] and integration["transport"] == "QUIC" and integration["match_count"] > 0
    evidence["integration_smoke"] = integration
    gates = []
    for iteration in (1, 2):
        gate_output = output / f"v2-fixture-{iteration}"
        environment = os.environ.copy()
        environment["ATLAS_V2_EVIDENCE"] = str(gate_output)
        run(f"v2_synthetic_reproduction_{iteration}", [executable, "-m", "research.v2.run", "gate"], environment=environment)
        gate = json.loads((gate_output / "topology-gate.json").read_text())
        assert gate["vr_passed"] and gate["witness_passed"]
        gates.append(gate)
    assert gates[0]["rows"] == gates[1]["rows"]
    evidence["reproduction_smoke"] = {"synthetic_only": True, "vr_gate": True, "witness_gate": True,
                                      "repeated_diagrams_equal": True, "final_test_evaluated": False}
    historical_paths = [name for name in command("git", "ls-files", "*.md").splitlines()
                        if name.startswith(("atlas-core/", "atlas-experiments/", "specs/"))
                        or name in ("01_core_principles.md", "ATLAS_PROMPT_BOOK.md", "ATLAS_TECHNICAL_README (1).md", "MASTER_PLAN.md", "pr11.md", "adrs/ADR-001_persistence_landscapes.md", "adrs/ADR-002_privacy_layer.md", "adrs/Phase20_Final_ADR.md")]
    assert all("Historical material" in (ROOT / name).read_text(encoding="utf8").splitlines()[2] for name in historical_paths)
    evidence["historical_markers"] = {"files_checked": len(historical_paths), "all_marked": True}
    evidence["freeze_after"] = verify(git_blobs=True)
    evidence["finished_utc"] = datetime.now(timezone.utc).isoformat()
    evidence["status"] = "passed"
    evidence["non_claims"] = ["Not a new research evaluation", "Not an independent security audit", "No software license invented"]
    write(ROOT / "docs/FINALIZATION_VERIFICATION.json", evidence)
    write(output / "complete.json", evidence)
    print("Final repository verification passed; no frozen experiment rerun", flush=True)


if __name__ == "__main__":
    main()
