#!/usr/bin/env python3
"""
Generate a PlantUML mindmap from Markdown.

This script serves two roles:
1. CLI utility for manual use.
2. Promptfoo Python provider via `call_api()`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BULLET_RE = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)|\[([^\]]+)\]\([^)]+\)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)(.*?)\1")


def _clean_inline_markup(text: str) -> str:
    text = LINK_RE.sub(lambda m: m.group(1) or m.group(2) or "", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = EMPHASIS_RE.sub(r"\2", text)
    return " ".join(text.split()).strip()


def _sanitize_plantuml_text(text: str) -> str:
    text = text.replace("{", "(").replace("}", ")")
    text = text.replace("[", "(").replace("]", ")")
    text = text.replace("<", "").replace(">", "")
    text = text.replace("|", "/")
    text = text.replace("\t", " ")
    text = " ".join(text.split())
    return text.strip() or "Untitled"


def _dedupe_sequential(items: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
    deduped: list[tuple[int, str]] = []
    for item in items:
        if deduped and deduped[-1] == item:
            continue
        deduped.append(item)
    return deduped


def parse_markdown(markdown: str, default_title: str = "Markdown Mindmap") -> tuple[str, list[tuple[int, str]]]:
    title = default_title
    nodes: list[tuple[int, str]] = []
    in_fence = False
    first_h1_consumed = False
    current_heading_depth = 1

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        stripped = line.strip()
        if not stripped:
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            text = _sanitize_plantuml_text(_clean_inline_markup(heading_match.group(2)))
            if level == 1 and not first_h1_consumed:
                title = text
                first_h1_consumed = True
                current_heading_depth = 1
                continue

            depth = max(2, level)
            nodes.append((depth, text))
            current_heading_depth = depth
            continue

        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            indent = len(bullet_match.group(1).expandtabs(2))
            nesting = indent // 2
            depth = max(2, current_heading_depth + 1 + nesting)
            text = _sanitize_plantuml_text(_clean_inline_markup(bullet_match.group(2)))
            nodes.append((depth, text))
            continue

    return title, _dedupe_sequential(nodes)


def build_mindmap(title: str, nodes: list[tuple[int, str]]) -> str:
    lines = ["@startmindmap", f"* {_sanitize_plantuml_text(title)}"]
    for depth, text in nodes:
        safe_depth = max(2, depth)
        lines.append(f"{'*' * safe_depth} {_sanitize_plantuml_text(text)}")
    lines.append("@endmindmap")
    return "\n".join(lines) + "\n"


def markdown_to_mindmap(markdown: str, default_title: str = "Markdown Mindmap") -> str:
    title, nodes = parse_markdown(markdown, default_title=default_title)
    return build_mindmap(title, nodes)


def _read_markdown_from_path(path_str: str, base_dir: Path | None = None) -> tuple[str, Path]:
    path = Path(path_str)
    if not path.is_absolute() and base_dir is not None:
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")
    if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
        raise ValueError(f"Unsupported input extension: {path.suffix}")

    return path.read_text(encoding="utf-8"), path


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    base_dir = Path(config.get("basePath", ".")).resolve()
    vars_map = (context or {}).get("vars", {}) or {}

    markdown_path = vars_map.get("markdown_path")
    default_title = vars_map.get("title") or config.get("defaultTitle") or "Markdown Mindmap"

    try:
        if markdown_path:
            markdown, source_path = _read_markdown_from_path(str(markdown_path), base_dir=base_dir)
            if "title" not in vars_map:
                default_title = source_path.stem.replace("_", " ").replace("-", " ").title()
        else:
            markdown = prompt

        output = markdown_to_mindmap(markdown, default_title=default_title)
        node_count = sum(1 for line in output.splitlines() if line.startswith("*"))
        return {
            "output": output,
            "metadata": {
                "nodeCount": node_count,
                "defaultTitle": default_title,
            },
        }
    except Exception as exc:
        return {
            "output": "",
            "error": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PlantUML mindmap source from Markdown.")
    parser.add_argument("-i", "--input", help="Input Markdown file. Reads from stdin if omitted.")
    parser.add_argument("-o", "--output", help="Output .puml file. Prints to stdout if omitted.")
    parser.add_argument("--title", help="Fallback title when the Markdown has no H1 heading.")
    parser.add_argument("--json", action="store_true", help="Print JSON with title and output.")
    args = parser.parse_args()

    if args.input:
        markdown, source_path = _read_markdown_from_path(args.input)
        default_title = args.title or source_path.stem.replace("_", " ").replace("-", " ").title()
    else:
        markdown = sys.stdin.read()
        if not markdown.strip():
            raise SystemExit("Error: empty Markdown input")
        default_title = args.title or "Markdown Mindmap"

    output = markdown_to_mindmap(markdown, default_title=default_title)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")

    if args.json:
        payload = {
            "title": default_title,
            "output": output,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif not args.output:
        print(output, end="")


if __name__ == "__main__":
    main()
