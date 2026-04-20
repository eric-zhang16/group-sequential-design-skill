"""
Parse a single GitHub issue (by number) into an eval entry and upsert it
into the appropriate plugins/{skill}/skills/{skill}/evals/evals.json file.

Usage:
    python import_issue_eval.py --issue 5
    python import_issue_eval.py --issue https://github.com/eric-zhang16/Biostatistics-skills/issues/5
"""

import json
import subprocess
import argparse
import sys
import os
import re
from pathlib import Path

REPO = "eric-zhang16/Biostatistics-skills"

# Must stay in sync with .github/ISSUE_TEMPLATE/benchmark.md
EXPECTED_HEADERS = {
    "skill":           "## Skills",
    "prompt":          "## Query",
    "expected_output": "## Expected Output",
    "files":           "## Attached Files / Input Context (Optional)",
    "assertions":      "## Rubric Criteria (Assertions)",
}

# Repo root is 3 levels up from this script
REPO_ROOT = Path(__file__).resolve().parents[3]


def clean_value(val: str) -> str:
    if not val:
        return ""
    val = re.sub(r"<!--.*?-->", "", val, flags=re.DOTALL)  # strip HTML comments
    val = re.sub(r"^[\s\-\*•]+", "", val.strip()).strip()
    return val


def parse_issue_markdown(body: str) -> dict:
    sections = {
        "skill":           r"## Skills\n(.*?)(?=\n##|$)",
        "prompt":          r"## Query\n(.*?)(?=\n##|$)",
        "expected_output": r"## Expected Output\n(.*?)(?=\n##|$)",
        "files":           r"## Attached Files / Input Context \(Optional\)\n(.*?)(?=\n##|$)",
        "assertions":      r"## Rubric Criteria \(Assertions\)\n(.*?)(?=\n##|$)",
    }

    data: dict = {}
    for key, pattern in sections.items():
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        content = match.group(1).strip() if match else ""

        if key == "skill":
            data["skill_name"] = clean_value(content).lower().replace(" ", "-").replace("_", "-")
        elif key == "files":
            data["files"] = [clean_value(f) for f in content.split("\n") if clean_value(f)]
        elif key == "assertions":
            data["assertions"] = [clean_value(a) for a in content.split("\n") if clean_value(a)]
        else:
            data[key] = clean_value(content)

        result_value = data.get("skill_name" if key == "skill" else key, "")
        is_empty = (
            not result_value
            if not isinstance(result_value, list)
            else len(result_value) == 0
        )
        if is_empty:
            print(
                f"WARNING: '{EXPECTED_HEADERS[key]}' section is empty or missing. "
                "Ensure the issue follows the benchmark template.",
                file=sys.stderr,
            )

    return data


def resolve_skill_evals_path(skill_name: str) -> Path:
    """
    Skills live at plugins/{skill_name}/skills/{skill_name}/evals/evals.json.
    Falls back to a direct flat path if the nested one doesn't exist (future-proofing).
    """
    nested = REPO_ROOT / "plugins" / skill_name / "skills" / skill_name / "evals"
    if nested.parent.exists() or not (REPO_ROOT / skill_name).exists():
        return nested / "evals.json"
    # Flat fallback
    return REPO_ROOT / skill_name / "evals" / "evals.json"


def save_to_evals(eval_entry: dict, skill_name: str) -> str:
    if not skill_name or skill_name == "unknown-skill":
        return "Error: Could not determine target skill name from issue."

    eval_file = resolve_skill_evals_path(skill_name)
    eval_file.parent.mkdir(parents=True, exist_ok=True)

    if eval_file.exists():
        with open(eval_file) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"skill_name": skill_name, "evals": []}
    else:
        data = {"skill_name": skill_name, "evals": []}

    found_idx = -1
    for i, existing in enumerate(data["evals"]):
        if existing.get("id") == eval_entry["id"]:
            found_idx = i
            break

    if found_idx != -1:
        existing = data["evals"][found_idx]
        changed = any(
            existing.get(field) != eval_entry.get(field)
            for field in ("prompt", "expected_output", "files", "assertions")
        )
        if not changed:
            return f"Skipped: {eval_entry['id']} in {skill_name} is up to date."
        data["evals"][found_idx] = eval_entry
        status = f"Updated: {eval_entry['id']} in {eval_file} (content changed)"
    else:
        data["evals"].append(eval_entry)
        status = f"Success: Added {eval_entry['id']} to {eval_file}"

    with open(eval_file, "w") as f:
        json.dump(data, f, indent=2)

    return status


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a single GitHub issue into the skill's evals.json."
    )
    parser.add_argument("--issue", required=True, help="GitHub issue number or URL")
    parser.add_argument("--repo", default=REPO, help=f"GitHub repo (default: {REPO})")
    args = parser.parse_args()

    issue_match = re.search(r"(\d+)$", args.issue)
    if not issue_match:
        print(f"Error: Could not parse issue number from '{args.issue}'", file=sys.stderr)
        sys.exit(1)

    issue_id = issue_match.group(1)

    try:
        result = subprocess.run(
            ["gh", "issue", "view", issue_id, "--repo", args.repo, "--json", "number,body,title"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: gh failed fetching issue {issue_id}: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    issue_data = json.loads(result.stdout)
    parsed = parse_issue_markdown(issue_data["body"])

    eval_entry = {
        "id": f"github-issue-{issue_data['number']}",
        "prompt": parsed.get("prompt", ""),
        "expected_output": parsed.get("expected_output", ""),
        "files": parsed.get("files", []),
        "assertions": parsed.get("assertions", []),
    }

    status = save_to_evals(eval_entry, parsed.get("skill_name", ""))
    print(status)


if __name__ == "__main__":
    main()
