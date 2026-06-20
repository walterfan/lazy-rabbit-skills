#!/usr/bin/env python3
"""
L4: A/B benchmark for two skill versions.

Given v1 and v2 skill directories and a shared cases directory, run each case
N times against each version using behavior_run.sh, then aggregate:

  - pass rate, average cost, average duration, avg tool-call count per version
  - optional blind pairwise judging: randomly order v1/v2 outputs and ask a
    stronger model which is better for the user's prompt

Outputs a markdown report to <output>/benchmark-<timestamp>.md .

Usage:
    python3 benchmark.py \
        --v1 <skill_dir_v1> \
        --v2 <skill_dir_v2> \
        --cases <cases_dir> \
        --output <report_dir> \
        [--repeat 3] \
        [--judge-model claude-sonnet-4-5] \
        [--no-judge]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed", file=sys.stderr)
    sys.exit(2)

import judge as judge_mod  # noqa: E402
from agent_runs import parse_run  # noqa: E402


BEHAVIOR_RUN = HERE / "behavior_run.sh"
EVALUATE_RUNS = HERE / "evaluate_runs.py"


def run_version(label: str, skill_dir: Path, cases_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["LAZY_SKILL_CHECK_LABEL"] = label

    subprocess.run(
        ["bash", str(BEHAVIOR_RUN), str(skill_dir), str(cases_dir), str(out_dir)],
        check=False,
        env=env,
    )

    proc = subprocess.run(
        [sys.executable, str(EVALUATE_RUNS), "--cases", str(cases_dir), "--runs", str(out_dir), "--json"],
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"total": 0, "passed": 0, "failed": 0, "rate": 0.0, "cases": []}


def _load_envelope(path: Path) -> tuple[dict, "object"]:
    """Mirror of evaluate_runs.load_run without the circular import."""
    raw = path.read_text(encoding="utf-8")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        envelope = {"_skilltest": {}}
    skilltest = (envelope.get("_skilltest") if isinstance(envelope, dict) else None) or {}
    payload_text = skilltest.get("payload_text")
    if not payload_text:
        payload = {k: v for k, v in envelope.items() if k != "_skilltest"} \
            if isinstance(envelope, dict) else {}
        payload_text = json.dumps(payload) if payload else raw
    return skilltest, parse_run(payload_text, agent_hint=skilltest.get("agent"))


def aggregate_runs(runs_dir: Path) -> dict:
    costs: list[float] = []
    durations: list[float] = []
    tool_counts: list[int] = []
    for f in runs_dir.glob("*.json"):
        try:
            skilltest, parsed = _load_envelope(f)
        except Exception:
            continue
        if isinstance(parsed.cost_usd, (int, float)):
            costs.append(float(parsed.cost_usd))
        dur = skilltest.get("duration_seconds")
        if isinstance(dur, (int, float)):
            durations.append(float(dur))
        tool_counts.append(len(parsed.tool_names))
    return {
        "avg_cost_usd": round(statistics.mean(costs), 4) if costs else None,
        "avg_duration_seconds": round(statistics.mean(durations), 2) if durations else None,
        "avg_tool_calls": round(statistics.mean(tool_counts), 2) if tool_counts else None,
    }


BLIND_JUDGE_TEMPLATE = """\
You are evaluating two assistant responses to the same user task.

User task:
---
{prompt}
---

Response A:
---
{a_text}
---

Response B:
---
{b_text}
---

