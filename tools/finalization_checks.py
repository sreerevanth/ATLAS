"""Non-scientific repository integrity checks; never runs retrieval evaluation."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "docs/FINALIZATION_FREEZE.json"


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf8")


def snapshot():
    if FREEZE.exists():
        raise RuntimeError("Never replace the pre-cleanup freeze")
    names = command("git", "ls-files", "research/v2", "docs/MANIFOLD_V2_REPORT.md", "docs/RESEARCH_REPORT.md").splitlines()
    baseline = json.loads((ROOT / "docs/MANIFOLD_V1_NO_GO.sha256.json").read_text())
    hashes = {name.replace("\\", "/"): value for name, value in baseline.items()}
    hashes.update({name: checksum(ROOT / name) for name in names})
    write(FREEZE, {"baseline_commit": command("git", "rev-parse", "HEAD"),
                   "created_utc": datetime.now(timezone.utc).isoformat(),
                   "purpose": "Byte freeze before presentation cleanup; all V1 protected files and tracked V2 files remain unchanged",
                   "files": hashes})
    print(f"Captured {len(hashes)} files")


def verify(git_blobs=False):
    expected = json.loads(FREEZE.read_text())["files"]
    missing, changed, blob_changed = [], [], []
    tracked = set(command("git", "ls-files").splitlines())
    for name, value in expected.items():
        path = ROOT / name
        if not path.exists():
            missing.append(name)
        elif checksum(path) != value:
            changed.append(name)
        if git_blobs and name in tracked:
            blob = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
            if hashlib.sha256(blob).hexdigest() != value:
                blob_changed.append(name)
    result = {"files": len(expected), "missing": missing, "changed": changed,
              "tracked_blob_mismatches": blob_changed, "git_blobs_checked": git_blobs}
    print(json.dumps(result))
    if missing or changed or blob_changed:
        raise AssertionError(result)
    return result


def prs():
    numbers = list(range(12, 23)) + list(range(24, 32))
    before = command("git", "ls-remote", "origin", "refs/heads/main").split()[0]
    local_before = command("git", "rev-parse", "HEAD")
    fields = " ".join(f"pr{number}:pullRequest(number:{number}){{number state merged mergedAt url}}" for number in numbers)
    query = 'query{repository(owner:"sreerevanth",name:"ATLAS"){' + fields + '}}'
    response = json.loads(command("gh", "api", "graphql", "-f", "query=" + query))
    observations = sorted(response["data"]["repository"].values(), key=lambda row: row["number"])
    for row in observations:
        if row["state"] == "OPEN":
            command("gh", "pr", "close", str(row["number"]), "--comment",
                    "Thank you for the contribution. Closing without merging as part of ATLAS's evidence-driven consolidation. The historical phase-based roadmap has been superseded by the current research implementation and measured findings; authorship, commits, and discussion remain preserved.")
    if any(row["state"] == "OPEN" for row in observations):
        response = json.loads(command("gh", "api", "graphql", "-f", "query=" + query))
        observations = sorted(response["data"]["repository"].values(), key=lambda row: row["number"])
    assert len(observations) == 19 and all(row["state"] == "CLOSED" and not row["merged"] and row["mergedAt"] is None for row in observations)
    after = command("git", "ls-remote", "origin", "refs/heads/main").split()[0]
    assert before == after and local_before == command("git", "rev-parse", "HEAD")
    evidence = {"checked_utc": datetime.now(timezone.utc).isoformat(), "prs": observations,
                "historical_open": 0, "closed": len(observations), "merged": 0,
                "remote_main_before": before, "remote_main_after": after,
                "local_head_before": local_before, "local_head_after": command("git", "rev-parse", "HEAD"),
                "research_integrity": verify()}
    write(ROOT / "docs/FINALIZATION_PR_VERIFICATION.json", evidence)
    print("19 historical PRs closed, none merged, main unchanged by verification/closures")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["snapshot", "verify", "prs"])
    parser.add_argument("--git-blobs", action="store_true")
    args = parser.parse_args()
    if args.stage == "snapshot":
        snapshot()
    elif args.stage == "prs":
        prs()
    else:
        verify(args.git_blobs)
