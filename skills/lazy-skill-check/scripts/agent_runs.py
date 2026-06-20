#!/usr/bin/env python3
"""
Cross-agent parser for headless run outputs.

Supported formats:
  - claude   : single JSON object from `claude -p --output-format json`
               or streaming JSONL that we collapse.
  - codex    : JSONL stream from `codex exec --json`.
  - cursor   : single JSON object from `cursor-agent --output-format json`
               or JSONL stream from `--output-format stream-json`.

Public surface:
  parse_run(raw_text: str, *, agent_hint: str | None = None) -> ParsedRun
  detect_agent(raw_text: str) -> str           # "claude" | "codex" | "cursor" | "unknown"

ParsedRun fields are agent-agnostic:
  agent              : which parser was used
  final_text         : the assistant's final answer as plain text
  tool_calls         : list of {name, args, result, ok}
  tool_names         : flat list of tool names in order observed
  cost_usd           : total cost (best-effort)
  duration_ms        : wall-clock reported by the agent, if any
  raw_events         : preserved for debugging
  model              : best-effort model identifier
  session_id         : best-effort session id
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ToolCall:
    name: str
    args: Any = None
    result: Any = None
    ok: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ParsedRun:
    agent: str
    final_text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    cost_usd: float | None = None
    duration_ms: int | None = None
    model: str | None = None
    session_id: str | None = None
    raw_events: list[Any] = field(default_factory=list)

    @property
    def tool_names(self) -> list[str]:
        return [tc.name for tc in self.tool_calls]

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "final_text": self.final_text,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "tool_names": self.tool_names,
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "session_id": self.session_id,
        }


def _try_jsonl(raw: str) -> list[Any] | None:
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return None
    events: list[Any] = []
    for ln in lines:
        try:
            events.append(json.loads(ln))
        except json.JSONDecodeError:
            return None
    return events if len(events) >= 2 else None


def _try_single_json(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def detect_agent(raw: str) -> str:
    """Cheap heuristic sniffing — looks at the first non-empty JSON chunk."""
    events = _try_jsonl(raw)
    if events:
        head = events[0] if isinstance(events[0], dict) else {}
        t = head.get("type")
        if t in {"thread.started", "turn.started", "item.started", "item.completed"}:
            return "codex"
        if t == "system" and head.get("subtype") == "init" and head.get("cwd"):
            return "cursor"
        for ev in events:
            if not isinstance(ev, dict):
                continue
            t2 = ev.get("type")
            if t2 == "tool_call" or t2 == "assistant":
                return "cursor"
            if t2 and t2.startswith("item."):
                return "codex"
        return "unknown"

    obj = _try_single_json(raw)
    if isinstance(obj, dict):
        if "messages" in obj or "total_cost_usd" in obj or "cost_usd" in obj:
            return "claude"
        if obj.get("type") == "result" and "result" in obj and "session_id" in obj:
            return "cursor"
        if obj.get("type") in {"message", "assistant"} or "content" in obj:
            return "claude"
    return "unknown"


# ---------- Claude Code ----------

def parse_claude(raw: str) -> ParsedRun:
    out = ParsedRun(agent="claude")

    events = _try_jsonl(raw)
    obj = None if events else _try_single_json(raw)

    if events:
        out.raw_events = events
        for ev in events:
            if not isinstance(ev, dict):
                continue
            t = ev.get("type")
            if t == "message" and ev.get("role") == "assistant":
                for part in ev.get("content", []) or []:
                    if isinstance(part, dict) and part.get("type") == "text":
                        out.final_text += part.get("text", "")
                    if isinstance(part, dict) and part.get("type") == "tool_use":
                        out.tool_calls.append(
                            ToolCall(name=str(part.get("name", "")), args=part.get("input"))
                        )
            elif t == "result":
                out.cost_usd = ev.get("total_cost_usd") or ev.get("cost_usd")
                out.duration_ms = ev.get("duration_ms")
                out.session_id = ev.get("session_id") or out.session_id
        return out

    if isinstance(obj, dict):
        out.raw_events = [obj]
        out.cost_usd = obj.get("total_cost_usd") or obj.get("cost_usd")
        out.duration_ms = obj.get("duration_ms")
        out.session_id = obj.get("session_id")
        out.model = obj.get("model")

        msgs = obj.get("messages")
        last_assistant_text = ""
        if isinstance(msgs, list):
            for m in msgs:
                if not isinstance(m, dict) or m.get("role") != "assistant":
                    continue
                texts: list[str] = []
                for part in m.get("content", []) or []:
                    if not isinstance(part, dict):
                        continue
                    if part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif part.get("type") == "tool_use":
                        out.tool_calls.append(
                            ToolCall(
                                name=str(part.get("name", "")),
                                args=part.get("input"),
                            )
                        )
                if texts:
                    last_assistant_text = "".join(texts)

        if isinstance(obj.get("result"), str) and obj["result"]:
            out.final_text = obj["result"]
        else:
            out.final_text = last_assistant_text
        return out

    out.final_text = raw
    return out


# ---------- OpenAI Codex ----------

def parse_codex(raw: str) -> ParsedRun:
    """Parse `codex exec --json` JSONL stream.

    Event shapes of interest:
      {"type":"thread.started","thread_id":"..."}
      {"type":"item.started","item":{"id":"...","type":"command_execution","command":"..."}}
      {"type":"item.completed","item":{"id":"...","type":"agent_message","text":"..."}}
      {"type":"item.completed","item":{"id":"...","type":"command_execution","command":"...","exit_code":0}}
      {"type":"item.completed","item":{"id":"...","type":"mcp_tool_call","server":"...","tool":"..."}}
      {"type":"turn.completed","usage":{...}}
    """
    out = ParsedRun(agent="codex")
    events = _try_jsonl(raw) or []
    out.raw_events = events

    agent_texts: list[str] = []

    for ev in events:
        if not isinstance(ev, dict):
            continue
        t = ev.get("type")
        if t == "thread.started":
            out.session_id = ev.get("thread_id") or out.session_id
        elif t == "item.completed":
            item = ev.get("item") or {}
            it = item.get("type")
            if it == "agent_message":
                txt = item.get("text") or ""
                if isinstance(txt, str) and txt:
                    agent_texts.append(txt)
            elif it == "command_execution":
                out.tool_calls.append(
                    ToolCall(
                        name="command_execution",
                        args={"command": item.get("command")},
                        result={"exit_code": item.get("exit_code")},
                        ok=(item.get("exit_code") in (0, None)),
                    )
                )
            elif it == "mcp_tool_call":
                name = item.get("tool") or item.get("name") or "mcp_tool_call"
                server = item.get("server")
                out.tool_calls.append(
                    ToolCall(
                        name=str(name),
                        args={"server": server, "arguments": item.get("arguments")},
                        result=item.get("result"),
                        ok=bool(item.get("success", True)),
                    )
                )
            elif it == "file_change":
                out.tool_calls.append(
                    ToolCall(
                        name="file_change",
                        args={"path": item.get("path"), "kind": item.get("change")},
                    )
                )
            elif it == "web_search":
                out.tool_calls.append(
                    ToolCall(name="web_search", args={"query": item.get("query")})
                )
        elif t == "turn.completed":
            usage = ev.get("usage") or {}
            cost = ev.get("total_cost_usd") or usage.get("total_cost_usd")
            if isinstance(cost, (int, float)):
                out.cost_usd = float(cost)

    out.final_text = "\n".join(agent_texts)
    return out


# ---------- Cursor Agent ----------

def parse_cursor(raw: str) -> ParsedRun:
    """Parse Cursor Agent CLI output.

    Supports both:
      --output-format json          (single result object)
      --output-format stream-json   (NDJSON with system/user/assistant/tool_call/result)
    """
    out = ParsedRun(agent="cursor")
    events = _try_jsonl(raw)

    if not events:
        obj = _try_single_json(raw)
        if isinstance(obj, dict) and obj.get("type") == "result":
            out.raw_events = [obj]
            out.final_text = obj.get("result") or ""
            out.duration_ms = obj.get("duration_ms")
            out.session_id = obj.get("session_id")
        else:
            out.final_text = raw
        return out

    out.raw_events = events
    assistant_texts: list[str] = []
    pending: dict[str, ToolCall] = {}

    for ev in events:
        if not isinstance(ev, dict):
            continue
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            out.model = ev.get("model") or out.model
            out.session_id = ev.get("session_id") or out.session_id
        elif t == "assistant":
            msg = ev.get("message") or {}
            for part in msg.get("content", []) or []:
                if isinstance(part, dict) and part.get("type") == "text":
                    assistant_texts.append(part.get("text", ""))
        elif t == "tool_call":
            call_id = ev.get("call_id") or f"anon_{len(pending)}"
            tc = ev.get("tool_call") or {}
            name: str
            args: Any
            if "readToolCall" in tc:
                name = "read"
                args = (tc["readToolCall"] or {}).get("args")
            elif "writeToolCall" in tc:
                name = "write"
                args = (tc["writeToolCall"] or {}).get("args")
            elif "function" in tc:
                fn = tc["function"] or {}
                name = str(fn.get("name") or "function")
                args = fn.get("arguments")
            else:
                remaining = [k for k in tc.keys() if k not in {"subtype"}]
                name = remaining[0].replace("ToolCall", "") if remaining else "unknown"
                args = tc.get(remaining[0]) if remaining else None

            subtype = ev.get("subtype")
            if subtype == "started":
                pending[call_id] = ToolCall(name=name, args=args)
                out.tool_calls.append(pending[call_id])
            elif subtype == "completed":
                result_block = None
                for k in ("readToolCall", "writeToolCall", "function"):
                    if k in tc:
                        result_block = (tc[k] or {}).get("result")
                        break
                tc_obj = pending.get(call_id)
                if tc_obj is None:
                    tc_obj = ToolCall(name=name, args=args)
                    out.tool_calls.append(tc_obj)
                tc_obj.result = result_block
                tc_obj.ok = bool(
                    isinstance(result_block, dict) and result_block.get("success")
                ) if isinstance(result_block, dict) else True
        elif t == "result":
            out.final_text = ev.get("result") or out.final_text
            out.duration_ms = ev.get("duration_ms")
            out.session_id = ev.get("session_id") or out.session_id

    if not out.final_text:
        out.final_text = "\n".join(assistant_texts)
    return out


# ---------- dispatcher ----------

PARSERS = {
    "claude": parse_claude,
    "codex": parse_codex,
    "cursor": parse_cursor,
}


def parse_run(raw: str, *, agent_hint: str | None = None) -> ParsedRun:
    if agent_hint and agent_hint in PARSERS:
        return PARSERS[agent_hint](raw)
    detected = detect_agent(raw)
    if detected in PARSERS:
        return PARSERS[detected](raw)
    fallback = parse_claude(raw)
    fallback.agent = "unknown"
    return fallback


def main() -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(description="Cross-agent run parser")
    p.add_argument("path", nargs="?", help="path to run output; - for stdin")
    p.add_argument("--agent", choices=sorted(PARSERS.keys()), default=None)
    args = p.parse_args()

    if not args.path or args.path == "-":
        raw = sys.stdin.read()
    else:
        raw = open(args.path, encoding="utf-8").read()
    parsed = parse_run(raw, agent_hint=args.agent)
    print(json.dumps(parsed.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
