#!/usr/bin/env python3
"""
lazyskillcheck — unified entrypoint for the lazy-skill-check pyramid.

Subcommands:
  lint       run L1 structural lint
  trigger    run L2 trigger precision eval
  behavior   run L3 behavior eval (agent spawn + assertions)
  benchmark  run L4 A/B benchmark
  gen        scaffold trigger-cases.yaml / behavior/ starter from SKILL.md
  all        run lint -> trigger -> behavior (skipping stages with no cases)
  selftest   run the bundled unit tests (agent_runs, judge, evaluate_runs)

Common options live on subcommands; run `lazyskillcheck <subcmd> --help` for details.

Design notes:
  - This CLI is a THIN DISPATCHER. Real logic stays in the per-stage scripts so
    they can be used directly from CI without going through lazyskillcheck.py.
  - By default we use the Python interpreter that runs us; override with
    LAZY_SKILL_CHECK_PYTHON if the project needs a specific venv.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = os.environ.get("LAZY_SKILL_CHECK_PYTHON") or sys.executable

LINT = HERE / "lint.py"
TRIGGER = HERE / "trigger_eval.py"
BEHAVIOR = HERE / "behavior_run.sh"
EVALUATE = HERE / "evaluate_runs.py"
BENCHMARK = HERE / "benchmark.py"


def _run(cmd: list[str], *, env: dict | None = None) -> int:
    print(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, env=env)
    return res.returncode


# ---------- subcommands ----------

def cmd_lint(args) -> int:
    return _run([PY, str(LINT), str(args.skill)])


def cmd_trigger(args) -> int:
    cases = args.cases or (Path(args.skill) / "references" / "trigger-cases.yaml")
    if not Path(cases).exists():
        print(f"[lazyskillcheck trigger] no cases file: {cases}", file=sys.stderr)
        return 2
    cmd = [
        PY, str(TRIGGER),
        "--skill", str(args.skill),
        "--cases", str(cases),
        "--judge-model", args.judge_model,
    ]
    if args.judge_vendor:
        cmd += ["--judge-vendor", args.judge_vendor]
    if args.json:
        cmd.append("--json")
    if args.f1_threshold is not None:
        cmd += ["--f1-threshold", str(args.f1_threshold)]
    return _run(cmd)


def cmd_behavior(args) -> int:
    cases_dir = args.cases_dir or (Path(args.skill) / "references" / "behavior")
    output_dir = args.output or (Path(".") / "skill-test-runs")
    if not Path(cases_dir).exists():
        print(f"[lazyskillcheck behavior] no cases dir: {cases_dir}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    if args.agent:
        env["LAZY_SKILL_CHECK_AGENT"] = args.agent
    if args.model:
        env["LAZY_SKILL_CHECK_MODEL"] = args.model

    rc = _run(
        ["bash", str(BEHAVIOR), str(args.skill), str(cases_dir), str(output_dir)],
        env=env,
    )
    if rc != 0 and not args.keep_going:
        return rc
    # assertions
    eval_cmd = [PY, str(EVALUATE), "--cases", str(cases_dir), "--runs", str(output_dir)]
    if args.json:
        eval_cmd.append("--json")
    if args.agent:
        eval_cmd += ["--agent", args.agent]
    return _run(eval_cmd)


def cmd_benchmark(args) -> int:
    cmd = [
        PY, str(BENCHMARK),
        "--v1", str(args.v1),
        "--v2", str(args.v2),
        "--cases", str(args.cases),
        "--output", str(args.output),
        "--repeat", str(args.repeat),
        "--judge-model", args.judge_model,
    ]
    if args.judge_vendor:
        cmd += ["--judge-vendor", args.judge_vendor]
    if args.no_judge:
        cmd.append("--no-judge")
    return _run(cmd)


def cmd_all(args) -> int:
    """Fan-through: lint -> trigger -> behavior. Stops on first fatal lint error."""
    rc = cmd_lint(args)
    if rc != 0 and not args.continue_on_fail:
        return rc

    trig_cases = Path(args.skill) / "references" / "trigger-cases.yaml"
    if trig_cases.exists():
        class T:
            skill = args.skill
            cases = trig_cases
            judge_model = args.judge_model
            judge_vendor = args.judge_vendor
            json = False
            f1_threshold = args.f1_threshold
        rc_t = cmd_trigger(T())
        if rc_t != 0 and not args.continue_on_fail:
            return rc_t
    else:
        print("[lazyskillcheck all] skipping L2 trigger (no trigger-cases.yaml)")

    beh_dir = Path(args.skill) / "references" / "behavior"
    if beh_dir.exists() and any(beh_dir.glob("*.yaml")):
        class B:
            skill = args.skill
            cases_dir = beh_dir
            output = Path(args.output_runs)
            agent = args.agent
            model = args.model
            json = False
            keep_going = args.continue_on_fail
        return cmd_behavior(B())
    else:
        print("[lazyskillcheck all] skipping L3 behavior (no behavior/*.yaml)")
        return 0


def cmd_gen(args) -> int:
    """Scaffold test case files from a SKILL.md description (offline, no LLM)."""
    import re

    skill_dir = Path(args.skill).resolve()
    skill_md = None
    for name in ("SKILL.md", "skill.md"):
        if (skill_dir / name).exists():
            skill_md = skill_dir / name
            break
    if skill_md is None:
        print(f"[lazyskillcheck gen] no SKILL.md in {skill_dir}", file=sys.stderr)
        return 2

    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        print("[lazyskillcheck gen] no YAML frontmatter", file=sys.stderr)
        return 2

    try:
        import yaml
    except ImportError:
        print("[lazyskillcheck gen] PyYAML not installed", file=sys.stderr)
        return 2

    fm = yaml.safe_load(m.group(1)) or {}
    name = str(fm.get("name") or skill_dir.name)
    description = str(fm.get("description") or "").strip()

    refs = skill_dir / "references"
    refs.mkdir(parents=True, exist_ok=True)
    trigger_path = refs / "trigger-cases.yaml"
    behavior_dir = refs / "behavior"
    behavior_dir.mkdir(parents=True, exist_ok=True)

    # heuristic pull first sentence of description as the positive pivot
    first_sentence = description.split(".")[0].split("。")[0][:200] if description else name
    trigger_stub = (
        f"# trigger-cases for skill: {name}\n"
        "# Positive cases (expect: trigger) — user prompts the skill should fire on.\n"
        "# Negative cases (expect: no-trigger) — prompts that must NOT fire the skill.\n"
        "cases:\n"
        f"  - prompt: \"{first_sentence}\"\n"
        "    expect: trigger\n"
        "  - prompt: \"hello, how are you?\"\n"
        "    expect: no-trigger\n"
        "  - prompt: \"what time is it?\"\n"
        "    expect: no-trigger\n"
    )
    if trigger_path.exists() and not args.force:
        print(f"[lazyskillcheck gen] {trigger_path} exists (use --force to overwrite)")
    else:
        trigger_path.write_text(trigger_stub, encoding="utf-8")
        print(f"[lazyskillcheck gen] wrote {trigger_path}")

    behavior_stub_path = behavior_dir / "smoke.yaml"
    behavior_stub = (
        f"# behavior case for skill: {name}\n"
        f"prompt: \"{first_sentence}\"\n"
        "setup: []\n"
        "expect:\n"
        "  contains: []            # keywords that must appear in the final output\n"
        "  tools_used: []          # tools the skill is supposed to invoke\n"
        "  files_exist: []         # files that must exist under the scratch workdir\n"
        "  max_cost_usd: 0.10\n"
        "  max_duration_seconds: 120\n"
    )
    if behavior_stub_path.exists() and not args.force:
        print(f"[lazyskillcheck gen] {behavior_stub_path} exists (use --force to overwrite)")
    else:
        behavior_stub_path.write_text(behavior_stub, encoding="utf-8")
        print(f"[lazyskillcheck gen] wrote {behavior_stub_path}")
    return 0


def cmd_selftest(args) -> int:
    """Run the bundled unit tests."""
    suites = [
        HERE / "test_agent_runs.py",
        HERE / "test_judge.py",
        HERE / "test_evaluate_runs.py",
    ]
    failures: list[str] = []
    for suite in suites:
        if not suite.exists():
            continue
        print(f"\n=== {suite.name} ===")
        rc = _run([PY, str(suite)])
        if rc != 0:
            failures.append(suite.name)
    print()
    if failures:
        print(f"[lazyskillcheck selftest] FAIL: {', '.join(failures)}")
        return 1
    print("[lazyskillcheck selftest] all suites passed")
    return 0


# ---------- parser wiring ----------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="lazyskillcheck",
        description="AI skill test pyramid runner (lint / trigger / behavior / benchmark)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="L1 structural lint")
    p.add_argument("skill")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("trigger", help="L2 trigger precision eval")
    p.add_argument("skill")
    p.add_argument("--cases")
    p.add_argument("--judge-model", default="claude-haiku-4-5")
    p.add_argument("--judge-vendor", choices=["anthropic", "openai"])
    p.add_argument("--f1-threshold", type=float, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_trigger)

    p = sub.add_parser("behavior", help="L3 behavior eval")
    p.add_argument("skill")
    p.add_argument("--cases-dir")
    p.add_argument("--output")
    p.add_argument("--agent", choices=["claude", "codex", "cursor"], default=None)
    p.add_argument("--model")
    p.add_argument("--json", action="store_true")
    p.add_argument("--keep-going", action="store_true",
                   help="run eval even if some behavior spawns failed")
    p.set_defaults(func=cmd_behavior)

    p = sub.add_parser("benchmark", help="L4 A/B benchmark")
    p.add_argument("--v1", required=True)
    p.add_argument("--v2", required=True)
    p.add_argument("--cases", required=True)
    p.add_argument("--output", default="skill-test-reports")
    p.add_argument("--repeat", type=int, default=3)
    p.add_argument("--judge-model", default="claude-sonnet-4-5")
    p.add_argument("--judge-vendor", choices=["anthropic", "openai"])
    p.add_argument("--no-judge", action="store_true")
    p.set_defaults(func=cmd_benchmark)

    p = sub.add_parser("all", help="run lint -> trigger -> behavior")
    p.add_argument("skill")
    p.add_argument("--judge-model", default="claude-haiku-4-5")
    p.add_argument("--judge-vendor", choices=["anthropic", "openai"])
    p.add_argument("--f1-threshold", type=float, default=None)
    p.add_argument("--agent", choices=["claude", "codex", "cursor"], default=None)
    p.add_argument("--model")
    p.add_argument("--output-runs", default="skill-test-runs")
    p.add_argument("--continue-on-fail", action="store_true")
    p.set_defaults(func=cmd_all)

    p = sub.add_parser("gen", help="scaffold trigger and behavior case templates")
    p.add_argument("skill")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing scaffold files")
    p.set_defaults(func=cmd_gen)

    p = sub.add_parser("selftest", help="run bundled unit tests")
    p.set_defaults(func=cmd_selftest)

    return ap


def main() -> int:
    ap = build_parser()
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
