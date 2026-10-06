"""Verify protected research files and snapshot a triage evidence inventory."""

import hashlib
import json
import re
from datetime import datetime, timezone

from capture_pr_triage import OUTPUT, REPOSITORY, ROOT, command, save


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    before = json.loads((OUTPUT / "protected-before.json").read_text(encoding="utf-8"))
    changed = [name for name, checksum in before.items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != checksum]
    unexpected = []
    for directory in ("src", "tests", "configs", "artifacts/local"):
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and OUTPUT not in path.parents and "__pycache__" not in path.parts:
                if str(path.relative_to(ROOT)) not in before:
                    unexpected.append(str(path.relative_to(ROOT)))
    current = json.loads(command("gh", "pr", "list", "--repo", REPOSITORY, "--state", "open",
                                 "--limit", "100", "--json", "number,headRefOid,state"))
    original = json.loads((OUTPUT / "open-prs.json").read_text(encoding="utf-8"))
    unchanged_prs = {item["number"]: item["headRefOid"] for item in original} == {
        item["number"]: item["headRefOid"] for item in current}
    main_before = json.loads((OUTPUT / "main.json").read_text(encoding="utf-8"))[0]["commit"]["sha"]
    main_after = command("gh", "api", f"repos/{REPOSITORY}/branches/main", "--jq", ".commit.sha").strip()
    result = {"utc": datetime.now(timezone.utc).isoformat(), "protected_file_count": len(before),
              "changed_or_missing_files": changed, "unexpected_files": unexpected,
              "protected_content_unchanged": not changed and not unexpected,
              "open_pr_heads_and_set_unchanged": unchanged_prs, "current_open_prs": current,
              "main_unchanged": main_before == main_after, "main": main_after}
    save("protected-verification.json", json.dumps(result, indent=2))
    if changed or unexpected or not unchanged_prs or main_before != main_after:
        raise RuntimeError(json.dumps(result))
    comparison = json.loads((OUTPUT / "comparison.json").read_text(encoding="utf-8"))
    assert len(comparison["prs"]) == 19
    report = (ROOT / "docs/PR_TRIAGE.md").read_text(encoding="utf-8")
    classification_rows = [line for line in report.splitlines() if line.startswith("| [#")]
    assert len(classification_rows) == len(comparison["prs"])
    classifications = {}
    allowed = {"MERGE", "SALVAGE", "SUPERSEDED", "OBSOLETE", "UNSUPPORTED", "DANGEROUS"}
    for line in classification_rows:
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        assert len(cells) == 11 and cells[8] in allowed
        number = int(re.search(r"\[#(\d+)\]", cells[0]).group(1))
        assert number not in classifications
        classifications[number] = cells[8]
    assert set(classifications) == {pull["number"] for pull in comparison["prs"]}
    for pull in comparison["prs"]:
        assert len(pull["unique_commits"]) == 1 and not pull["ancestor_open_prs"]
        assert all(item["path"].endswith(".md") for item in pull["files"])
        assert not pull["reviews"] and not pull["inline_comments"] and not pull["check_runs"]
        assert len(pull["discussion"]) == 1
        assert all(item["description"] == "Review rate limited" for item in pull["statuses"])
        assert (OUTPUT / f"{pull['number']}.diff").read_text(encoding="utf-8") == (
            OUTPUT / f"{pull['number']}-current-main.diff").read_text(encoding="utf-8")
        assert (OUTPUT / f"{pull['number']}.diff").read_text(encoding="utf-8").rstrip() in report
    inventory = {str(path.relative_to(ROOT)): digest(path) for path in sorted(OUTPUT.iterdir())
                 if path.is_file() and path.name != "inventory.json"}
    save("inventory.json", json.dumps({"verification": result, "classifications": classifications, "files_sha256": inventory,
         "tools_sha256": {str(path.relative_to(ROOT)): digest(path) for path in sorted((ROOT / "tools").glob("*.py"))}}, indent=2))
    print(json.dumps({"protected_files": len(before), "unchanged": True,
                      "open_prs": len(current), "all_diffs_match_current_main_merge_base": True,
                      "raw_evidence_files": len(inventory)}))


if __name__ == "__main__":
    main()
