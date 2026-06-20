#!/usr/bin/env python3
"""
Generate a PlantUML mindmap from Markdown and render it to an image.

This script serves as:
1. A CLI wrapper for manual use.
2. A Promptfoo Python provider for end-to-end evaluation.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from markdown_to_mindmap import markdown_to_mindmap


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    safe = safe.strip(".-")
    return safe or "mindmap"


def _resolve_output_path(output_path: str, base_dir: Path | None = None) -> Path:
    path = Path(output_path)
    resolved = (base_dir / path).resolve() if base_dir and not path.is_absolute() else path.resolve()
    if base_dir is not None:
        base_resolved = base_dir.resolve()
        if base_resolved not in resolved.parents and resolved != base_resolved:
            raise ValueError(f"Output path escapes allowed base directory: {resolved}")
    return resolved


def render_markdown_to_image(
    markdown_text: str,
    output_image: Path,
    title: str | None = None,
    output_puml: Path | None = None,
) -> dict:
    output_image.parent.mkdir(parents=True, exist_ok=True)
    if output_puml is None:
        output_puml = output_image.with_suffix(".puml")
    output_puml.parent.mkdir(parents=True, exist_ok=True)

    mindmap = markdown_to_mindmap(markdown_text, default_title=title or "Markdown Mindmap")
    output_puml.write_text(mindmap, encoding="utf-8")

    renderer = Path(__file__).with_name("render_diagram.py")
    if shutil.which("uv"):
        cmd = ["uv", "run", str(renderer), "plantuml", "-i", str(output_puml), "-o", str(output_image)]
    else:
        cmd = [
            sys.executable,
            str(renderer),
            "plantuml",
            "-i",
            str(output_puml),
            "-o",
            str(output_image),
        ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(stderr or f"Renderer exited with code {exc.returncode}") from exc

    return {
        "success": output_image.exists() and output_image.stat().st_size > 0,
        "image_path": str(output_image),
        "puml_path": str(output_puml),
        "image_bytes": output_image.stat().st_size if output_image.exists() else 0,
        "mindmap": mindmap,
    }


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    base_dir = Path(config.get("basePath", ".")).resolve()
    output_dir = _resolve_output_path(config.get("outputDir", ".tmp-output"), base_dir=base_dir)
    vars_map = (context or {}).get("vars", {}) or {}
    name = _safe_name(str(vars_map.get("name", f"case-{int(time.time() * 1000)}")))
    title = vars_map.get("title")

    markdown_text = prompt
    markdown_path = vars_map.get("markdown_path")
    if markdown_path:
        md_path = (base_dir / str(markdown_path)).resolve()
        markdown_text = md_path.read_text(encoding="utf-8")
        if title is None:
            title = md_path.stem.replace("_", " ").replace("-", " ").title()

    image_path = output_dir / f"{name}.png"
    puml_path = output_dir / f"{name}.puml"

    try:
        result = render_markdown_to_image(markdown_text, image_path, title=title, output_puml=puml_path)
        return {
            "output": json.dumps(result, ensure_ascii=False),
            "metadata": result,
        }
    except Exception as exc:
        return {
            "output": json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False),
            "error": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and render a PlantUML mindmap from Markdown.")
    parser.add_argument("-i", "--input", required=True, help="Input Markdown file path")
    parser.add_argument("-o", "--output-image", required=True, help="Output PNG path")
    parser.add_argument("--output-puml", help="Optional output .puml path")
    parser.add_argument("--title", help="Fallback title when Markdown has no H1 heading")
    args = parser.parse_args()

    markdown_path = Path(args.input).resolve()
    markdown_text = markdown_path.read_text(encoding="utf-8")
    output_image = Path(args.output_image).resolve()
    output_puml = Path(args.output_puml).resolve() if args.output_puml else None
    title = args.title or markdown_path.stem.replace("_", " ").replace("-", " ").title()

    result = render_markdown_to_image(markdown_text, output_image, title=title, output_puml=output_puml)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
