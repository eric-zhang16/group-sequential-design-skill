"""
run_benchmark.py — Pure Anthropic SDK benchmark runner

Selects the next pending eval case via get_next_eval.py, calls the API for
Agent A (with skill) and Agent B (without skill) in parallel, scores each
output against assertions via LLM-as-judge, and posts the result to the
originating GitHub issue.

Usage:
    python run_benchmark.py --model claude-sonnet-4-6
    python run_benchmark.py --model claude-sonnet-4-6 --priority-skill km-digitizer
    python run_benchmark.py --model claude-sonnet-4-6 --priority-issue github-issue-3
"""

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import anthropic

REPO = "eric-zhang16/Biostatistics-skills"
REPO_ROOT = Path(__file__).resolve().parents[3]
JUDGE_MODEL = "claude-haiku-4-5-20251001"


def call_api(client: anthropic.Anthropic, model: str,
             system: str, prompt: str) -> tuple[str, float]:
    import time
    start = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text, round((time.time() - start) / 60, 1)


def judge_assertion(client: anthropic.Anthropic, assertion: str, response: str) -> str:
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content":
            f"Does the response meet the assertion? Reply with exactly one word: Pass, Partial, or Fail.\n\n"
            f"Assertion: {assertion}\n\nResponse:\n{response}"}],
    )
    v = resp.content[0].text.strip().capitalize()
    return v if v in ("Pass", "Partial", "Fail") else "Fail"


def score(verdicts: list[str]) -> tuple[float, int, int, int]:
    p, pt, f = verdicts.count("Pass"), verdicts.count("Partial"), verdicts.count("Fail")
    total = len(verdicts)
    pct = round((p + 0.5 * pt) / total * 100, 1) if total else 0.0
    return pct, p, pt, f


def build_comment(eval_case: dict, model: str,
                  resp_a: str, resp_b: str,
                  verdicts_a: list[str], verdicts_b: list[str],
                  time_a: float, time_b: float) -> str:
    skill_name = eval_case["_skill_name"]
    eval_id = eval_case["id"]
    skill_sha = eval_case["_skill_sha"]
    assertions = eval_case.get("assertions", [])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pct_a, pa, pta, fa = score(verdicts_a)
    pct_b, pb, ptb, fb = score(verdicts_b)

    lines = [
        f"## Automated Benchmark Results — `{skill_name}`",
        "",
        "### Run Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| **Eval ID** | `{eval_id}` |",
        f"| **Run date** | {now} |",
        f"| **Model** | `{model}` |",
        f"| **Skill version** | `{skill_sha}` |",
        "| **Triggered by** | GitHub Actions (workflow_dispatch) |",
        "",
        "### Scorecard",
        "",
        "| Metric | With Skill | Without Skill |",
        "|---|---|---|",
        f"| **Score** | {pct_a}% | {pct_b}% |",
        f"| **Assertions** | {pa}P {pta}Pt {fa}F | {pb}P {ptb}Pt {fb}F |",
        f"| **Execution time** | {time_a}m | {time_b}m |",
        "",
    ]

    if assertions:
        lines += [
            "<details>",
            "<summary>Assertion Breakdown</summary>",
            "",
            "| Assertion | With Skill | Without Skill |",
            "|---|---|---|",
        ]
        for i, a in enumerate(assertions):
            va = verdicts_a[i] if i < len(verdicts_a) else "N/A"
            vb = verdicts_b[i] if i < len(verdicts_b) else "N/A"
            short = (a[:80] + "…") if len(a) > 80 else a
            lines.append(f"| {short} | {va} | {vb} |")
        lines += ["", "</details>", ""]

    lines += [
        "---",
        "*Posted automatically by `benchmark-runner` · "
        "Repo: https://github.com/eric-zhang16/Biostatistics-skills*",
    ]
    return "\n".join(lines)


def post_comment(issue_id: str, body: str) -> None:
    m = re.search(r"(\d+)$", str(issue_id))
    if not m:
        print(f"Warning: cannot parse issue number from '{issue_id}'", file=sys.stderr)
        return
    tmp = Path(f"/tmp/benchmark_{issue_id}.md")
    tmp.write_text(body)
    subprocess.run(
        ["gh", "issue", "comment", m.group(1), "--repo", REPO, "--body-file", str(tmp)],
        check=True,
    )


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--priority-skill")
    parser.add_argument("--priority-issue")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(REPO_ROOT / "_automation/benchmark-runner/scripts/get_next_eval.py"),
        "--model", args.model,
    ]
    if args.priority_skill:
        cmd += ["--priority-skill", args.priority_skill]
    if args.priority_issue:
        cmd += ["--priority-issue", args.priority_issue]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    if output.startswith("STATUS: UP_TO_DATE"):
        print("All benchmarks up to date.")
        return

    eval_case = json.loads(output)
    skill_name = eval_case["_skill_name"]
    eval_id = eval_case["id"]
    skill_content = eval_case.get("_skill_content", "")
    prompt = eval_case.get("prompt", "")
    files = eval_case.get("files", [])
    assertions = eval_case.get("assertions", [])
    expected_output = eval_case.get("expected_output", "")

    if files:
        prompt += "\n\nReferenced files (provide your best answer without them): " + ", ".join(files)

    print(f"Benchmarking: skill={skill_name}  id={eval_id}")

    client = anthropic.Anthropic()
    system_a = "You are a biostatistics assistant. Use the following skill guide:\n\n" + skill_content
    system_b = "You are a biostatistics assistant. Answer using only your base knowledge."

    print("Running Agent A (with skill) and Agent B (without) in parallel...")
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(call_api, client, args.model, system_a, prompt)
        fut_b = pool.submit(call_api, client, args.model, system_b, prompt)
        resp_a, time_a = fut_a.result()
        resp_b, time_b = fut_b.result()
    print(f"Agent A: {time_a}m  Agent B: {time_b}m")

    if assertions:
        print(f"Scoring {len(assertions)} assertions...")
        verdicts_a = [judge_assertion(client, a, resp_a) for a in assertions]
        verdicts_b = [judge_assertion(client, a, resp_b) for a in assertions]
    else:
        rubric = expected_output or "Provide a complete and accurate answer."
        verdicts_a = [judge_assertion(client, f"The response fully satisfies: {rubric}", resp_a)]
        verdicts_b = [judge_assertion(client, f"The response fully satisfies: {rubric}", resp_b)]

    pct_a, *_ = score(verdicts_a)
    pct_b, *_ = score(verdicts_b)
    print(f"Score: A={pct_a}%  B={pct_b}%")

    comment = build_comment(eval_case, args.model,
                            resp_a, resp_b,
                            verdicts_a, verdicts_b,
                            time_a, time_b)

    if str(eval_id).startswith("github-issue-"):
        try:
            post_comment(str(eval_id), comment)
            print(f"Comment posted to issue {eval_id}")
        except subprocess.CalledProcessError as e:
            print(f"Warning: failed to post comment: {e}", file=sys.stderr)
    else:
        print(f"Non-issue eval ID '{eval_id}' — printing report to stdout:")
        print(comment)


if __name__ == "__main__":
    main()
