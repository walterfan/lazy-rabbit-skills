#!/usr/bin/env python3
"""
Cross-vendor judge LLM helper.

Centralizes a thin "ask model a short question, get a short answer" call used
by L2 trigger eval and L4 pairwise benchmark. Supports:

  - Anthropic API        (ANTHROPIC_API_KEY)        model id starting with "claude-"
  - OpenAI API           (OPENAI_API_KEY)           model id starting with "gpt-" or "o"
  - Claude Code CLI      (`claude --bare -p`)       any claude-* model
  - Codex CLI            (`codex exec`)             any openai-* or gpt-* model

Vendor is inferred from the model id, then overridden by LAZY_SKILL_CHECK_JUDGE_VENDOR
if set. Fallbacks cascade (API failure -> CLI if available).

Also provides pick_letter() for "A / B / TIE" style outputs with position-swap
protection so the caller only has to track which side is which.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


VENDOR_ANTHROPIC = "anthropic"
VENDOR_OPENAI = "openai"


@dataclass
class JudgeResult:
    text: str
    vendor: str
    backend: str  # "api" or "cli"


def infer_vendor(model: str) -> str:
    override = os.environ.get("LAZY_SKILL_CHECK_JUDGE_VENDOR", "").strip().lower()
    if override in (VENDOR_ANTHROPIC, VENDOR_OPENAI):
        return override
    m = (model or "").lower()
    if m.startswith("claude") or "sonnet" in m or "haiku" in m or "opus" in m:
        return VENDOR_ANTHROPIC
    if m.startswith(("gpt", "o1", "o3", "o4")) or "codex" in m:
        return VENDOR_OPENAI
    return VENDOR_ANTHROPIC


def _call_anthropic_api(model: str, prompt: str, *, max_tokens: int, timeout: float) -> str:
    import urllib.request

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    payload = json.dumps(
        {"model": model, "max_tokens": max_tokens,
         "messages": [{"role": "user", "content": prompt}]}
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    for part in body.get("content", []) or []:
        if part.get("type") == "text":
            return part.get("text", "").strip()
    return ""


def _call_openai_api(model: str, prompt: str, *, max_tokens: int, timeout: float) -> str:
    import urllib.request

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")

    # Use the lowest-common-denominator chat completions endpoint. Judge prompts
    # are single-turn plain text, so this works for gpt-4o, gpt-4.1, o-series, etc.
    payload = json.dumps(
        {
            "model": model,
            "max_completion_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    choices = body.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for p in content:
            if isinstance(p, dict) and isinstance(p.get("text"), str):
                parts.append(p["text"])
        return "".join(parts).strip()
    return ""


def _call_claude_cli(model: str, prompt: str, *, timeout: float) -> str:
    if not shutil.which("claude"):
        raise RuntimeError("claude CLI not found in PATH")
    r = subprocess.run(
        [
            "claude", "-p", prompt,
            "--model", model,
            "--max-turns", "1",
            "--output-format", "text",
        ],
        capture_output=True, text=True, timeout=timeout,
        stdin=subprocess.DEVNULL,
    )
    if r.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _call_codex_cli(model: str, prompt: str, *, timeout: float) -> str:
    if not shutil.which("codex"):
        raise RuntimeError("codex CLI not found in PATH")
    # codex exec prints progress on stderr and only the final agent message
    # on stdout — exactly what we want as a plain text answer.
    r = subprocess.run(
        ["codex", "exec", "--skip-git-repo-check", "--model", model, prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(f"codex CLI failed: {r.stderr.strip()}")
    return r.stdout.strip()


def ask(
    model: str,
    prompt: str,
    *,
    vendor: Optional[str] = None,
    max_tokens: int = 16,
    timeout: float = 30.0,
) -> JudgeResult:
    """Ask the judge model a question; prefer API then fall back to CLI.

    Raises RuntimeError if every backend for the chosen vendor fails.
    """
    v = vendor or infer_vendor(model)

    errors: list[str] = []
    if v == VENDOR_ANTHROPIC:
        try:
            text = _call_anthropic_api(model, prompt, max_tokens=max_tokens, timeout=timeout)
            return JudgeResult(text=text, vendor=v, backend="api")
        except Exception as exc:
            errors.append(f"anthropic api: {exc}")
        try:
            text = _call_claude_cli(model, prompt, timeout=timeout)
            return JudgeResult(text=text, vendor=v, backend="cli")
        except Exception as exc:
            errors.append(f"claude cli: {exc}")
    elif v == VENDOR_OPENAI:
        try:
            text = _call_openai_api(model, prompt, max_tokens=max_tokens, timeout=timeout)
            return JudgeResult(text=text, vendor=v, backend="api")
        except Exception as exc:
            errors.append(f"openai api: {exc}")
        try:
            text = _call_codex_cli(model, prompt, timeout=timeout)
            return JudgeResult(text=text, vendor=v, backend="cli")
        except Exception as exc:
            errors.append(f"codex cli: {exc}")
    else:
        raise RuntimeError(f"unknown vendor: {v}")

    raise RuntimeError("judge failed: " + " | ".join(errors))


def pick_letter(text: str) -> str:
    """Normalize a judge's answer to 'A' / 'B' / 'TIE'.

    Rules, in order:
      1. 'both A and B', 'tie' -> TIE
      2. first standalone A / B / TIE token on the first line wins
      3. otherwise: single presence of A or B on the first line
    """
    if not text:
        return "TIE"
    first = text.strip().splitlines()[0].upper()
    low_first = first.lower()
    if "tie" in low_first or ("both" in low_first and " a " in f" {low_first} " and " b " in f" {low_first} "):
        return "TIE"

    import re
    tokens = re.findall(r"\b(A|B|TIE)\b", first)
    if tokens:
        return tokens[0]

    has_a = "A" in first
    has_b = "B" in first
    if has_a and not has_b:
        return "A"
    if has_b and not has_a:
        return "B"
    return "TIE"


def pick_yes_no(text: str) -> str:
    """Normalize a judge's answer to 'YES' / 'NO'. Empty / ambiguous -> 'NO'."""
    if not text:
        return "NO"
    first = text.strip().splitlines()[0].upper()
    token = first.split()[0] if first.split() else first
    token = token.strip("*`\"'.,;:!?()[]{}")
    if token.startswith("YES"):
        return "YES"
    if token.startswith("NO"):
        return "NO"
    if "YES" in first and "NO" not in first:
        return "YES"
    if "NO" in first and "YES" not in first:
        return "NO"
    return "NO"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-haiku-4-5")
    ap.add_argument("--vendor", choices=[VENDOR_ANTHROPIC, VENDOR_OPENAI], default=None)
    ap.add_argument("prompt", nargs="?", default="Say YES")
    args = ap.parse_args()
    res = ask(args.model, args.prompt, vendor=args.vendor)
    print(f"vendor={res.vendor} backend={res.backend}")
    print(res.text)
