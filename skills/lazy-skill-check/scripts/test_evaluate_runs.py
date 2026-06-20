#!/usr/bin/env python3
"""
End-to-end tests for evaluate_runs.py across all three agents.

We build a fake runs_dir with synthetic envelope files (as behavior_run.sh
would produce) and a matching cases_dir, then invoke evaluate_runs.main().
No real agent CLI is spawned.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import evaluate_runs  # noqa: E402


FAILS: list[str] = []


def check(label: str, cond: bool, hint: str = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}" + (f"   [{hint}]" if hint else ""))
        FAILS.append(label)


def envelope(agent: str, workdir: str, duration: int, payload_text: str) -> str:
    out = {
        "_skilltest": {
            "agent": agent,
            "workdir": workdir,
            "duration_seconds": duration,
            "exit_code": 0,
            "payload_text": payload_text,
        }
    }
    return json.dumps(out, ensure_ascii=False)


def write_case(dst: Path, prompt: str, expect: dict) -> None:
    import yaml
    dst.write_text(yaml.safe_dump({"prompt": prompt, "expect": expect}), encoding="utf-8")


def run_evaluator(cases_dir: Path, runs_dir: Path) -> dict:
    """Invoke main() via argv; capture stdout JSON."""
    import contextlib
    import io

    saved = sys.argv
    sys.argv = [
        "evaluate_runs.py",
        "--cases", str(cases_dir),
        "--runs", str(runs_dir),
        "--json",
    ]
    buf = io.StringIO()
    rc = 1
    try:
        with contextlib.redirect_stdout(buf):
            rc = evaluate_runs.main()
    except SystemExit as e:
        rc = int(e.code or 0)
    finally:
        sys.argv = saved
    return {"rc": rc, "report": json.loads(buf.getvalue())}


def test_claude_pass():
    print("evaluate_runs: claude pass")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = root / "cases"; cases.mkdir()
        runs = root / "runs"; runs.mkdir()
        work = root / "work"; work.mkdir()
        (work / "result.txt").write_text("done", encoding="utf-8")

        write_case(
            cases / "c1.yaml",
            "summarize",
            {
                "tools_used": ["Read"],
                "files_exist": ["result.txt"],
                "contains": ["hello"],
                "max_cost_usd": 0.1,
                "max_duration_seconds": 60,
            },
        )

        claude_payload = json.dumps({
            "type": "result",
            "subtype": "success",
            "session_id": "s1",
            "duration_ms": 1000,
            "total_cost_usd": 0.0123,
            "result": "hello world",
            "messages": [
                {"role": "assistant", "content": [
                    {"type": "text", "text": "reading"},
                    {"type": "tool_use", "name": "Read", "input": {"path": "x"}},
                ]},
                {"role": "assistant", "content": [
                    {"type": "text", "text": "hello world"},
                ]},
            ],
        })
        (runs / "c1.json").write_text(
            envelope("claude", str(work), 5, claude_payload), encoding="utf-8"
        )

        res = run_evaluator(cases, runs)
        rep = res["report"]
        check("rc==0", res["rc"] == 0, str(rep))
        check("one case passed", rep["passed"] == 1 and rep["failed"] == 0)
        check("agent=claude recorded", rep["cases"][0].get("agent") == "claude")


def test_codex_pass():
    print("evaluate_runs: codex pass")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = root / "cases"; cases.mkdir()
        runs = root / "runs"; runs.mkdir()
        work = root / "work"; work.mkdir()

        write_case(
            cases / "c1.yaml",
            "run ls",
            {
                "tools_used": ["command_execution"],
                "contains": ["listed"],
                "max_cost_usd": 0.1,
            },
        )

        codex_payload = "\n".join([
            json.dumps({"type": "thread.started", "thread_id": "th1"}),
            json.dumps({"type": "turn.started"}),
            json.dumps({"type": "item.completed",
                        "item": {"id": "a", "type": "command_execution",
                                 "command": "ls", "exit_code": 0}}),
            json.dumps({"type": "item.completed",
                        "item": {"id": "b", "type": "agent_message",
                                 "text": "repo listed"}}),
            json.dumps({"type": "turn.completed",
                        "total_cost_usd": 0.0007,
                        "usage": {"input_tokens": 10, "output_tokens": 5}}),
        ])
        (runs / "c1.json").write_text(
            envelope("codex", str(work), 3, codex_payload), encoding="utf-8"
        )

        res = run_evaluator(cases, runs)
        rep = res["report"]
        check("rc==0", res["rc"] == 0, str(rep))
        check("one case passed", rep["passed"] == 1 and rep["failed"] == 0, str(rep))
        check("agent=codex recorded", rep["cases"][0].get("agent") == "codex")


def test_cursor_pass():
    print("evaluate_runs: cursor pass")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = root / "cases"; cases.mkdir()
        runs = root / "runs"; runs.mkdir()
        work = root / "work"; work.mkdir()

        write_case(
            cases / "c1.yaml",
            "read readme",
            {
                "tools_used": ["read"],
                "contains": ["OK"],
                "max_duration_seconds": 30,
            },
        )

        cursor_payload = "\n".join([
            json.dumps({"type": "system", "subtype": "init",
                        "cwd": str(work), "session_id": "s1",
                        "model": "Claude 4 Sonnet", "permissionMode": "default",
                        "apiKeySource": "login"}),
            json.dumps({"type": "tool_call", "subtype": "started",
                        "call_id": "t1",
                        "tool_call": {"readToolCall": {"args": {"path": "README.md"}}},
                        "session_id": "s1"}),
            json.dumps({"type": "tool_call", "subtype": "completed",
                        "call_id": "t1",
                        "tool_call": {"readToolCall": {
                            "args": {"path": "README.md"},
                            "result": {"success": {"totalLines": 5}},
                        }},
                        "session_id": "s1"}),
            json.dumps({"type": "result", "subtype": "success",
                        "duration_ms": 1000, "is_error": False,
                        "result": "README read OK", "session_id": "s1"}),
        ])
        (runs / "c1.json").write_text(
            envelope("cursor", str(work), 3, cursor_payload), encoding="utf-8"
        )

        res = run_evaluator(cases, runs)
        rep = res["report"]
        check("rc==0", res["rc"] == 0, str(rep))
        check("one case passed", rep["passed"] == 1 and rep["failed"] == 0, str(rep))
        check("agent=cursor recorded", rep["cases"][0].get("agent") == "cursor")


def test_fail_path_missing_file():
    print("evaluate_runs: claude fail on missing file")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cases = root / "cases"; cases.mkdir()
        runs = root / "runs"; runs.mkdir()
        work = root / "work"; work.mkdir()

        write_case(
            cases / "c1.yaml",
            "produce artifact",
            {"files_exist": ["artifact.txt"], "contains": ["ok"]},
        )
        claude_payload = json.dumps({
            "type": "result", "subtype": "success",
            "result": "ok", "session_id": "s1", "total_cost_usd": 0.0,
            "messages": [{"role": "assistant", "content": [
                {"type": "text", "text": "ok"}
            ]}],
        })
        (runs / "c1.json").write_text(
            envelope("claude", str(work), 1, claude_payload), encoding="utf-8"
        )

        res = run_evaluator(cases, runs)
        rep = res["report"]
        check("rc!=0", res["rc"] != 0)
        check("failure recorded", rep["failed"] == 1 and rep["passed"] == 0)
        failures = rep["cases"][0]["failures"]
        check("file_exist failure flagged", any("file_exist" in f for f in failures),
              str(failures))


def main() -> int:
    test_claude_pass()
    test_codex_pass()
    test_cursor_pass()
    test_fail_path_missing_file()
    print()
    if FAILS:
        print(f"FAIL: {len(FAILS)} assertion(s)")
        for f in FAILS:
            print(f"   - {f}")
        return 1
    print("evaluate_runs: all e2e tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
