#!/usr/bin/env python3
"""
Smoke tests for agent_runs parser.

Run:
    python3 test_agent_runs.py

Prints PASS/FAIL per case and exits 0 on full success, 1 otherwise.
Keep it dependency-free so it works in any venv.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from agent_runs import detect_agent, parse_run  # noqa: E402


# ---------- fixtures ----------

CLAUDE_SINGLE = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "session_id": "abc-123",
        "duration_ms": 4321,
        "total_cost_usd": 0.0123,
        "result": "hello from claude",
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "I'll look at the file."},
                    {"type": "tool_use", "name": "Read", "input": {"path": "a.md"}},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "hello from claude"},
                ],
            },
        ],
    }
)

CODEX_JSONL = "\n".join(
    [
        json.dumps({"type": "thread.started", "thread_id": "thread-xyz"}),
        json.dumps({"type": "turn.started"}),
        json.dumps(
            {
                "type": "item.started",
                "item": {"id": "i1", "type": "command_execution", "command": "ls"},
            }
        ),
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "id": "i1",
                    "type": "command_execution",
                    "command": "ls",
                    "exit_code": 0,
                },
            }
        ),
        json.dumps(
            {
                "type": "item.completed",
                "item": {"id": "i2", "type": "agent_message", "text": "repo listed"},
            }
        ),
        json.dumps(
            {
                "type": "turn.completed",
                "usage": {"input_tokens": 100, "output_tokens": 20},
                "total_cost_usd": 0.0007,
            }
        ),
    ]
)

CURSOR_SINGLE = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "duration_ms": 1234,
        "duration_api_ms": 1234,
        "result": "cursor says hi",
        "session_id": "cur-1",
    }
)

CURSOR_STREAM = "\n".join(
    [
        json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "cwd": "/tmp/x",
                "session_id": "s1",
                "model": "Claude 4 Sonnet",
                "permissionMode": "default",
                "apiKeySource": "login",
            }
        ),
        json.dumps(
            {
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": "read README"}]},
                "session_id": "s1",
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]},
                "session_id": "s1",
            }
        ),
        json.dumps(
            {
                "type": "tool_call",
                "subtype": "started",
                "call_id": "t1",
                "tool_call": {"readToolCall": {"args": {"path": "README.md"}}},
                "session_id": "s1",
            }
        ),
        json.dumps(
            {
                "type": "tool_call",
                "subtype": "completed",
                "call_id": "t1",
                "tool_call": {
                    "readToolCall": {
                        "args": {"path": "README.md"},
                        "result": {"success": {"totalLines": 5}},
                    }
                },
                "session_id": "s1",
            }
        ),
        json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "duration_ms": 9876,
                "is_error": False,
                "result": "README read OK",
                "session_id": "s1",
            }
        ),
    ]
)


# ---------- tiny assert helper ----------

FAILS: list[str] = []


def check(label: str, cond: bool, hint: str = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}" + (f"   [{hint}]" if hint else ""))
        FAILS.append(label)


# ---------- tests ----------

def test_detect():
    print("detect_agent")
    check("claude single", detect_agent(CLAUDE_SINGLE) == "claude")
    check("codex jsonl", detect_agent(CODEX_JSONL) == "codex")
    check("cursor single", detect_agent(CURSOR_SINGLE) == "cursor")
    check("cursor stream", detect_agent(CURSOR_STREAM) == "cursor")


def test_parse_claude():
    print("parse_claude")
    r = parse_run(CLAUDE_SINGLE)
    check("agent=claude", r.agent == "claude")
    check("final_text has hello", "hello from claude" in r.final_text, r.final_text)
    check("tool Read captured", "Read" in r.tool_names, str(r.tool_names))
    check("cost captured", r.cost_usd == 0.0123, str(r.cost_usd))
    check("session id", r.session_id == "abc-123")


def test_parse_codex():
    print("parse_codex")
    r = parse_run(CODEX_JSONL)
    check("agent=codex", r.agent == "codex")
    check("final_text has repo listed", "repo listed" in r.final_text, r.final_text)
    check(
        "command_execution captured",
        "command_execution" in r.tool_names,
        str(r.tool_names),
    )
    check("session_id=thread-xyz", r.session_id == "thread-xyz")
    check("cost captured", r.cost_usd == 0.0007, str(r.cost_usd))


def test_parse_cursor_single():
    print("parse_cursor (single json)")
    r = parse_run(CURSOR_SINGLE)
    check("agent=cursor", r.agent == "cursor")
    check("final_text", r.final_text == "cursor says hi")
    check("duration captured", r.duration_ms == 1234)
    check("no tool calls", r.tool_names == [])


def test_parse_cursor_stream():
    print("parse_cursor (stream-json)")
    r = parse_run(CURSOR_STREAM)
    check("agent=cursor", r.agent == "cursor")
    check(
        "final_text preferred from result event",
        r.final_text == "README read OK",
        r.final_text,
    )
    check("read tool captured", "read" in r.tool_names, str(r.tool_names))
    check("duration captured", r.duration_ms == 9876)
    check("model captured", r.model == "Claude 4 Sonnet")


def main() -> int:
    test_detect()
    test_parse_claude()
    test_parse_codex()
    test_parse_cursor_single()
    test_parse_cursor_stream()
    print()
    if FAILS:
        print(f"FAIL: {len(FAILS)} assertion(s) failed")
        for f in FAILS:
            print(f"   - {f}")
        return 1
    print("All smoke tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
