#!/usr/bin/env python3
"""Pure-logic tests for judge.py (no network calls)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import judge  # noqa: E402


FAILS: list[str] = []


def check(label: str, cond: bool, hint: str = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}" + (f"   [{hint}]" if hint else ""))
        FAILS.append(label)


def test_infer_vendor():
    print("infer_vendor")
    os.environ.pop("LAZY_SKILL_CHECK_JUDGE_VENDOR", None)
    check("claude-sonnet -> anthropic", judge.infer_vendor("claude-sonnet-4-5") == "anthropic")
    check("claude-haiku -> anthropic", judge.infer_vendor("claude-haiku-4-5") == "anthropic")
    check("gpt-4o -> openai", judge.infer_vendor("gpt-4o") == "openai")
    check("gpt-5-codex -> openai", judge.infer_vendor("gpt-5-codex") == "openai")
    check("o3-mini -> openai", judge.infer_vendor("o3-mini") == "openai")
    os.environ["LAZY_SKILL_CHECK_JUDGE_VENDOR"] = "openai"
    check("override wins", judge.infer_vendor("claude-sonnet-4-5") == "openai")
    os.environ.pop("LAZY_SKILL_CHECK_JUDGE_VENDOR", None)


def test_pick_letter():
    print("pick_letter")
    check("exact A", judge.pick_letter("A") == "A")
    check("exact B", judge.pick_letter("B") == "B")
    check("TIE", judge.pick_letter("TIE") == "TIE")
    check("verbose A", judge.pick_letter("**A**\nbecause x") == "A")
    check("verbose Answer: B", judge.pick_letter("Answer: B. Clearer.") == "B")
    check("equivocal tie", judge.pick_letter("Both A and B are fine") == "TIE")
    check("empty -> tie", judge.pick_letter("") == "TIE")


def test_pick_yes_no():
    print("pick_yes_no")
    check("YES plain", judge.pick_yes_no("YES") == "YES")
    check("NO plain", judge.pick_yes_no("NO") == "NO")
    check("mixed yes", judge.pick_yes_no("  yes\n(the skill applies)") == "YES")
    check("mixed no", judge.pick_yes_no("no — another skill fits") == "NO")
    check("empty -> NO", judge.pick_yes_no("") == "NO")


def main() -> int:
    test_infer_vendor()
    test_pick_letter()
    test_pick_yes_no()
    print()
    if FAILS:
        print(f"FAIL: {len(FAILS)} assertion(s)")
        for f in FAILS:
            print(f"   - {f}")
        return 1
    print("judge: all logic tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
