"""
Discover all skills with evals/evals.json, select the highest-priority pending
eval (one not yet benchmarked for the current skill SHA + model), and output
the eval case as JSON for the benchmark-runner skill to consume.

Skills live at: plugins/{skill_name}/skills/{skill_name}/
Evals live at:  plugins/{skill_name}/skills/{skill_name}/evals/evals.json

Usage:
    python get_next_eval.py --model claude-sonnet-4-6
    python get_next_eval.py --model claude-sonnet-4-6 --priority-skill km-digitizer
    python get_next_eval.py --model claude-sonnet-4-6 --priority-issue github-issue-3
"""

import json
import subprocess
import argparse
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = "eric-zhang16/Biostatistics-skills"
REPO_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_SIZE_LIMIT_BYTES = 100 * 1024  # 100 KB
RUNS_DIR = REPO_ROOT / "_automation" / "benchmark-runner" / "runs"


def normalize_model_name(name: str) -> str:
    return re.sub(r"[\s\-_\.]", "", name.lower())


def get_git_sha(skill_path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-n", "1", "--format=%H", "--", str(skill_path)],
            capture_output=True, text=True, check=True, cwd=str(REPO_ROOT),
        )
        sha = result.stdout.strip()
        return sha if sha else "unknown"
    except subprocess.CalledProcessError as e:
        print(f"Error: git log failed for {skill_path}: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def check_github_comments(issue_id: str, target_sha: str, target_model: str) -> bool:
    # Only check GitHub for IDs that originate from issues
    if not str(issue_id).startswith("github-issue-"):
        return False
    match = re.search(r"(\d+)$", str(issue_id))
    if not match:
        return False
    issue_number = match.group(1)

    try:
        result = subprocess.run(
            ["gh", "issue", "view", issue_number, "--repo", REPO, "--json", "comments"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        print(
            f"Warning: gh failed checking comments for issue {issue_id} — "
            f"treating as pending: {e.stderr}",
            file=sys.stderr,
        )
        return False

    data = json.loads(result.stdout)
    norm_target = normalize_model_name(target_model)

    for comment in data.get("comments", []):
        body = comment.get("body", "")
        if "Automated Benchmark Results" not in body:
            continue
        has_sha = (
            f"Skill version: `{target_sha}`" in body
            or f"**Skill version** | `{target_sha}`" in body
        )
        has_model = norm_target in normalize_model_name(body)
        if has_sha and has_model:
            return True
    return False


def write_run_manifest(eval_case: dict, model: str, skill_sha: str, status: str) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "eval_id": eval_case.get("id"),
        "skill_name": eval_case.get("_skill_name"),
        "skill_sha": skill_sha,
        "model": model,
        "run_date": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }
    manifest_path = RUNS_DIR / "runs.json"
    records = []
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                records = json.load(f)
        except (json.JSONDecodeError, OSError):
            records = []
    records.append(record)
    with open(manifest_path, "w") as f:
        json.dump(records, f, indent=2)


def discover_skills() -> list[Path]:
    """
    Discover all skill directories containing SKILL.md + evals/evals.json.
    In this repo, skills live at plugins/{skill_name}/skills/{skill_name}/.
    """
    skills: list[Path] = []
    plugins_dir = REPO_ROOT / "plugins"
    if not plugins_dir.exists():
        return skills

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        skills_subdir = plugin_dir / "skills"
        if not skills_subdir.exists():
            continue
        for skill_dir in skills_subdir.iterdir():
            if not skill_dir.is_dir():
                continue
            if (skill_dir / "SKILL.md").exists() and (skill_dir / "evals" / "evals.json").exists():
                skills.append(skill_dir)

    return skills


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select the next pending benchmark eval case."
    )
    parser.add_argument("--model", required=True, help="Model API ID (e.g. claude-sonnet-4-6)")
    parser.add_argument("--priority-skill", help="Focus on this specific skill name.")
    parser.add_argument("--priority-issue", help="Prioritize this specific issue ID (e.g. github-issue-3).")
    args = parser.parse_args()

    skills = discover_skills()

    if not skills:
        print("No skills with evals/evals.json found under plugins/.", file=sys.stderr)
        print("STATUS: UP_TO_DATE")
        return

    if args.priority_skill:
        skills.sort(key=lambda p: (0 if p.name == args.priority_skill else 1, p.name))
    else:
        skills.sort(key=lambda p: p.name)

    today_last_digit = int(str(datetime.now(timezone.utc).day)[-1])
    eligible_evals: list[dict] = []

    for skill_path in skills:
        evals_path = skill_path / "evals" / "evals.json"
        try:
            with open(evals_path) as f:
                eval_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error reading {evals_path}: {e}", file=sys.stderr)
            continue

        skill_name = eval_data.get("skill_name", skill_path.name)
        skill_sha = get_git_sha(skill_path)

        eval_cases = eval_data.get("evals", [])
        if args.priority_issue:
            eval_cases.sort(key=lambda e: (0 if str(e.get("id")) == args.priority_issue else 1))

        # Load local run manifest for deduplication of non-github-issue IDs
        local_run_keys: set[str] = set()
        manifest_path = RUNS_DIR / "runs.json"
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    for rec in json.load(f):
                        if rec.get("skill_sha") == skill_sha and \
                           normalize_model_name(rec.get("model", "")) == normalize_model_name(args.model) and \
                           rec.get("status") == "dispatched":
                            local_run_keys.add(str(rec.get("eval_id", "")))
            except (json.JSONDecodeError, OSError):
                pass

        for eval_case in eval_cases:
            eval_id = eval_case.get("id")

            already_run = str(eval_id) in local_run_keys
            if already_run:
                continue

            if not check_github_comments(str(eval_id), skill_sha, args.model):
                eval_case["_skill_name"] = skill_name
                eval_case["_skill_sha"] = skill_sha
                eval_case["_skill_dir"] = str(skill_path.relative_to(REPO_ROOT))

                with open(skill_path / "SKILL.md") as s:
                    eval_case["_skill_content"] = s.read()

                # Bundle .md and .py and .R files from skill dir, excluding evals/
                bundled: dict[str, str] = {}
                total_bytes = 0
                size_warned = False
                for root, dirs, files in os.walk(skill_path):
                    root_path = Path(root)
                    if root_path.name == "evals":
                        dirs.clear()
                        continue
                    for fname in sorted(files):
                        if not any(fname.endswith(ext) for ext in (".md", ".py", ".R")):
                            continue
                        fpath = root_path / fname
                        rel = str(fpath.relative_to(skill_path))
                        try:
                            content = fpath.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                        total_bytes += len(content.encode())
                        if total_bytes > BUNDLE_SIZE_LIMIT_BYTES and not size_warned:
                            print(
                                f"Warning: bundle for '{skill_name}' exceeds "
                                f"{BUNDLE_SIZE_LIMIT_BYTES // 1024} KB.",
                                file=sys.stderr,
                            )
                            size_warned = True
                        bundled[rel] = content
                eval_case["_bundled_resources"] = bundled
                eligible_evals.append(eval_case)

                if args.priority_issue and str(eval_id) == args.priority_issue:
                    break

        # If priority flags are set and we already have a candidate, stop scanning more skills
        if eligible_evals and (args.priority_skill or args.priority_issue):
            break

    if not eligible_evals:
        print("STATUS: UP_TO_DATE")
        return

    def get_issue_num(eval_id) -> int:
        if isinstance(eval_id, int):
            return eval_id
        match = re.search(r"(\d+)$", str(eval_id))
        return int(match.group(1)) if match else 0

    if args.priority_skill or args.priority_issue:
        # Priority flags were given — respect iteration order (first eligible wins)
        selected_eval = eligible_evals[0]
    else:
        selected_eval = min(
            eligible_evals,
            key=lambda e: (
                abs((get_issue_num(e["id"]) % 10) - today_last_digit),
                get_issue_num(e["id"])
            )
        )

    write_run_manifest(selected_eval, args.model, selected_eval["_skill_sha"], "dispatched")
    print(json.dumps(selected_eval, indent=2))


if __name__ == "__main__":
    main()
