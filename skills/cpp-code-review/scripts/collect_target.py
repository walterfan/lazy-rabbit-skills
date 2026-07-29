#!/usr/bin/env python3
"""Collect a local C++ review target and render a focused review prompt.

This script never talks to GitLab/GitHub. It reads C++ source from the local
filesystem in one of three modes:

  * --diff [REV]   : `git diff REV` (default REV=HEAD) tracked changes
  * --staged       : `git diff --cached` staged changes
  * PATH...        : one or more C++ files or directories

It then renders a single-focus review prompt from a markdown template in
assets/prompts/ (or a custom --prompt-file), embedding the collected C++ code
plus lightweight repo context (build system, C++ standard, detected libraries).
"""

from __future__ import annotations

import argparse
import json
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
    "memory": PROMPTS_DIR / "memory-review.md",
    "concurrency": PROMPTS_DIR / "concurrency-review.md",
    "performance": PROMPTS_DIR / "performance-review.md",
    "security": PROMPTS_DIR / "security-review.md",
    "api-lifetime": PROMPTS_DIR / "api-lifetime-review.md",
    "testing": PROMPTS_DIR / "testing-review.md",
    "modern-cpp": PROMPTS_DIR / "modern-cpp-review.md",
    "boost": PROMPTS_DIR / "boost-review.md",
}

FOCUS_ALIASES = {
    "default": "correctness",
    "correct": "correctness",
    "bugs": "correctness",
    "bug": "correctness",
    "ub": "correctness",
    "mem": "memory",
    "memory-safety": "memory",
    "leak": "memory",
    "leaks": "memory",
    "raii": "memory",
    "ownership": "memory",
    "concurrent": "concurrency",
    "race": "concurrency",
    "races": "concurrency",
    "thread": "concurrency",
    "threading": "concurrency",
    "perf": "performance",
    "sec": "security",
    "api": "api-lifetime",
    "lifetime": "api-lifetime",
    "interface": "api-lifetime",
    "dangling": "api-lifetime",
    "maintainability": "api-lifetime",
    "tests": "testing",
    "test": "testing",
    "modern": "modern-cpp",
    "modernize": "modern-cpp",
    "modern-c++": "modern-cpp",
    "cpp11": "modern-cpp",
    "cpp14": "modern-cpp",
    "cpp17": "modern-cpp",
    "cpp20": "modern-cpp",
    "cpp23": "modern-cpp",
    "boost-lib": "boost",
}

# Library / framework hints detected from build files and include directives.
CPP_LIB_HINTS = {
    "gtest/gtest.h": "GoogleTest",
    "gmock/gmock.h": "GoogleMock",
    "catch2/catch": "Catch2",
    "doctest.h": "doctest",
    "boost/": "Boost",
    "fmt/": "fmt",
    "spdlog/": "spdlog",
    "absl/": "Abseil",
    "grpcpp/": "gRPC",
    "google/protobuf": "Protobuf",
    "nlohmann/json": "nlohmann/json",
    "qcoreapplication": "Qt",
    "eigen/": "Eigen",
    "opencv2/": "OpenCV",
    "asio": "Asio",
}

CPP_EXTENSIONS = {
    ".cpp", ".cc", ".cxx", ".c++", ".hpp", ".hh", ".hxx", ".h++",
    ".h", ".ipp", ".inl", ".tpp", ".cppm", ".ixx",
}

