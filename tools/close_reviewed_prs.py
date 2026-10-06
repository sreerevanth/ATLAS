"""Execute the explicitly approved closure of the nineteen triaged PRs."""

import concurrent.futures
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "sreerevanth/ATLAS"
NUMBERS = [*range(12, 23), *range(24, 32)]
COMMENT = (
    "Thank you @SHAURYASANYAL3 for contributing this phase documentation. "
    "Following the accepted PR triage, we are closing this without merging because "
    "the historical phase-based roadmap has been superseded by ATLAS's current "
    "evidence-driven implementation and research program. Your authorship, commits, "
    "and discussion remain preserved in this PR and repository history."
)


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8")


def close(number):
    before = json.loads(run("gh", "api", f"repos/{REPO}/pulls/{number}"))
    if before["state"] == "open":
        run("gh", "pr", "close", str(number), "--repo", REPO, "--comment", COMMENT)
    after = json.loads(run("gh", "api", f"repos/{REPO}/pulls/{number}"))
    if after["state"] != "closed" or after["merged"] or after["head"]["sha"] != before["head"]["sha"]:
        raise RuntimeError(f"Unexpected state for PR {number}")
    comments = json.loads(run("gh", "api", "--paginate", "--slurp", f"repos/{REPO}/issues/{number}/comments"))
    matches = [item for page in comments for item in page if item["body"] == COMMENT]
    if not matches:
        raise RuntimeError(f"Closing comment missing: {number}")
    return {"number": number, "state": after["state"], "merged": after["merged"],
            "merged_at": after["merged_at"], "closed_at": after["closed_at"],
            "head": after["head"]["sha"], "comment_url": matches[-1]["html_url"]}


def main():
    initial = run("gh", "api", f"repos/{REPO}/branches/main", "--jq", ".commit.sha").strip()
    local = run("git", "rev-parse", "HEAD").strip()
    protected = json.loads((ROOT / "artifacts/local/pr-triage/protected-before.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(close, NUMBERS))
    final = run("gh", "api", f"repos/{REPO}/branches/main", "--jq", ".commit.sha").strip()
    changed = []
    for name, expected in protected.items():
        with (ROOT / name).open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            changed.append(name)
    result = {"utc": datetime.now(timezone.utc).isoformat(), "comment": COMMENT,
              "prs": rows, "remote_main_before": initial, "remote_main_after": final,
              "local_head_before": local, "local_head_after": run("git", "rev-parse", "HEAD").strip(),
              "protected_files": len(protected), "changed_protected_files": changed}
    path = ROOT / "artifacts/local/pr-triage/closure.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if initial != final or changed or result["local_head_after"] != local:
        raise RuntimeError("Closure integrity failed")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
