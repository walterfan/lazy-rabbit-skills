#!/usr/bin/env python3
"""
L3 assertions: evaluate collected behavior runs against case expectations.

Usage:
    python3 evaluate_runs.py --cases <cases_dir> --runs <runs_dir> [--json]
                             [--agent claude|codex|cursor]

Pairs each <case>.yaml with <runs_dir>/<case>.json, then runs these assertions:

  - tools_used:   required tool names appear in the recorded tool calls
  - files_exist:  required files exist under the case's workdir
  - contains:     required substrings appear in the final assistant output
  - max_cost_usd / max_duration_seconds: budget guards

Per-case fields are optional — only what's specified gets checked.

Parsing is cross-agent: supports Claude Code, OpenAI Codex, and Cursor Agent
output formats via agent_runs.parse_run. Auto-detects by sniffing the payload;
pass --agent to force a parser.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed", file=sys.stderr)
    sys.exit(2)

from agent_runs import parse_run  # noqa: E402


def load_run(run_file: Path, agent_hint: str | None) -> tuple[dict, "object"]:
    raw = run_file.read_text(encoding="utf-8")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        envelope = {"_skilltest": {}}
    skilltest = (envelope.get("_skilltest") if isinstance(envelope, dict) else None) or {}
    payload_text = skilltest.get("payload_text")
    if not payload_text:
        if isinstance(envelope, dict):
            payload = {k: v for k, v in envelope.items() if k != "_skilltest"}
            payload_text = json.dumps(payload)
        else:
            payload_text = raw
    hint = agent_hint or skilltest.get("agent")
    parsed = parse_run(payload_text, agent_hint=hint)
    return skilltest, parsed


def evaluate_case(case: dict, skilltest: dict, parsed) -> dict:
    expect = case.get("expect") or {}
    failures: list[str] = []

    tools = parsed.tool_names
    for required in expect.get("tools_used", []) or []:
        if required not in tools:
            failures.append(f"tool_used: expected '{required}', observed {tools}")

    workdir = Path(skilltest.get("workdir", ""))
    for rel in expect.get("files_exist", []) or []:
        target = workdir / rel
        if not target.exists():
            failures.append(f"file_exist: {rel} not found under {workdir}")

    final_text = parsed.final_text or ""
    for needle in expect.get("contains", []) or []:
        if needle not in final_text:
            failures.append(f"contains: '{needle}' missing from final output")

    max_cost = expect.get("max_cost_usd")
    if isinstance(max_cost, (int, float)):
        cost = parsed.cost_usd
        if isinstance(cost, (int, float)) and cost > max_cost:
            failures.append(f"cost: ${cost:.4f} > ${max_cost:.4f}")

    max_dur = expect.get("max_duration_seconds")
    if isinstance(max_dur, (int, float)):
        dur = skilltest.get("duration_seconds")
        if isinstance(dur, (int, float)) and dur > max_dur:
            failures.append(f"duration: {dur}s > {max_dur}s")

    return {
        "passed": not failures,
        "failures": failures,
        "tools_observed": tools,
        "agent": parsed.agent,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--agent",
        choices=["claude", "codex", "cursor"],
        default=None,
        help="force agent parser; defaults to auto-detect / run metadata",
    )
    args = parser.parse_args()

    cases_dir = Path(args.cases).resolve()
    runs_dir = Path(args.runs).resolve()

    report: dict = {"total": 0, "passed": 0, "failed": 0, "cases": []}

    for case_file in sorted(
        list(cases_dir.glob("*.yaml")) + list(cases_dir.glob("*.yml"))
    ):
        case = yaml.safe_load(case_file.read_text(encoding="utf-8")) or {}
        run_file = runs_dir / (case_file.stem + ".json")
        if not run_file.exists():
            report["cases"].append(
                {"case": case_file.name, "passed": False, "failures": ["no run output"]}
            )
            report["failed"] += 1
            report["total"] += 1
            continue
        try:
            skilltest, parsed = load_run(run_file, args.agent)
        except Exception as exc:  # defensive; never let evaluator crash
            report["cases"].append(
                {"case": case_file.name, "passed": False, "failures": [f"parse error: {exc}"]}
            )
            report["failed"] += 1
            report["total"] += 1
            continue

        verdict = evaluate_case(case, skilltest, parsed)
        report["cases"].append({"case": case_file.name, **verdict})
        report["total"] += 1
        if verdict["passed"]:
            report["passed"] += 1
        else:
            report["failed"] += 1

    report["rate"] = (report["passed"] / report["total"]) if report["total"] else 0.0
    all_pass = report["failed"] == 0

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if all_pass else "FAIL"
        print(f"[L3 behavior eval] {status}  {report['passed']}/{report['total']} cases passed")
        for c in report["cases"]:
            if c["passed"]:
                print(f"  OK     {c['case']}  (agent={c.get('agent', '?')})")
            else:
                print(f"  FAIL   {c['case']}  (agent={c.get('agent', '?')})")
                for f in c.get("failures", []):
                    print(f"           - {f}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
