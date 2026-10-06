"""Capture read-only GitHub PR evidence without checking out historical code."""

import concurrent.futures
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/local/pr-triage"
REPOSITORY = "sreerevanth/ATLAS"


def command(*arguments):
    result = subprocess.run(arguments, cwd=ROOT, capture_output=True, check=True)
    return result.stdout.decode("utf-8")


def save(name, value):
    (OUTPUT / name).write_text(value, encoding="utf-8")


def api(endpoint):
    return command("gh", "api", "--paginate", "--slurp", f"repos/{REPOSITORY}/{endpoint}")


def capture(pull):
    number = pull["number"]
    for suffix, endpoint in [
        ("metadata", f"pulls/{number}"),
        ("files", f"pulls/{number}/files?per_page=100"),
        ("commits", f"pulls/{number}/commits?per_page=100"),
        ("discussion", f"issues/{number}/comments?per_page=100"),
        ("reviews", f"pulls/{number}/reviews?per_page=100"),
        ("inline-comments", f"pulls/{number}/comments?per_page=100"),
        ("checks", f"commits/{pull['headRefOid']}/check-runs?per_page=100"),
        ("status", f"commits/{pull['headRefOid']}/status"),
    ]:
        save(f"{number}-{suffix}.json", api(endpoint))
    save(f"{number}.diff", command("gh", "pr", "diff", str(number), "--repo", REPOSITORY))
    return number


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frozen = {}
    for directory in ("src", "tests", "configs", "artifacts/local"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and OUTPUT not in path.parents and "__pycache__" not in path.parts:
                with path.open("rb") as stream:
                    frozen[str(path.relative_to(ROOT))] = hashlib.file_digest(stream, "sha256").hexdigest()
    save("protected-before.json", json.dumps(frozen, indent=2))
    listing = command("gh", "pr", "list", "--repo", REPOSITORY, "--state", "open", "--limit", "100",
                      "--json", "number,title,headRefOid,headRefName,baseRefName,url")
    save("open-prs.json", listing)
    save("main.json", api("branches/main"))
    save("capture.json", json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
         "local_head": command("git", "rev-parse", "HEAD").strip(),
         "git_status": command("git", "status", "--porcelain"), "repository": REPOSITORY}, indent=2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for number in pool.map(capture, json.loads(listing)):
            print(f"Captured PR #{number}", flush=True)


if __name__ == "__main__":
    main()