DEFAULT_MAX_FILES = 25
DEFAULT_MAX_CHARS = 60000
SKIP_DIR_MARKERS = (
    "/build/", "/cmake-build-", "/.git/", "/node_modules/",
    "/third_party/", "/thirdparty/", "/external/", "/vendor/",
    "/.deps/", "/out/", "/_deps/",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a local C++ code review prompt (no VCS server calls).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="C++ files or directories to review. Ignored when --diff/--staged is used.",
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
        default=os.getenv("CPP_REVIEW_FOCUS") or "correctness",
        help="Review focus: correctness, memory, concurrency, performance, "
             "security, api-lifetime, testing, modern-cpp, boost.",
    )
    parser.add_argument(
        "--std",
        default=os.getenv("CPP_REVIEW_STD") or None,
        help="C++ standard the code targets, e.g. c++11/14/17/20/23. Overrides "
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
        help="Project root used to collect build system and library context.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=int(os.getenv("CPP_REVIEW_MAX_FILES", str(DEFAULT_MAX_FILES))),
        help="Maximum number of files to include.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=int(os.getenv("CPP_REVIEW_MAX_CHARS", str(DEFAULT_MAX_CHARS))),
        help="Maximum total characters of code/diff to include.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test files (paths containing 'test') when scanning directories.",
    )
    parser.add_argument(
        "--format",
        choices=("prompt", "code", "context", "json"),
        default="prompt",
        help="Output format. 'prompt' renders the template; 'code'/'context' print "
             "raw sections; 'json' emits a stable structured contract for automation.",
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
    raise ReviewError(
        "unsupported_focus",
        "unsupported focus '{focus}'.".format(focus=focus),
        ["Use one of: {available}.".format(available=available)],
    )


class ReviewError(ValueError):
    """A user-facing error carrying a short reason plus next-step suggestions.

    Kept intentionally small so both the human (stderr) and JSON output paths
    can render a concise conclusion and an actionable list of alternatives —
    never a raw multi-line git/help dump.
    """

    def __init__(self, code: str, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.suggestions = suggestions or []


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
        raise ReviewError(
            "git_missing",
            "git is not available in this environment.",
            [
                "Install git, or review specific files instead of a diff, e.g. "
                "`collect_target.py src/socket.cpp --focus memory`.",
            ],
        ) from exc
    except subprocess.CalledProcessError as exc:
        # Keep only the first meaningful stderr line — never echo the full git
        # usage/help block, which is pure noise for the reviewer.
        raw = (exc.stderr or exc.stdout or str(exc)).strip()
        first_line = next((ln.strip() for ln in raw.splitlines() if ln.strip()), str(exc))
        raise ReviewError(
            "git_command_failed",
            "git command failed: {err}".format(err=first_line),
            [
                "Pass --project-root pointing at the git repo root.",
                "Or review files directly instead of --diff/--staged, e.g. "
                "`collect_target.py path/to/file.cpp`.",
            ],
        ) from exc
    return result.stdout


def is_git_repo(project_root: Path) -> bool:
    try:
        out = run_git(project_root, ["rev-parse", "--is-inside-work-tree"]).strip()
        return out == "true"
    except ReviewError:
        return False


def has_valid_head(project_root: Path) -> bool:
    try:
        run_git(project_root, ["rev-parse", "--verify", "--quiet", "HEAD"])
        return True
    except ReviewError:
        return False


def precheck_diff_mode(project_root: Path, staged: bool) -> None:
    """Validate the environment for a --diff/--staged run before touching git.

    Emits concise ReviewErrors with next-step suggestions rather than letting a
    raw `git diff` failure dump the entire git help text.
    """
    if not is_git_repo(project_root):
        raise ReviewError(
            "not_a_git_repo",
            "'{root}' is not inside a git repository, so --diff/--staged "
            "cannot be used.".format(root=project_root),
            [
                "Review the files directly, e.g. "
                "`collect_target.py src/socket.cpp --focus memory`.",
                "Or point --project-root at a real git repo root.",
            ],
        )
    # A brand-new repo with no commits has no HEAD to diff against.
    if not staged and not has_valid_head(project_root):
        raise ReviewError(
            "no_valid_head",
            "The repository has no commits yet (no valid HEAD to diff against).",
            [
                "Make an initial commit, then retry --diff.",
                "Use --staged to review staged-but-uncommitted changes.",
                "Or review files directly: `collect_target.py path/to/file.cpp`.",
            ],
        )


def repo_root(project_root: Path) -> Path:
    try:
        top = run_git(project_root, ["rev-parse", "--show-toplevel"]).strip()
        if top:
            return Path(top)
    except ReviewError:
        pass
    return project_root


def _git_pathspecs() -> List[str]:
    # Restrict the diff to C++ files by extension.
    return ["*" + ext for ext in sorted(CPP_EXTENSIONS)]


def collect_diff(project_root: Path, rev: Optional[str], staged: bool) -> Tuple[str, List[str], str]:
    pathspecs = _git_pathspecs()
    if staged:
        args = ["diff", "--cached", "--find-renames", "--"] + pathspecs
        label = "git diff --cached"
    else:
        args = ["diff", "--find-renames", rev or "HEAD", "--"] + pathspecs
        label = "git diff {rev}".format(rev=rev or "HEAD")
    diff_text = run_git(project_root, args)
    paths = re.findall(r"^\+\+\+ b/(.+)$", diff_text, flags=re.MULTILINE)
    return diff_text, paths, label


def is_skippable(path: str) -> bool:
    normalized = "/" + path.replace("\\", "/").strip("/") + "/"
    return any(marker in normalized for marker in SKIP_DIR_MARKERS)


def _is_test_path(path: Path) -> bool:
    lowered = str(path).lower()
    return "test" in lowered or "mock" in lowered or lowered.endswith("_spec.cpp")


def gather_cpp_files(paths: Iterable[str], include_tests: bool) -> List[Path]:
    collected: List[Path] = []
    seen = set()
    for raw in paths:
        p = Path(raw).resolve()
        if p.is_file() and p.suffix.lower() in CPP_EXTENSIONS:
            if p not in seen:
                collected.append(p)
                seen.add(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if not f.is_file() or f.suffix.lower() not in CPP_EXTENSIONS:
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
        block = "// FILE: {rel}\n```cpp\n{content}\n```".format(rel=rel, content=content.rstrip())
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


def _detect_cpp_standard(text: str) -> str:
    # CMake: set(CMAKE_CXX_STANDARD 17) or target_compile_features(... cxx_std_20)
    m = re.search(r"CMAKE_CXX_STANDARD\s+(\d+)", text)
    if m:
        return "C++" + m.group(1)
    m = re.search(r"cxx_std_(\d+)", text)
    if m:
        return "C++" + m.group(1)
    m = re.search(r"-std=(?:gnu|c)\+\+(\w+)", text)
    if m:
        return "C++" + m.group(1)
    return ""


def _normalize_std(value: str) -> str:
    v = value.strip().lower().replace("gnu++", "").replace("c++", "").replace("cpp", "")
    v = v.strip()
    mapping = {"0x": "11", "1y": "14", "1z": "17", "2a": "20", "2b": "23", "2c": "26"}
    v = mapping.get(v, v)
    if v.isdigit():
        return "C++" + v
    return value.strip()


# boost:: identifiers that are values/helpers, not sub-library names.
_BOOST_NON_LIBS = {
    "none", "make_shared", "get", "bind", "ref", "cref", "move", "forward",
    "system", "placeholders",
}


def detect_boost_libraries(code: str) -> List[str]:
    """Detect which Boost sub-libraries appear in the reviewed code."""
    found = []
    # Prefer include paths — these name the sub-library directly.
    for m in re.finditer(r"#\s*include\s*[<\"]boost/([a-zA-Z0-9_]+)", code):
        lib = m.group(1)
        if lib not in found:
            found.append(lib)
    # Also catch boost:: qualified usage, filtering out value/helper identifiers.
    for m in re.finditer(r"\bboost::([a-zA-Z0-9_]+)", code):
        lib = m.group(1)
        if lib in _BOOST_NON_LIBS:
            continue
        if lib not in found:
            found.append(lib)
    return found


def collect_repo_context(root: Path, std_override: Optional[str], code: str) -> Dict[str, str]:
    build_system = "unknown"
    cpp_standard = "unknown"
    libraries: List[str] = []
    combined_text = ""

    build_files = {
        "CMakeLists.txt": "CMake",
        "meson.build": "Meson",
        "BUILD": "Bazel",
        "BUILD.bazel": "Bazel",
        "Makefile": "Make",
        "conanfile.txt": "Conan",
        "conanfile.py": "Conan",
        "vcpkg.json": "vcpkg",
    }
    detected_bs: List[str] = []
    for fname, bs in build_files.items():
        fpath = root / fname
        if fpath.exists():
            if bs not in detected_bs:
                detected_bs.append(bs)
            try:
                combined_text += "\n" + fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    if detected_bs:
        build_system = ", ".join(detected_bs)

    # C++ standard: explicit override wins over build-file detection.
    if std_override:
        cpp_standard = _normalize_std(std_override)
    else:
        std = _detect_cpp_standard(combined_text)
        if std:
            cpp_standard = std

    # Library hints from build files and from the reviewed code.
    lowered = (combined_text + "\n" + code).lower()
    for needle, name in CPP_LIB_HINTS.items():
        if needle.lower() in lowered and name not in libraries:
            libraries.append(name)

    boost_libs = detect_boost_libraries(code)
    boost_note = ""
    if boost_libs:
        if "Boost" not in libraries:
            libraries.append("Boost")
        preview = ", ".join(sorted(set(boost_libs))[:12])
        boost_note = "- Boost sub-libraries in code: {p}".format(p=preview)

    std_source = "user-specified" if std_override else "auto-detected"
    lines = [
        "## Project Context",
        "",
        "- Build system: `{bs}`".format(bs=build_system),
        "- C++ standard: `{std}` ({src})".format(std=cpp_standard, src=std_source),
        "- Libraries/frameworks: {libs}".format(
            libs=", ".join(libraries) if libraries else "none detected"
        ),
    ]
    if boost_note:
        lines.append(boost_note)

    # When the standard cannot be resolved, say *why* it failed and give the
    # user a concrete alternative input, so the modern-cpp/boost rounds are not
    # silently blocked on "please tell me your standard".
    std_unknown = cpp_standard == "unknown"
    if std_unknown:
        if build_system == "unknown":
            reason = (
                "no build system found under the project root, so no "
                "CMAKE_CXX_STANDARD / cxx_std_* / -std= flag could be read"
            )
        else:
            reason = (
                "the {bs} build files declare no CMAKE_CXX_STANDARD / "
                "cxx_std_* / -std= flag".format(bs=build_system)
            )
        lines.append(
            "- NOTE: C++ standard unknown ({reason}).".format(reason=reason)
        )
        lines.append(
            "  Re-run with an explicit standard, e.g. `--std c++17` "
            "(or c++11/14/20/23), or ask the user which standard they target "
            "before giving any modern-C++ / Boost-replacement suggestion."
        )

    return {
        "project_context": "\n".join(lines),
        "cpp_standard": cpp_standard,
        "cpp_standard_source": std_source,
        "cpp_standard_known": not std_unknown,
        "build_system": build_system,
        "libraries": libraries,
        "boost_libraries_list": sorted(set(boost_libs)),
        "project_frameworks": ", ".join(libraries) if libraries else "none detected",
        "boost_libraries": ", ".join(sorted(set(boost_libs))) if boost_libs else "none",
    }


def render(template: str, ctx: Dict[str, str]) -> str:
    out = template
    for key, value in ctx.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def emit_error(err: "ReviewError", as_json: bool, exit_code: int) -> int:
    """Render a concise error (never a raw git/help dump) and return exit_code.

    In JSON mode the error is a stable object: {ok, error:{code,message,suggestions}}.
    In text mode it is a short "Error: ..." line plus a "Next steps:" list.
    """
    if as_json:
        json.dump(
            {
                "ok": False,
                "error": {
                    "code": err.code,
                    "message": err.message,
                    "suggestions": err.suggestions,
                },
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print("Error: {msg}".format(msg=err.message), file=sys.stderr)
        for i, s in enumerate(err.suggestions, 1):
            print("  Next step {i}: {s}".format(i=i, s=s), file=sys.stderr)
    return exit_code


def main() -> int:
    args = parse_args()
    as_json = args.format == "json"
    root = repo_root(Path(args.project_root).resolve())

    using_diff = args.diff is not None or args.staged
    if not using_diff and not args.paths:
        return emit_error(
            ReviewError(
                "no_input",
                "No review target given.",
                [
                    "Pass C++ file/dir paths, e.g. `collect_target.py src/socket.cpp`.",
                    "Or use --diff [REV] / --staged to review local changes.",
                ],
            ),
            as_json,
            2,
        )

    try:
        focus = normalize_focus(args.focus)
        prompt_file = resolve_prompt_file(args.focus, args.prompt_file)
    except ReviewError as exc:
        return emit_error(exc, as_json, 2)

    scope_lines: List[str] = ["## Review Scope", ""]
    scope_summary: Dict[str, object] = {"focus": focus}
    try:
        if using_diff:
            # Precheck the git environment first so a non-repo or headless repo
            # yields a concise conclusion + alternatives, not a git help dump.
            precheck_diff_mode(root, args.staged)
            diff_text, changed_paths, label = collect_diff(root, args.diff, args.staged)
            if not diff_text.strip():
                return emit_error(
                    ReviewError(
                        "no_cpp_changes",
                        "No C++ changes found for {label}.".format(label=label),
                        [
                            "Stage or commit C++ changes, then retry.",
                            "Or review files directly: `collect_target.py path/to/file.cpp`.",
                        ],
                    ),
                    as_json,
                    1,
                )
            code = truncate(diff_text, args.max_chars)
            scope_lines += [
                "- Mode: {label} (C++ files only)".format(label=label),
                "- Changed C++ files: {n}".format(n=len(changed_paths)),
            ]
            scope_summary.update(
                {
                    "mode": "diff",
                    "label": label,
                    "changed_files": changed_paths,
                    "omitted_files": [],
                }
            )
            language = "C++ (unified diff)"
        else:
            files = gather_cpp_files(args.paths, args.include_tests)
            if not files:
                return emit_error(
                    ReviewError(
                        "no_cpp_files",
                        "No C++ files found in the provided paths.",
                        [
                            "Check the paths, or point at a directory containing C++ code.",
                            "Recognized extensions: "
                            + " ".join(sorted(CPP_EXTENSIONS)) + ".",
                        ],
                    ),
                    as_json,
                    1,
                )
            code, included, omitted = read_files_as_code(files, args.max_files, args.max_chars)
            scope_lines += [
                "- Mode: local files/directories",
                "- Files included: {n}".format(n=len(included)),
                "- Files omitted (budget): {n}".format(n=len(omitted)),
            ]
            if omitted:
                preview = ", ".join(omitted[:8]) + (", ..." if len(omitted) > 8 else "")
                scope_lines.append("- Omitted: {preview}".format(preview=preview))
            scope_summary.update(
                {
                    "mode": "files",
                    "label": "local files/directories",
                    "changed_files": included,
                    "omitted_files": omitted,
                }
            )
            language = "C++"
    except ReviewError as exc:
        return emit_error(exc, as_json, 1)

    repo_ctx = collect_repo_context(root, args.std, code)
    ctx = {
        "language": language,
        "review_focus": focus,
        "review_scope": "\n".join(scope_lines),
        "project_context": repo_ctx["project_context"],
        "cpp_standard": repo_ctx["cpp_standard"],
        "project_frameworks": repo_ctx["project_frameworks"],
        "boost_libraries": repo_ctx["boost_libraries"],
        "code": code,
    }

    if args.format == "json":
        rendered_prompt = render(prompt_file.read_text(encoding="utf-8"), ctx)
        payload = {
            "ok": True,
            "language": language,
            "focus": focus,
            "scope": scope_summary,
            "context": {
                "build_system": repo_ctx["build_system"],
                "cpp_standard": repo_ctx["cpp_standard"],
                "cpp_standard_source": repo_ctx["cpp_standard_source"],
                "cpp_standard_known": repo_ctx["cpp_standard_known"],
                "libraries": repo_ctx["libraries"],
                "boost_libraries": repo_ctx["boost_libraries_list"],
            },
            "project_context_md": repo_ctx["project_context"],
            "code": code,
            "prompt": rendered_prompt,
        }
        output = json.dumps(payload, indent=2)
    elif args.format == "code":
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
