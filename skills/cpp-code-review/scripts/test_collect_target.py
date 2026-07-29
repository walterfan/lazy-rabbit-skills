#!/usr/bin/env python3
"""Regression tests for collect_target.py — focused on the usability contracts:

  1. --diff / --staged outside a git repo returns a CONCISE error (code
     `not_a_git_repo`) with next-step suggestions — never a raw git help dump.
  2. --diff in a repo with no commits returns `no_valid_head`, not a git dump.
  3. When the C++ standard cannot be detected, the context/JSON explains WHY and
     tells the user to pass `--std c++17`.
  4. `--format json` emits a STABLE structured contract for automation, both on
     success (`ok: true` + context/scope/prompt) and on error (`ok: false` +
     error.code/message/suggestions).

Run: python3 scripts/test_collect_target.py
No network, no external deps — just python3 + git.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "collect_target.py"

_passed = 0
_failed = 0


def run(args, cwd):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    return proc.returncode, proc.stdout, proc.stderr


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print("  PASS  " + name)
    else:
        _failed += 1
        print("  FAIL  " + name + ("  -- " + detail if detail else ""))


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def test_non_git_diff():
    print("[1] --diff outside a git repo")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "socket.cpp").write_text("int main(){int* p=new int; return *p;}\n")

        # text mode
        rc, out, err = run(["--diff", "--project-root", "."], d)
        check("exit code 1", rc == 1, "rc=%d" % rc)
        check("mentions not a git repository", "not inside a git repository" in err)
        check("has next-step suggestion", "Next step 1" in err)
        # The crucial regression: no git usage/help dump leaking through.
        for noise in ("usage: git diff", "--find-renames", "Diff output format options"):
            check("no git help noise: %r" % noise, noise not in err and noise not in out)

        # json mode
        rc, out, err = run(["--diff", "--format", "json", "--project-root", "."], d)
        check("json exit code 1", rc == 1, "rc=%d" % rc)
        obj = json.loads(out)
        check("json ok=false", obj.get("ok") is False)
        check("json error.code=not_a_git_repo", obj["error"]["code"] == "not_a_git_repo")
        check("json has suggestions", len(obj["error"]["suggestions"]) >= 1)


def test_no_head():
    print("[2] --diff in a repo with no commits")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q")
        (d / "a.cpp").write_text("int f(){return 0;}\n")
        rc, out, err = run(["--diff", "--project-root", "."], d)
        check("exit code 1", rc == 1, "rc=%d" % rc)
        check("mentions no commits / valid HEAD", "no valid HEAD" in err or "no commits" in err)
        check("no git help noise", "usage: git" not in err)


def test_standard_hint():
    print("[3] unknown C++ standard -> actionable hint")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "socket.cpp").write_text("int main(){return 0;}\n")
        rc, out, err = run(
            ["socket.cpp", "--focus", "modern-cpp", "--format", "context", "--project-root", "."],
            d,
        )
        check("exit code 0", rc == 0, "rc=%d err=%s" % (rc, err))
        check("standard unknown noted", "C++ standard unknown" in out)
        check("suggests --std c++17", "--std c++17" in out)
        check("explains reason", "no build system" in out or "declare no" in out)


def test_json_success():
    print("[4] --format json success contract")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "socket.cpp").write_text("int main(){int* p=new int; return *p;}\n")
        rc, out, err = run(
            ["socket.cpp", "--focus", "memory", "--std", "c++17", "--format", "json",
             "--project-root", "."],
            d,
        )
        check("exit code 0", rc == 0, "rc=%d err=%s" % (rc, err))
        obj = json.loads(out)
        check("ok=true", obj.get("ok") is True)
        for key in ("language", "focus", "scope", "context", "project_context_md", "code", "prompt"):
            check("has top-level key %r" % key, key in obj)
        check("focus=memory", obj["focus"] == "memory")
        check("context.cpp_standard=C++17", obj["context"]["cpp_standard"] == "C++17")
        check("context.cpp_standard_known=true", obj["context"]["cpp_standard_known"] is True)
        check("scope.mode=files", obj["scope"]["mode"] == "files")
        check("scope.changed_files lists socket.cpp",
              "socket.cpp" in obj["scope"]["changed_files"])
        check("prompt non-empty", isinstance(obj["prompt"], str) and len(obj["prompt"]) > 0)


def test_unsupported_focus_json():
    print("[5] unsupported focus -> stable json error")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "a.cpp").write_text("int f(){return 0;}\n")
        rc, out, err = run(["a.cpp", "--focus", "bogus", "--format", "json", "--project-root", "."], d)
        check("exit code 2", rc == 2, "rc=%d" % rc)
        obj = json.loads(out)
        check("ok=false", obj.get("ok") is False)
        check("error.code=unsupported_focus", obj["error"]["code"] == "unsupported_focus")


def main() -> int:
    test_non_git_diff()
    test_no_head()
    test_standard_hint()
    test_json_success()
    test_unsupported_focus_json()
    print("\n%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
