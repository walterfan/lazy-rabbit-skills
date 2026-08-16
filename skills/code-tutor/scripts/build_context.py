#!/usr/bin/env python3
"""Assemble a GROUNDED diagnosis context for the code-tutor skill.

The whole point of code-tutor is to debug a learner's cell using *real* context
instead of guessing: the cells they already ran, the error (or confusing result)
they actually got, and the gotcha markers the tutorial author planted. This
script gathers exactly that from a notebook and prints a compact bundle for the
tutor to reason over.

It also runs two cheap static checks that catch the two most common newcomer
slips before an LLM is even involved:

  * used-but-undefined names in the failing cell  -> "you skipped a step / the
    cell that defines this was never run" (the classic auth-ordering gotcha);
  * a syntax error in the failing cell             -> point at the exact line.

Stdlib only. Never executes notebook code; only parses it.

Usage:
    python build_context.py NOTEBOOK.ipynb --cell 3 --error "$(pbpaste)"
    python build_context.py NB.ipynb --cell 3 --error-file err.txt --format md
    python build_context.py NB.ipynb --cell 3          # no error: soft/"empty result" case
"""
from __future__ import annotations

import argparse
import ast
import builtins
import json
import re
import sys
from pathlib import Path

EXPECTED_RE = re.compile(r"#\s*(?:→|->|=>|expected:?)\s*(.+)", re.IGNORECASE)
# A gotcha marker block, as emitted by tutorial-to-notebook:
#   > ⚠️ **常见坑 · 异步任务**
#   > 症状：...   原因：...   修复：...
GOTCHA_HEAD_RE = re.compile(r"⚠️|常见坑|gotcha|pitfall|\bcaveat\b", re.IGNORECASE)
FIELD_RE = re.compile(
    r"(症状|原因|修复|symptom|cause|fix)\s*[：:]\s*(.+)", re.IGNORECASE
)
BUILTINS = set(dir(builtins)) | {"__name__", "__file__", "self", "cls"}


def load_cells(path: Path) -> list[dict]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb.get("cells", [])
    for idx, c in enumerate(cells):
        c["_index"] = idx
        c["_text"] = "".join(c.get("source", []))
    return cells


def parse_gotchas(cells: list[dict]) -> list[dict]:
    """Extract structured gotcha markers from markdown cells."""
    out: list[dict] = []
    for c in cells:
        if c.get("cell_type") != "markdown":
            continue
        lines = c["_text"].split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if GOTCHA_HEAD_RE.search(line) and (">" in line or line.strip().startswith("#")):
                title = re.sub(r"^[>\s#*⚠️]+", "", line).strip().strip("*")
                fields: dict[str, str] = {}
                j = i + 1
                while j < len(lines):
                    body = lines[j].lstrip("> ").strip()
                    fm = FIELD_RE.match(body)
                    if fm:
                        key = fm.group(1).lower()
                        key = {"symptom": "症状", "cause": "原因", "fix": "修复"}.get(key, key)
                        fields[key] = fm.group(2).strip()
                        j += 1
                        continue
                    if body == "" or (not lines[j].lstrip().startswith(">") and lines[j].strip() != ""):
                        break
                    j += 1
                out.append({
                    "title": title,
                    "symptom": fields.get("症状", ""),
                    "cause": fields.get("原因", ""),
                    "fix": fields.get("修复", ""),
                })
                i = j
            else:
                i += 1
    return out


def expected_outputs(cells: list[dict], upto: int) -> list[dict]:
    out = []
    for c in cells:
        if c.get("cell_type") != "code" or c["_index"] > upto:
            continue
        for m in EXPECTED_RE.finditer(c["_text"]):
            out.append({"cell": c["_index"], "expected": m.group(1).strip()})
    return out


def _assigned_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    names.add(item.optional_vars.id)
    return names


def _loaded_names(tree: ast.AST) -> set[str]:
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


def static_checks(cells: list[dict], target_idx: int) -> dict:
    """Best-effort static analysis: syntax error + used-but-undefined names."""
    result: dict = {"syntax_error": None, "undefined_names": [], "note": ""}
    target = next((c for c in cells if c["_index"] == target_idx), None)
    if target is None or target.get("cell_type") != "code":
        result["note"] = "target cell is not a code cell"
        return result

    # 1. syntax error in the failing cell
    try:
        target_tree = ast.parse(target["_text"])
    except SyntaxError as e:
        result["syntax_error"] = {"line": e.lineno, "offset": e.offset, "msg": e.msg}
        return result

    # 2. names loaded in target but never assigned in target or any prior code cell
    prior_assigned: set[str] = set()
    for c in cells:
        if c.get("cell_type") != "code" or c["_index"] >= target_idx:
            continue
        try:
            prior_assigned |= _assigned_names(ast.parse(c["_text"]))
        except SyntaxError:
            continue
    target_assigned = _assigned_names(target_tree)
    used = _loaded_names(target_tree)
    undefined = sorted(used - target_assigned - prior_assigned - BUILTINS)
    result["undefined_names"] = undefined
    if undefined:
        result["note"] = (
            "These names are used here but were never defined in this cell or an "
            "earlier one — the learner likely skipped or never ran the cell that "
            "defines them (classic 'skipped a step' / auth-ordering slip)."
        )
    return result


