#!/usr/bin/env python3
"""Convert a Markdown tutorial into an executable Jupyter notebook (.ipynb).

This is the deterministic backbone of the tutorial-to-notebook skill. It does the
mechanical, boring part reliably:

  * prose (headings, paragraphs, lists) -> Markdown cells
  * fenced code blocks in an *executable* language -> code cells
  * fenced blocks in an *illustrative* language (console, output, json, yaml,
    text, ...) -> left inside Markdown cells, because they are results/snippets
    to read, not code to run.

The agent then ENRICHES the result (setup cell, expected outputs, editable-param
markers, gotcha markers, verification cells) per references/notebook-authoring-guide.md.

Stdlib only -- no nbformat, no pip install. Output is a valid nbformat v4 notebook
that opens in Jupyter, JupyterLab, JupyterLite and Google Colab.

Usage:
    python md_to_notebook.py TUTORIAL.md -o TUTORIAL.ipynb
    python md_to_notebook.py TUTORIAL.md --lang python,bash
    cat TUTORIAL.md | python md_to_notebook.py - -o out.ipynb

Security note: this script never fetches anything and never executes any of the
code it reads. It is a pure text transform.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Languages we treat as runnable code cells. Everything else in a fenced block
# (console, text, output, json, yaml, http, mermaid, ...) stays in Markdown so
# the reader sees it as an illustration, not something to execute.
DEFAULT_EXECUTABLE = {"python", "py", "ipython"}
# Common aliases mapped to the notebook language name.
LANG_ALIASES = {"py": "python", "ipython": "python"}

FENCE_RE = re.compile(r"^(`{3,}|~{3,})\s*([^\s`~]*)\s*$")
# Pelican / Jekyll style front matter delimiters we optionally strip.
FRONTMATTER_KEYS = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:\s")


def strip_frontmatter(lines: list[str]) -> list[str]:
    """Drop a leading `---` YAML block or a leading Pelican key:value header.

    Pelican headers are a run of `Key: value` lines at the very top with no blank
    line before the first one; we stop at the first blank line.
    """
    if not lines:
        return lines
    # YAML front matter: --- ... ---
    if lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1:]
        return lines  # unterminated; leave as-is
    # Pelican header block: consecutive Key: value lines up to a blank line.
    if FRONTMATTER_KEYS.match(lines[0]):
        i = 0
        while i < len(lines) and lines[i].strip() != "":
            if not FRONTMATTER_KEYS.match(lines[i]):
                # A non key:value line inside the block -> not a header, bail out.
                return lines
            i += 1
        # skip the block and one trailing blank line
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        return lines[i:]
    return lines


def md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": _as_source_list(source),
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _as_source_list(source),
    }


def _as_source_list(text: str) -> list[str]:
    """nbformat stores source as a list of lines each ending in \n (except last)."""
    text = text.rstrip("\n")
    if text == "":
        return []
    lines = text.split("\n")
    return [ln + "\n" for ln in lines[:-1]] + [lines[-1]]


def parse(markdown: str, executable: set[str], strip_fm: bool) -> list[dict]:
    lines = markdown.split("\n")
    if strip_fm:
        lines = strip_frontmatter(lines)

    cells: list[dict] = []
    md_buf: list[str] = []
    i = 0
    n = len(lines)

    def flush_md():
        if md_buf:
            text = "\n".join(md_buf).strip("\n")
            if text.strip():
                cells.append(md_cell(text))
        md_buf.clear()

    while i < n:
        line = lines[i]
        m = FENCE_RE.match(line)
        if m:
            fence, lang = m.group(1), m.group(2).lower()
            # collect until matching closing fence of same char & >= length
            body: list[str] = []
            j = i + 1
            closed = False
            while j < n:
                mc = FENCE_RE.match(lines[j])
                if mc and mc.group(1)[0] == fence[0] and len(mc.group(1)) >= len(fence) and mc.group(2) == "":
                    closed = True
                    break
                body.append(lines[j])
                j += 1
            code = "\n".join(body)
            is_exec = lang in executable
            if is_exec:
                flush_md()
                cells.append(code_cell(code))
            else:
                # keep the fenced block verbatim inside the markdown stream
                md_buf.append(line)
                md_buf.extend(body)
                if closed:
                    md_buf.append(lines[j])
            i = j + 1 if closed else j
        else:
            md_buf.append(line)
            i += 1
    flush_md()
    return cells


def build_notebook(cells: list[dict]) -> dict:
    # nbformat 4.5 requires a stable `id` on every cell. Use a deterministic,
    # index-based id so regenerating the same tutorial yields the same notebook.
    for idx, cell in enumerate(cells):
        cell["id"] = f"cell-{idx}"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
            "tutorial_to_notebook": {
                "generated_by": "tutorial-to-notebook skill",
                "note": "Mechanical conversion; enrich per notebook-authoring-guide.md",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Markdown file, or - for stdin")
    ap.add_argument("-o", "--output", help="Output .ipynb path (default: alongside input)")
    ap.add_argument(
        "--lang",
        default="python",
        help="Comma-separated languages to treat as runnable code cells (default: python)",
    )
    ap.add_argument(
        "--keep-frontmatter",
        action="store_true",
        help="Do not strip a leading YAML/Pelican metadata block",
    )
    args = ap.parse_args(argv)

    if args.input == "-":
        markdown = sys.stdin.read()
        default_out = "notebook.ipynb"
    else:
        src = Path(args.input)
        if not src.is_file():
            print(f"error: input file not found: {src}", file=sys.stderr)
            return 2
        markdown = src.read_text(encoding="utf-8")
        default_out = str(src.with_suffix(".ipynb"))

    executable = set()
    for raw in args.lang.split(","):
        lang = raw.strip().lower()
        if not lang:
            continue
        executable.add(LANG_ALIASES.get(lang, lang))
        executable.add(lang)
    if not executable:
        executable = set(DEFAULT_EXECUTABLE)

    cells = parse(markdown, executable, strip_fm=not args.keep_frontmatter)
    if not any(c["cell_type"] == "code" for c in cells):
        print(
            "warning: no runnable code cells found. Check --lang matches the "
            "fenced code language in the tutorial (e.g. ```python).",
            file=sys.stderr,
        )
    notebook = build_notebook(cells)

    out_path = Path(args.output or default_out)
    out_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    code_n = sum(1 for c in cells if c["cell_type"] == "code")
    md_n = sum(1 for c in cells if c["cell_type"] == "markdown")
    print(f"wrote {out_path}  ({md_n} markdown cells, {code_n} code cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
