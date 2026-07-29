#!/usr/bin/env python3
"""Collect a local Go review target and render a focused review prompt.

This script never talks to GitLab/GitHub. It reads Go source from the local
filesystem in one of three modes:

  * --diff [REV]   : `git diff REV` (default REV=HEAD) tracked changes
  * --staged       : `git diff --cached` staged changes
  * PATH...        : one or more .go files or directories

It then renders a single-focus review prompt from a markdown template in
assets/prompts/ (or a custom --prompt-file), embedding the collected Go code
plus lightweight repo context (module path, detected frameworks).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROMPTS_DIR = SKILL_DIR / "assets" / "prompts"

BUILTIN_FOCUSES = {
    "correctness": PROMPTS_DIR / "correctness-review.md",
    "concurrency": PROMPTS_DIR / "concurrency-review.md",
    "security": PROMPTS_DIR / "security-review.md",
    "performance": PROMPTS_DIR / "performance-review.md",
    "idiomatic": PROMPTS_DIR / "idiomatic-review.md",
    "testing": PROMPTS_DIR / "testing-review.md",
}

FOCUS_ALIASES = {
    "default": "correctness",
    "correct": "correctness",
    "bugs": "correctness",
    "bug": "correctness",
    "concurrent": "concurrency",
    "race": "concurrency",
    "goroutine": "concurrency",
    "sec": "security",
    "perf": "performance",
    "style": "idiomatic",
    "idioms": "idiomatic",
    "maintainability": "idiomatic",
    "tests": "testing",
    "test": "testing",
}

GO_FRAMEWORK_HINTS = {
    "github.com/gin-gonic/gin": "Gin",
    "github.com/labstack/echo": "Echo",
    "github.com/gofiber/fiber": "Fiber",
    "github.com/go-chi/chi": "chi",
    "gorm.io/gorm": "GORM",
    "github.com/jmoiron/sqlx": "sqlx",
    "github.com/go-resty/resty": "Resty",
    "github.com/spf13/cobra": "Cobra",
    "google.golang.org/grpc": "gRPC",
    "github.com/redis/go-redis": "Redis",
    "github.com/segmentio/kafka-go": "Kafka",
    "github.com/ibm/sarama": "Kafka",
    "github.com/stretchr/testify": "testify",
}

DEFAULT_MAX_FILES = 25
DEFAULT_MAX_CHARS = 60000
SKIP_DIR_MARKERS = ("/vendor/", "/node_modules/", "/.git/", "/testdata/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a local Go code review prompt (no VCS server calls).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Go files or directories to review. Ignored when --diff/--staged is used.",
    )
    parser.add_argument(
        "--diff",
        nargs="?",
        const="HEAD",
        default=None,
        metavar="REV",
        help="Review `git diff REV` tracked changes (default REV=HEAD).",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Review staged changes via `git diff --cached`.",
    )
    parser.add_argument(
        "--focus",
        default=os.getenv("GO_REVIEW_FOCUS") or "correctness",
        help="Review focus: correctness, concurrency, security, performance, idiomatic, testing.",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Custom markdown prompt template. Overrides --focus.",
    )
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Project root used to collect module and framework context.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=int(os.getenv("GO_REVIEW_MAX_FILES", str(DEFAULT_MAX_FILES))),
        help="Maximum number of files to include.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=int(os.getenv("GO_REVIEW_MAX_CHARS", str(DEFAULT_MAX_CHARS))),
        help="Maximum total characters of code/diff to include.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include *_test.go files when scanning directories.",
    )
    parser.add_argument(
        "--format",
        choices=("prompt", "code", "context"),
        default="prompt",
        help="Output format. 'prompt' renders the template; 'code'/'context' print raw sections.",
    )
    parser.add_argument(
        "--output-file",
        help="Write the result to a file instead of stdout.",
    )
    return parser.parse_args()


def normalize_focus(focus: str) -> str:
    normalized = focus.strip().lower()
    return FOCUS_ALIASES.get(normalized, normalized)


def resolve_prompt_file(focus: str, prompt_file: Optional[str]) -> Path:
    if prompt_file:
        return Path(prompt_file)
    normalized = normalize_focus(focus)
    path = BUILTIN_FOCUSES.get(normalized)
    if path:
        return path
    available = ", ".join(sorted(BUILTIN_FOCUSES))
    raise ValueError(
        "unsupported focus '{focus}'. Supported: {available}".format(
            focus=focus, available=available
        )
    )


def run_git(project_root: Path, args: List[str]) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not available in this environment") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise ValueError("git command failed: {err}".format(err=stderr)) from exc
    return result.stdout


def repo_root(project_root: Path) -> Path:
    try:
        top = run_git(project_root, ["rev-parse", "--show-toplevel"]).strip()
        if top:
            return Path(top)
    except ValueError:
        pass
    return project_root


def collect_diff(project_root: Path, rev: Optional[str], staged: bool) -> Tuple[str, List[str]]:
    if staged:
        args = ["diff", "--cached", "--find-renames", "--", "*.go"]
        label = "git diff --cached"
    else:
        args = ["diff", "--find-renames", rev or "HEAD", "--", "*.go"]
        label = "git diff {rev}".format(rev=rev or "HEAD")
    diff_text = run_git(project_root, args)
    paths = re.findall(r"^\+\+\+ b/(.+)$", diff_text, flags=re.MULTILINE)
    return diff_text, paths, label  # type: ignore[return-value]


def is_skippable(path: str) -> bool:
    normalized = "/" + path.replace("\\", "/").strip("/") + "/"
    return any(marker in normalized for marker in SKIP_DIR_MARKERS)


def gather_go_files(paths: Iterable[str], include_tests: bool) -> List[Path]:
    collected: List[Path] = []
    seen = set()
    for raw in paths:
        p = Path(raw).resolve()
        if p.is_file() and p.suffix == ".go":
            if p not in seen:
                collected.append(p)
                seen.add(p)
        elif p.is_dir():
            for go_file in sorted(p.rglob("*.go")):
                if is_skippable(str(go_file)):
                    continue
                if not include_tests and go_file.name.endswith("_test.go"):
                    continue
                if go_file not in seen:
                    collected.append(go_file)
                    seen.add(go_file)
    return collected


def read_files_as_code(files: List[Path], max_files: int, max_chars: int) -> Tuple[str, List[str], List[str]]:
    parts: List[str] = []
    included: List[str] = []
    omitted: List[str] = []
    used_chars = 0
    for f in files:
        rel = _display_path(f)
        if len(included) >= max_files:
            omitted.append(rel)
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            omitted.append(rel)
            continue
        block = "// FILE: {rel}\n```go\n{content}\n```".format(rel=rel, content=content.rstrip())
        if used_chars + len(block) > max_chars and included:
            omitted.append(rel)
            continue
        parts.append(block)
        included.append(rel)
        used_chars += len(block)
    return "\n\n".join(parts), included, omitted


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n... truncated to fit review budget."


def collect_repo_context(root: Path) -> Dict[str, str]:
    go_mod = root / "go.mod"
    module = "unknown"
    go_version = "unknown"
    frameworks: List[str] = []
    if go_mod.exists():
        try:
            text = go_mod.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        m = re.search(r"^module\s+(\S+)", text, flags=re.MULTILINE)
        if m:
            module = m.group(1)
        v = re.search(r"^go\s+(\S+)", text, flags=re.MULTILINE)
        if v:
            go_version = v.group(1)
        lowered = text.lower()
        for needle, name in GO_FRAMEWORK_HINTS.items():
            if needle.lower() in lowered and name not in frameworks:
                frameworks.append(name)
    loop_note = ""
    if go_version not in ("unknown",):
        try:
            major_minor = tuple(int(x) for x in go_version.split(".")[:2])
            if major_minor < (1, 22):
                loop_note = " (pre-1.22: for-loop variables are shared per loop; watch capture bugs)"
            else:
                loop_note = " (1.22+: for-loop variables are per-iteration)"
        except ValueError:
            loop_note = ""
    lines = [
        "## Project Context",
        "",
        "- Module: `{module}`".format(module=module),
        "- Go version: `{v}`{note}".format(v=go_version, note=loop_note),
        "- Frameworks/stack: {fw}".format(
            fw=", ".join(frameworks) if frameworks else "none detected in go.mod"
        ),
    ]
    return {
        "project_context": "\n".join(lines),
        "go_version": go_version,
        "project_frameworks": ", ".join(frameworks) if frameworks else "none detected",
    }


def render(template: str, ctx: Dict[str, str]) -> str:
    out = template
    for key, value in ctx.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def main() -> int:
    args = parse_args()
    root = repo_root(Path(args.project_root).resolve())

    using_diff = args.diff is not None or args.staged
    if not using_diff and not args.paths:
        print(
            "Provide Go file/dir paths, or use --diff [REV] / --staged to review local changes.",
            file=sys.stderr,
        )
        return 2

    try:
        focus = normalize_focus(args.focus)
        prompt_file = resolve_prompt_file(args.focus, args.prompt_file)
    except ValueError as exc:
        print("Error: {err}".format(err=exc), file=sys.stderr)
        return 2

    scope_lines: List[str] = ["## Review Scope", ""]
    try:
        if using_diff:
            diff_text, changed_paths, label = collect_diff(root, args.diff, args.staged)
            if not diff_text.strip():
                print(
                    "No Go changes found for {label}. Stage/commit changes or pass file paths.".format(
                        label=label
                    ),
                    file=sys.stderr,
                )
                return 1
            code = truncate(diff_text, args.max_chars)
            scope_lines += [
                "- Mode: {label} (Go files only)".format(label=label),
                "- Changed Go files: {n}".format(n=len(changed_paths)),
            ]
            language = "Go (unified diff)"
        else:
            files = gather_go_files(args.paths, args.include_tests)
            if not files:
                print("No .go files found in the provided paths.", file=sys.stderr)
                return 1
            code, included, omitted = read_files_as_code(files, args.max_files, args.max_chars)
            scope_lines += [
                "- Mode: local files/directories",
                "- Files included: {n}".format(n=len(included)),
                "- Files omitted (budget): {n}".format(n=len(omitted)),
            ]
            if omitted:
                preview = ", ".join(omitted[:8]) + (", ..." if len(omitted) > 8 else "")
                scope_lines.append("- Omitted: {preview}".format(preview=preview))
            language = "Go"
    except ValueError as exc:
        print("Error: {err}".format(err=exc), file=sys.stderr)
        return 1

    repo_ctx = collect_repo_context(root)
    ctx = {
        "language": language,
        "review_focus": focus,
        "review_scope": "\n".join(scope_lines),
        "project_context": repo_ctx["project_context"],
        "go_version": repo_ctx["go_version"],
        "project_frameworks": repo_ctx["project_frameworks"],
        "code": code,
    }

    if args.format == "code":
        output = code
    elif args.format == "context":
        output = repo_ctx["project_context"]
    else:
        template = prompt_file.read_text(encoding="utf-8")
        output = render(template, ctx)

    if args.output_file:
        out_path = Path(args.output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