def build(path: Path, target_idx: int, error: str) -> dict:
    cells = load_cells(path)
    n_code = sum(1 for c in cells if c.get("cell_type") == "code")
    target = next((c for c in cells if c["_index"] == target_idx), None)
    prior_code = [
        {"index": c["_index"], "source": c["_text"]}
        for c in cells
        if c.get("cell_type") == "code" and c["_index"] < target_idx
    ]
    return {
        "notebook": str(path),
        "code_cell_count": n_code,
        "target_cell": {
            "index": target_idx,
            "source": target["_text"] if target else None,
        },
        "prior_code_cells": prior_code,
        "error_or_result": error.strip(),
        "has_hard_error": bool(error.strip()) and _looks_like_traceback(error),
        "expected_outputs": expected_outputs(cells, target_idx),
        "gotcha_markers": parse_gotchas(cells),
        "static_checks": static_checks(cells, target_idx),
    }


_HTTP_STATUS_RE = re.compile(r"\b[45]\d\d\b")


def _looks_like_traceback(text: str) -> bool:
    """Distinguish a hard error (traceback / HTTP 4xx-5xx) from a soft gotcha.

    A soft gotcha is the dangerous case: no error at all, just a
    confusing/empty result (e.g. status=processing, text=null). We must NOT
    misclassify that as a hard error, so keep the signals specific.
    """
    t = text.lower()
    keyword = any(k in t for k in ("traceback", "error", "exception", "unauthorized", "forbidden"))
    return keyword or bool(_HTTP_STATUS_RE.search(text))


def to_markdown(ctx: dict) -> str:
    lines = ["# code-tutor diagnosis context", ""]
    lines.append(f"- notebook: `{ctx['notebook']}`")
    lines.append(f"- failing cell index: **{ctx['target_cell']['index']}** of {ctx['code_cell_count']} code cells")
    lines.append(f"- hard error present: {ctx['has_hard_error']}")
    sc = ctx["static_checks"]
    if sc.get("syntax_error"):
        se = sc["syntax_error"]
        lines.append(f"- ⚠️ syntax error at line {se['line']}: {se['msg']}")
    if sc.get("undefined_names"):
        lines.append(f"- ⚠️ used-but-undefined names: `{', '.join(sc['undefined_names'])}` — {sc['note']}")
    lines += ["", "## Failing cell", "```python", ctx["target_cell"]["source"] or "", "```", ""]
    lines.append("## Error / unexpected result the learner got")
    lines += ["```", ctx["error_or_result"] or "(none reported — likely a silent/empty-result gotcha)", "```", ""]
    if ctx["prior_code_cells"]:
        lines.append("## Prior code cells (state the learner should have)")
        for c in ctx["prior_code_cells"]:
            lines += [f"### cell {c['index']}", "```python", c["source"], "```"]
        lines.append("")
    if ctx["expected_outputs"]:
        lines.append("## Author-annotated expected outputs")
        for e in ctx["expected_outputs"]:
            lines.append(f"- cell {e['cell']}: `{e['expected']}`")
        lines.append("")
    if ctx["gotcha_markers"]:
        lines.append("## Gotcha markers the tutorial author planted (match against these FIRST)")
        for g in ctx["gotcha_markers"]:
            lines.append(f"- **{g['title']}** — 症状: {g['symptom']} | 原因: {g['cause']} | 修复: {g['fix']}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebook", help="Path to the .ipynb the learner is running")
    ap.add_argument("--cell", type=int, required=True, help="Index of the failing code cell")
    ap.add_argument("--error", default="", help="The error text or confusing result the learner got")
    ap.add_argument("--error-file", help="Read the error text from a file instead of --error")
    ap.add_argument("--format", choices=["json", "md"], default="json")
    args = ap.parse_args(argv)

    path = Path(args.notebook)
    if not path.is_file():
        print(f"error: notebook not found: {path}", file=sys.stderr)
        return 2
    error = args.error
    if args.error_file:
        ef = Path(args.error_file)
        if not ef.is_file():
            print(f"error: error-file not found: {ef}", file=sys.stderr)
            return 2
        error = ef.read_text(encoding="utf-8")

    ctx = build(path, args.cell, error)
    if args.format == "md":
        print(to_markdown(ctx))
    else:
        print(json.dumps(ctx, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