Which response better completes the task? Consider correctness, efficiency, and
clarity. Answer with exactly one of: A, B, TIE.
Output only the letter/word on a single line.
"""


def blind_judge(
    prompt: str,
    a_text: str,
    b_text: str,
    model: str,
    *,
    vendor: str | None,
) -> str:
    q = BLIND_JUDGE_TEMPLATE.format(
        prompt=prompt, a_text=a_text[:4000], b_text=b_text[:4000]
    )
    try:
        res = judge_mod.ask(model, q, vendor=vendor, max_tokens=8, timeout=45.0)
    except Exception:
        return "TIE"
    return judge_mod.pick_letter(res.text)


def _final_text_of(run_path: Path) -> str:
    try:
        _, parsed = _load_envelope(run_path)
        return parsed.final_text or ""
    except Exception:
        return run_path.read_text(encoding="utf-8", errors="replace")


def run_ab_judge(
    v1_runs: Path,
    v2_runs: Path,
    cases_dir: Path,
    model: str,
    *,
    vendor: str | None,
) -> list[dict]:
    """Pairwise blind judge. Order is randomized per case to reduce bias."""
    verdicts: list[dict] = []
    for case_file in sorted(list(cases_dir.glob("*.yaml")) + list(cases_dir.glob("*.yml"))):
        case = yaml.safe_load(case_file.read_text(encoding="utf-8")) or {}
        prompt = case.get("prompt", "")
        v1_out = v1_runs / (case_file.stem + ".json")
        v2_out = v2_runs / (case_file.stem + ".json")
        if not (v1_out.exists() and v2_out.exists()):
            continue

        v1_text = _final_text_of(v1_out)
        v2_text = _final_text_of(v2_out)

        swap = random.choice([False, True])
        a, b = (v2_text, v1_text) if swap else (v1_text, v2_text)
        raw = blind_judge(prompt, a, b, model, vendor=vendor)
        if raw == "TIE":
            winner = "tie"
        else:
            winner = "v1" if ((raw == "A") ^ swap) else "v2"

        verdicts.append(
            {"case": case_file.name, "winner": winner, "raw": raw, "swap": swap}
        )
    return verdicts


def render_report(
    *,
    v1_dir: Path,
    v2_dir: Path,
    cases_dir: Path,
    repeat: int,
    v1_agg: dict,
    v2_agg: dict,
    v1_eval: dict,
    v2_eval: dict,
    verdicts: list[dict] | None,
    model: str,
) -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    lines.append(f"# Skill A/B Benchmark Report")
    lines.append("")
    lines.append(f"- Generated: {now}")
    lines.append(f"- v1: `{v1_dir}`")
    lines.append(f"- v2: `{v2_dir}`")
    lines.append(f"- cases: `{cases_dir}`  repeat={repeat}")
    lines.append(f"- judge model: `{model}`")
    lines.append("")
    lines.append("## Quantitative")
    lines.append("")
    lines.append("| metric | v1 | v2 |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| pass rate | {v1_eval.get('rate', 0):.2%} ({v1_eval.get('passed', 0)}/{v1_eval.get('total', 0)}) | {v2_eval.get('rate', 0):.2%} ({v2_eval.get('passed', 0)}/{v2_eval.get('total', 0)}) |")
    lines.append(f"| avg cost (USD) | {v1_agg.get('avg_cost_usd')} | {v2_agg.get('avg_cost_usd')} |")
    lines.append(f"| avg duration (s) | {v1_agg.get('avg_duration_seconds')} | {v2_agg.get('avg_duration_seconds')} |")
    lines.append(f"| avg tool calls | {v1_agg.get('avg_tool_calls')} | {v2_agg.get('avg_tool_calls')} |")
    lines.append("")

    if verdicts:
        win_v1 = sum(1 for v in verdicts if v["winner"] == "v1")
        win_v2 = sum(1 for v in verdicts if v["winner"] == "v2")
        tie = sum(1 for v in verdicts if v["winner"] == "tie")
        lines.append("## Blind Pairwise Judge")
        lines.append("")
        lines.append(f"- v1 wins: {win_v1}")
        lines.append(f"- v2 wins: {win_v2}")
        lines.append(f"- ties:    {tie}")
        lines.append("")
        lines.append("| case | winner |")
        lines.append("| --- | --- |")
        for v in verdicts:
            lines.append(f"| {v['case']} | {v['winner']} |")
        lines.append("")

    lines.append("## Verdict")
    lines.append("")
    v2_better_quant = (
        (v2_eval.get("rate", 0) > v1_eval.get("rate", 0))
        or (
            v2_eval.get("rate", 0) == v1_eval.get("rate", 0)
            and (v2_agg.get("avg_cost_usd") or 0) < (v1_agg.get("avg_cost_usd") or 0)
        )
    )
    if verdicts:
        win_v2 = sum(1 for v in verdicts if v["winner"] == "v2")
        win_v1 = sum(1 for v in verdicts if v["winner"] == "v1")
        v2_better_qual = win_v2 > win_v1
    else:
        v2_better_qual = None

    if v2_better_quant and (v2_better_qual is not False):
        lines.append("**Recommendation: merge v2.** Quantitative metrics favor v2 and "
                     "pairwise judgments do not contradict.")
    elif not v2_better_quant and v2_better_qual is False:
        lines.append("**Recommendation: hold v2.** Both quantitative and qualitative signals "
                     "favor v1; investigate what v2 regressed on.")
    else:
        lines.append("**Recommendation: needs more data.** Mixed signals between "
                     "quantitative and qualitative. Try increasing --repeat or adding cases.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1", required=True)
    parser.add_argument("--v2", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--output", default="skill-test-reports")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--judge-model", default="claude-sonnet-4-5")
    parser.add_argument(
        "--judge-vendor",
        choices=[judge_mod.VENDOR_ANTHROPIC, judge_mod.VENDOR_OPENAI],
        default=None,
        help="force judge vendor; defaults to inferring from --judge-model",
    )
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    v1_dir = Path(args.v1).resolve()
    v2_dir = Path(args.v2).resolve()
    cases_dir = Path(args.cases).resolve()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_root = out_dir / f"benchmark_{stamp}"

    v1_eval_totals: list[dict] = []
    v2_eval_totals: list[dict] = []

    for i in range(1, args.repeat + 1):
        print(f"\n=== iteration {i}/{args.repeat} ===")
        v1_runs = runs_root / f"v1_iter{i}"
        v2_runs = runs_root / f"v2_iter{i}"
        v1_eval_totals.append(run_version("v1", v1_dir, cases_dir, v1_runs))
        v2_eval_totals.append(run_version("v2", v2_dir, cases_dir, v2_runs))

    def avg_eval(totals: list[dict]) -> dict:
        total = sum(t.get("total", 0) for t in totals)
        passed = sum(t.get("passed", 0) for t in totals)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "rate": (passed / total) if total else 0.0,
        }

    v1_eval = avg_eval(v1_eval_totals)
    v2_eval = avg_eval(v2_eval_totals)

    last_v1_runs = runs_root / f"v1_iter{args.repeat}"
    last_v2_runs = runs_root / f"v2_iter{args.repeat}"
    v1_agg = aggregate_runs(last_v1_runs)
    v2_agg = aggregate_runs(last_v2_runs)

    verdicts: list[dict] = []
    if not args.no_judge:
        verdicts = run_ab_judge(
            last_v1_runs,
            last_v2_runs,
            cases_dir,
            args.judge_model,
            vendor=args.judge_vendor,
        )

    report = render_report(
        v1_dir=v1_dir, v2_dir=v2_dir, cases_dir=cases_dir,
        repeat=args.repeat,
        v1_agg=v1_agg, v2_agg=v2_agg,
        v1_eval=v1_eval, v2_eval=v2_eval,
        verdicts=verdicts, model=args.judge_model,
    )
    report_path = out_dir / f"benchmark_{stamp}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n[L4 benchmark] report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
