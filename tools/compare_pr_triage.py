"""Verify PR deltas and ancestry against the captured main commit."""

import hashlib
import json
import subprocess

from capture_pr_triage import OUTPUT, ROOT, command, save


def pages(number, kind):
    return json.loads((OUTPUT / f"{number}-{kind}.json").read_text(encoding="utf-8"))


def blob(reference, path):
    result = subprocess.run(["git", "rev-parse", f"{reference}:{path}"], cwd=ROOT,
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def main():
    pulls = json.loads((OUTPUT / "open-prs.json").read_text(encoding="utf-8"))
    main_commit = json.loads((OUTPUT / "main.json").read_text(encoding="utf-8"))[0]["commit"]["sha"]
    results = []
    for pull in sorted(pulls, key=lambda item: item["number"]):
        number, head = pull["number"], pull["headRefOid"]
        files = [item for page in pages(number, "files") for item in page]
        parent = command("git", "rev-parse", f"{head}^").strip()
        merge_base = command("git", "merge-base", main_commit, head).strip()
        save(f"{number}-current-main.diff", command("git", "diff", f"{main_commit}...{head}"))
        changes = []
        for item in files:
            path = item["filename"]
            main_blob, head_blob = blob(main_commit, path), blob(head, path)
            current = ROOT / path
            changes.append({"path": path, "status": item["status"], "additions": item["additions"],
                            "deletions": item["deletions"], "main_blob": main_blob, "head_blob": head_blob,
                            "already_identical_on_main": main_blob == head_blob,
                            "current_working_file_exists": current.exists(),
                            "current_working_sha256": hashlib.sha256(current.read_bytes()).hexdigest() if current.exists() else None})
        dependencies = []
        for other in pulls:
            if other["number"] != number:
                result = subprocess.run(["git", "merge-base", "--is-ancestor", other["headRefOid"], head], cwd=ROOT)
                if result.returncode == 0:
                    dependencies.append(other["number"])
                elif result.returncode != 1:
                    raise RuntimeError("Ancestry check failed")
        row = {"number": number, "title": pull["title"], "head": head, "parent": parent,
               "merge_base_with_main": merge_base, "files": changes,
               "unique_commits": command("git", "rev-list", f"{main_commit}..{head}").splitlines(),
               "ancestor_open_prs": dependencies,
               "discussion": [{"author": item["user"]["login"], "url": item["html_url"], "body": item["body"]}
                              for page in pages(number, "discussion") for item in page],
               "reviews": [item for page in pages(number, "reviews") for item in page],
               "inline_comments": [item for page in pages(number, "inline-comments") for item in page],
               "check_runs": [item for page in pages(number, "checks") for item in page["check_runs"]],
               "statuses": [{key: item[key] for key in ("context", "state", "description")}
                            for item in pages(number, "status")[0]["statuses"]]}
        results.append(row)
        print(json.dumps({key: row[key] for key in ("number", "parent", "merge_base_with_main", "ancestor_open_prs", "files")}), flush=True)
    save("comparison.json", json.dumps({"main": main_commit, "prs": results}, indent=2))


if __name__ == "__main__":
    main()
