#!/usr/bin/env python3
"""
L2: trigger precision evaluation.

Given a skill's description and a set of prompts with expected
trigger/no-trigger labels, ask a judge LLM whether the skill would
be triggered, then compute precision/recall/F1.

Usage:
    python3 trigger_eval.py \
        --skill <skill_dir> \
        --cases <trigger-cases.yaml> \
        [--judge-model claude-haiku-4-5] \
        [--json]

trigger-cases.yaml format:
    cases:
      - prompt: "fill out this PDF form"
        expect: trigger
      - prompt: "read me the contract"
        expect: no-trigger

Backend: calls Anthropic's Messages API if ANTHROPIC_API_KEY is set.
Falls back to `claude -p` (Claude Code CLI) if available.
Either way, it only asks yes/no per case — cheap and fast.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

import judge as judge_mod  # noqa: E402


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

JUDGE_PROMPT_TEMPLATE = """\
You are a router inside an AI assistant. Several skills are installed.
One of them has this description:

---
{description}
---

A user just said:

    {user_prompt}

Decide: should the assistant trigger this skill?

Answer with exactly ONE word on a single line:
  YES   — this skill is a good match for the user's request
  NO    — this skill does not match; another skill or plain chat should handle it

Do not explain. Output only YES or NO.
"""


@dataclass
class Case:
    prompt: str
    expect: str  # "trigger" or "no-trigger"


@dataclass
class Result:
    case: Case
    predicted: str  # "trigger" or "no-trigger"
    raw: str


def load_description(skill_dir: Path) -> str:
    for name in ("SKILL.md", "skill.md"):
        p = skill_dir / name
        if p.exists():
            text = p.read_text(encoding="utf-8")
            m = FRONTMATTER_RE.match(text)
            if not m:
                raise SystemExit(f"{p} has no YAML frontmatter")
            fm = yaml.safe_load(m.group(1)) or {}
            desc = fm.get("description")
            if not desc:
                raise SystemExit(f"{p} frontmatter has no description")
            return str(desc)
    raise SystemExit(f"no SKILL.md in {skill_dir}")


def load_cases(cases_path: Path) -> list[Case]:
    data = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    raw = data.get("cases", []) if isinstance(data, dict) else data
    cases: list[Case] = []
    for item in raw:
        expect = str(item.get("expect", "")).strip().lower()
        if expect not in ("trigger", "no-trigger"):
            raise SystemExit(
                f"case expect must be 'trigger' or 'no-trigger', got: {expect!r}"
            )
        cases.append(Case(prompt=str(item["prompt"]), expect=expect))
    if not cases:
        raise SystemExit("no cases found")
    return cases


def evaluate(
    description: str,
    cases: list[Case],
    model: str,
    vendor: str | None,
) -> list[Result]:
    results: list[Result] = []
    for case in cases:
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            description=description, user_prompt=case.prompt
        )
        try:
            jr = judge_mod.ask(model, prompt, vendor=vendor, max_tokens=8, timeout=45.0)
            raw = jr.text
        except Exception as exc:
            raise SystemExit(f"judge failed for model={model}: {exc}")
        yn = judge_mod.pick_yes_no(raw)
        predicted = "trigger" if yn == "YES" else "no-trigger"
        results.append(Result(case=case, predicted=predicted, raw=raw))
    return results


def metrics(results: list[Result]) -> dict:
    tp = sum(1 for r in results if r.case.expect == "trigger" and r.predicted == "trigger")
    fp = sum(1 for r in results if r.case.expect == "no-trigger" and r.predicted == "trigger")
    fn = sum(1 for r in results if r.case.expect == "trigger" and r.predicted == "no-trigger")
    tn = sum(1 for r in results if r.case.expect == "no-trigger" and r.predicted == "no-trigger")

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(results) if results else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "total": len(results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L2 trigger precision evaluation")
    parser.add_argument("--skill", required=True, help="skill directory")
    parser.add_argument("--cases", required=True, help="trigger cases YAML")
    parser.add_argument("--judge-model", default="claude-haiku-4-5")
    parser.add_argument(
        "--judge-vendor",
        choices=[judge_mod.VENDOR_ANTHROPIC, judge_mod.VENDOR_OPENAI],
        default=None,
        help="force vendor; defaults to inferring from model id",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--f1-threshold", type=float, default=0.85)
    args = parser.parse_args()

    description = load_description(Path(args.skill).resolve())
    cases = load_cases(Path(args.cases).resolve())
    results = evaluate(description, cases, args.judge_model, args.judge_vendor)
    m = metrics(results)
    passed = m["f1"] >= args.f1_threshold

    failures = [
        {
            "prompt": r.case.prompt,
            "expect": r.case.expect,
            "predicted": r.predicted,
        }
        for r in results
        if r.case.expect != r.predicted
    ]

    output = {
        "passed": passed,
        "metrics": m,
        "threshold": {"f1": args.f1_threshold},
        "failures": failures,
        "judge_model": args.judge_model,
        "judge_vendor": args.judge_vendor or judge_mod.infer_vendor(args.judge_model),
    }

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if passed else "FAIL"
        vendor = args.judge_vendor or judge_mod.infer_vendor(args.judge_model)
        print(f"[L2 trigger eval] {status} (judge={args.judge_model} vendor={vendor})")
        print(
            f"  precision={m['precision']:.2f} "
            f"recall={m['recall']:.2f} "
            f"f1={m['f1']:.2f} "
            f"accuracy={m['accuracy']:.2f} "
            f"(tp={m['tp']}, fp={m['fp']}, fn={m['fn']}, tn={m['tn']})"
        )
        for f in failures:
            print(f"  MISS   expected={f['expect']:<10} got={f['predicted']:<10} :: {f['prompt']}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
