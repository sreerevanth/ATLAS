import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("ATLAS_V2_EVIDENCE", str(ROOT / "research/v2/evidence"))).resolve()
CACHE = Path(os.environ.get("ATLAS_V2_CACHE", str(ROOT / "artifacts/local/manifold-v2"))).resolve()
SEED = 20261006


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf8")


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1048576):
            checksum.update(block)
    return checksum.hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def protected():
    expected = read(ROOT / "docs/MANIFOLD_V1_NO_GO.sha256.json")
    missing = [name for name in expected if not (ROOT / name.replace("\\", "/")).exists()]
    allowed_missing = os.environ.get("ATLAS_V2_ALLOW_MISSING_V1_ARTIFACTS") == "1"
    if missing and (not allowed_missing or any(not (name.replace("\\", "/").startswith("artifacts/local/") or ".egg-info/" in name.replace("\\", "/")) for name in missing)):
        raise AssertionError("Missing frozen files. Fresh clones may explicitly allow unavailable ignored V1 artifacts; tracked code may not be missing.")
    changed = [name for name, value in expected.items() if name not in missing and digest(ROOT / name.replace("\\", "/")) != value]
    if changed:
        raise AssertionError(f"Frozen V1 changed: {changed}")
    return {"checked": len(expected) - len(missing), "changed": changed, "unavailable": missing}


def manifest(command):
    sources = sorted((ROOT / "research/v2").rglob("*.py"))
    sources += [ROOT / "research/v2/PROTOCOL.md"]
    dirty = git("status", "--porcelain", "--", *[str(path) for path in sources])
    if dirty:
        raise RuntimeError("Commit experiment code/protocol before execution: " + dirty)
    return {"command": command, "git_commit": git("rev-parse", "HEAD"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(), "seed": SEED,
            "python": sys.version, "os": platform.platform(), "cpu": platform.processor(),
            "logical_cpus": psutil.cpu_count(), "ram_bytes": psutil.virtual_memory().total,
            "gpu_used": False, "dependencies": {item.metadata["Name"]: item.version
                for item in importlib.metadata.distributions()},
            "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for path in sources},
            "protected": protected()}


def finite(diagram):
    diagram = np.asarray(diagram).reshape(-1, 2)
    return diagram[np.isfinite(diagram).all(axis=1)]


def intervals_json(diagrams):
    return [[[float(birth), float(death) if np.isfinite(death) else None]
             for birth, death in diagram] for diagram in diagrams]
