"""Machine-readable evidence and reproducibility manifests."""

import importlib.metadata
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import psutil


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def manifest(root: Path, config: dict) -> dict:
    files = sorted(root.glob("src/**/*.py")) + sorted(root.glob("tests/**/*.py"))
    files += [root / "pyproject.toml", root / "requirements-lock.txt"]
    source_hashes = {str(path.relative_to(root)): digest(path) for path in files if path.exists()}
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()
    try:
        installed = importlib.metadata.version("atlas-research")
    except importlib.metadata.PackageNotFoundError:
        installed = "editable-or-uninstalled"
    return {
        "utc": datetime.now(timezone.utc).isoformat(),
        "command": subprocess.list2cmdline([sys.executable, *sys.argv]),
        "config": config,
        "config_sha256": config_hash,
        "package_version": installed,
        "python": sys.version,
        "os": platform.platform(),
        "cpu": platform.processor(),
        "logical_cpus": psutil.cpu_count(),
        "ram_bytes": psutil.virtual_memory().total,
        "hardware_used": "CPU",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "git_status": subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root, text=True
        ).splitlines(),
        "source_sha256": source_hashes,
        "source_tree_sha256": hashlib.sha256(
            json.dumps(source_hashes, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "dependencies": {
            package.metadata["Name"]: package.version
            for package in importlib.metadata.distributions()
        },
    }
