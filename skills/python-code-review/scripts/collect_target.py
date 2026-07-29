#!/usr/bin/env python3
"""Collect a local Python review target and render a focused review prompt.

This script never talks to GitLab/GitHub. It reads Python source from the local
filesystem in one of three modes:

  * --diff [REV]   : `git diff REV` (default REV=HEAD) tracked changes
  * --staged       : `git diff --cached` staged changes
  * PATH...        : one or more .py files or directories

It then renders a single-focus review prompt from a markdown template in
assets/prompts/ (or a custom --prompt-file), embedding the collected Python code
plus lightweight repo context (Python version, tooling, Pydantic usage).
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
    "pitfalls": PROMPTS_DIR / "pitfalls-review.md",
    "concurrency": PROMPTS_DIR / "concurrency-review.md",
    "performance": PROMPTS_DIR / "performance-review.md",
    "security": PROMPTS_DIR / "security-review.md",
    "typing-tooling": PROMPTS_DIR / "typing-tooling-review.md",
    "pydantic": PROMPTS_DIR / "pydantic-review.md",
    "testing": PROMPTS_DIR / "testing-review.md",
}

FOCUS_ALIASES = {
    "default": "correctness",
    "correct": "correctness",
    "bugs": "correctness",
    "bug": "correctness",
    "traps": "pitfalls",
    "trap": "pitfalls",
    "gotchas": "pitfalls",
    "pitfall": "pitfalls",
    "concurrent": "concurrency",
    "async": "concurrency",
    "asyncio": "concurrency",
    "gil": "concurrency",
    "thread": "concurrency",
    "threading": "concurrency",
    "perf": "performance",
    "sec": "security",
    "typing": "typing-tooling",
    "types": "typing-tooling",
    "tooling": "typing-tooling",
    "lint": "typing-tooling",
    "mypy": "typing-tooling",
    "maintainability": "typing-tooling",
    "validation": "pydantic",
    "models": "pydantic",
    "tests": "testing",
    "test": "testing",
}

# Library / framework hints detected from manifests and imports.
PY_LIB_HINTS = {
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "starlette": "Starlette",
    "pydantic-settings": "pydantic-settings",
    "pydantic_settings": "pydantic-settings",
    "sqlalchemy": "SQLAlchemy",
    "tortoise": "Tortoise ORM",
    "celery": "Celery",
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    "requests": "requests",
    "pandas": "pandas",
    "numpy": "numpy",
    "pytest": "pytest",
    "asyncio": "asyncio",
    "sqlmodel": "SQLModel",
}

DEFAULT_MAX_FILES = 25
DEFAULT_MAX_CHARS = 60000
SKIP_DIR_MARKERS = (
    "/.git/", "/.venv/", "/venv/", "/env/", "/node_modules/",
    "/__pycache__/", "/.mypy_cache/", "/.pytest_cache/", "/.ruff_cache/",
    "/build/", "/dist/", "/.tox/", "/.eggs/", "/site-packages/",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a local Python code review prompt (no VCS server calls).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Python files or directories to review. Ignored when --diff/--staged is used.",
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
        default=os.getenv("PY_REVIEW_FOCUS") or "correctness",
        help="Review focus: correctness, pitfalls, concurrency, performance, "
             "security, typing-tooling, pydantic, testing.",
    )
    parser.add_argument(
        "--py",
        default=os.getenv("PY_REVIEW_PY") or None,
        help="Python version the code targets, e.g. 3.9/3.10/3.12. Overrides "
             "auto-detection. Ask the user if it cannot be detected.",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Custom markdown prompt template. Overrides --focus.",
    )
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="Project root used to collect Python version, tooling, and library context.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=int(os.getenv("PY_REVIEW_MAX_FILES", str(DEFAULT_MAX_FILES))),
        help="Maximum number of files to include.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=int(os.getenv("PY_REVIEW_MAX_CHARS", str(DEFAULT_MAX_CHARS))),
        help="Maximum total characters of code/diff to include.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files (test_*.py / *_test.py / tests/) when scanning directories.",
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


def collect_diff(project_root: Path, rev: Optional[str], staged: bool) -> Tuple[str, List[str], str]:
    if staged:
        args = ["diff", "--cached", "--find-renames", "--", "*.py", "*.pyi"]
        label = "git diff --cached"
    else:
        args = ["diff", "--find-renames", rev or "HEAD", "--", "*.py", "*.pyi"]
        label = "git diff {rev}".format(rev=rev or "HEAD")
    diff_text = run_git(project_root, args)
    paths = re.findall(r"^\+\+\+ b/(.+)$", diff_text, flags=re.MULTILINE)
    return diff_text, paths, label


def is_skippable(path: str) -> bool:
    normalized = "/" + path.replace("\\", "/").strip("/") + "/"
    return any(marker in normalized for marker in SKIP_DIR_MARKERS)


def _is_test_path(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    parts = {p.lower() for p in path.parts}
    return "tests" in parts or "test" in parts


def gather_py_files(paths: Iterable[str], include_tests: bool) -> List[Path]:
    collected: List[Path] = []
    seen = set()
    for raw in paths:
        p = Path(raw).resolve()
        if p.is_file() and p.suffix in (".py", ".pyi"):
            if p not in seen:
                collected.append(p)
                seen.add(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if not f.is_file() or f.suffix not in (".py", ".pyi"):
                    continue
                if is_skippable(str(f)):
                    continue
                if not include_tests and _is_test_path(f):
                    continue
                if f not in seen:
                    collected.append(f)
                    seen.add(f)
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
        block = "# FILE: {rel}\n```python\n{content}\n```".format(rel=rel, content=content.rstrip())
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


def _normalize_py(value: str) -> str:
    v = value.strip().lower().replace("python", "").replace("py", "").replace("cpython", "").strip()
    m = re.search(r"(\d+)\.(\d+)", v)
    if m:
        return "Python {}.{}".format(m.group(1), m.group(2))
    if v.isdigit():
        return "Python " + v
    return value.strip()


def _detect_py_version(text: str) -> str:
    # pyproject: requires-python = ">=3.10" / target-version = "py312" / python_version = "3.12"
    m = re.search(r"target-version\s*=\s*['\"]py(\d)(\d+)['\"]", text)
    if m:
        return "Python {}.{}".format(m.group(1), m.group(2))
    m = re.search(r"python_version\s*=\s*['\"](\d+\.\d+)['\"]", text)
    if m:
        return "Python " + m.group(1)
    m = re.search(r"requires-python\s*=\s*['\"][>=~^ ]*(\d+\.\d+)", text)
    if m:
        return "Python " + m.group(1)
    m = re.search(r"python_requires\s*=\s*['\"]?[>=~^ ]*(\d+\.\d+)", text)
    if m:
        return "Python " + m.group(1)
    return ""


def detect_tooling(text: str) -> List[str]:
    tools = []
    checks = {
        "ruff": r"\bruff\b",
        "flake8": r"\bflake8\b",
        "mypy": r"\bmypy\b",
        "pyright": r"\bpyright\b",
        "black": r"\bblack\b",
        "isort": r"\bisort\b",
        "pylint": r"\bpylint\b",
        "pytest": r"\bpytest\b",
        "poetry": r"\[tool\.poetry\]|\bpoetry\b",
        "uv": r"\buv\b|\[tool\.uv\]",
    }
    lowered = text.lower()
    for name, pat in checks.items():
        if re.search(pat, lowered):
            tools.append(name)
    return tools


def detect_pydantic(text: str, code: str) -> str:
    """Return 'v2', 'v1', 'yes (version unclear)', or '' for the Pydantic usage."""
    combined = (text + "\n" + code).lower()
    uses = bool(
        re.search(r"\bpydantic\b", combined)
        or re.search(r"from pydantic", code.lower())
        or re.search(r"import pydantic", code.lower())
    )
    if not uses:
        return ""
    # v2 signals
    v2 = bool(re.search(r"model_validate|model_dump|field_validator|model_validator|"
                        r"model_config\s*=|ConfigDict|TypeAdapter|pydantic-?settings|"
                        r"pydantic\s*[>=~]=?\s*2", combined))
    # v1 signals
    v1 = bool(re.search(r"\bparse_obj\b|@validator\b|@root_validator\b|\.dict\(\)|"
                        r"class Config:|pydantic\s*[<>=~]=?\s*1", combined))
    if v2 and not v1:
        return "v2"
    if v1 and not v2:
        return "v1"
    if v1 and v2:
        return "MIXED v1/v2 (risk)"
    return "yes (version unclear)"


def collect_repo_context(root: Path, py_override: Optional[str], code: str) -> Dict[str, str]:
    py_version = "unknown"
    tooling: List[str] = []
    libraries: List[str] = []
    combined_text = ""

    manifest_files = [
        "pyproject.toml", "setup.cfg", "setup.py", "requirements.txt",
        "requirements-dev.txt", "tox.ini", "Pipfile", ".pre-commit-config.yaml",
        "mypy.ini", ".flake8",
    ]
    for fname in manifest_files:
        fpath = root / fname
        if fpath.exists():
            try:
                combined_text += "\n" + fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    # also scan any requirements*.txt
    for fpath in sorted(root.glob("requirements*.txt")):
        try:
            combined_text += "\n" + fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass

    # Python version: explicit override wins.
    if py_override:
        py_version = _normalize_py(py_override)
    else:
        detected = _detect_py_version(combined_text)
        if detected:
            py_version = detected

    tooling = detect_tooling(combined_text)

    lowered = (combined_text + "\n" + code).lower()
    for needle, name in PY_LIB_HINTS.items():
        if needle.lower() in lowered and name not in libraries:
            libraries.append(name)

    pydantic_usage = detect_pydantic(combined_text, code)

    py_source = "user-specified" if py_override else "auto-detected"
    lines = [
        "## Project Context",
        "",
        "- Python version: `{v}` ({src})".format(v=py_version, src=py_source),
        "- Tooling detected: {t}".format(t=", ".join(tooling) if tooling else "none detected"),
        "- Libraries/frameworks: {libs}".format(
            libs=", ".join(libraries) if libraries else "none detected"
        ),
        "- Pydantic: {p}".format(p=pydantic_usage if pydantic_usage else "not detected"),
    ]
    if py_version == "unknown":
        lines.append(
            "- NOTE: Python version unknown — ASK THE USER which version they "
            "target (e.g. 3.9/3.10/3.11/3.12) before giving version-specific "
            "suggestions (walrus :=, dict |, match, X | None syntax)."
        )
    if pydantic_usage == "MIXED v1/v2 (risk)":
        lines.append(
            "- WARNING: mixed Pydantic v1 and v2 signals — confirm the version; "
            "v1/v2 APIs differ (parse_obj vs model_validate, etc.)."
        )
    return {
        "project_context": "\n".join(lines),
        "py_version": py_version,
        "project_frameworks": ", ".join(libraries) if libraries else "none detected",
        "tooling": ", ".join(tooling) if tooling else "none detected",
        "pydantic_usage": pydantic_usage if pydantic_usage else "not detected",
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
            "Provide Python file/dir paths, or use --diff [REV] / --staged to review local changes.",
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
                    "No Python changes found for {label}. Stage/commit changes or pass file paths.".format(
                        label=label
                    ),
                    file=sys.stderr,
                )
                return 1
            code = truncate(diff_text, args.max_chars)
            scope_lines += [
                "- Mode: {label} (Python files only)".format(label=label),
                "- Changed Python files: {n}".format(n=len(changed_paths)),
            ]
            language = "Python (unified diff)"
        else:
            files = gather_py_files(args.paths, args.include_tests)
            if not files:
                print("No Python files found in the provided paths.", file=sys.stderr)
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
            language = "Python"
    except ValueError as exc:
        print("Error: {err}".format(err=exc), file=sys.stderr)
        return 1

    repo_ctx = collect_repo_context(root, args.py, code)
    ctx = {
        "language": language,
        "review_focus": focus,
        "review_scope": "\n".join(scope_lines),
        "project_context": repo_ctx["project_context"],
        "py_version": repo_ctx["py_version"],
        "project_frameworks": repo_ctx["project_frameworks"],
        "tooling": repo_ctx["tooling"],
        "pydantic_usage": repo_ctx["pydantic_usage"],
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
