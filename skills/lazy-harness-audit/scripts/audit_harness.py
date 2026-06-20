#!/usr/bin/env python3
"""Collect deterministic evidence for an AI coding-agent harness audit."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    "coverage",
}

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".vue",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".gradle",
    ".xml",
}


PATTERNS: dict[str, list[str]] = {
    "agent_guides": [
        r"(^|/)AGENTS(\.md)?$",
        r"(^|/)CLAUDE(\.md)?$",
        r"(^|/)GEMINI(\.md)?$",
        r"(^|/)\.cursor/rules/",
        r"(^|/)\.codex/(commands|skills|agents)/",
        r"(^|/)\.claude/(commands|skills|agents)/",
        r"(^|/)\.claude/CLAUDE\.md$",
    ],
    "knowledge_docs": [
        r"(^|/)README\.md$",
        r"(^|/)docs?(/|$)",
        r"(^|/)man(/|$)",
        r"(^|/)adr(/|$)",
        r"(^|/)architecture(/|$)",
    ],
    "ci": [
        r"(^|/)\.github/workflows/.+\.(ya?ml)$",
        r"(^|/)\.gitlab-ci\.ya?ml$",
        r"(^|/)Jenkinsfile$",
        r"(^|/)azure-pipelines\.ya?ml$",
        r"(^|/)circle\.yml$",
    ],
    "hooks": [
        r"(^|/)\.pre-commit-config\.ya?ml$",
        r"(^|/)lefthook\.ya?ml$",
        r"(^|/)husky(/|$)",
        r"(^|/)\.husky(/|$)",
        r"(^|/)\.claude/settings\.json$",
        r"(^|/)\.codex(/|$)",
    ],
    "verification_entrypoints": [
        r"(^|/)scripts/(agent-)?check\.(sh|py|js|ts)$",
        r"(^|/)scripts/.+verify.+\.(sh|py|js|ts)$",
        r"(^|/)Makefile$",
        r"(^|/)Taskfile\.ya?ml$",
        r"(^|/)justfile$",
    ],
    "tests": [
        r"(^|/)tests?(/|$)",
        r"(^|/)__tests__(/|$)",
        r"(^|/)src/test(/|$)",
        r"(^|/)test_.+\.py$",
        r".+(_test\.go|Test\.java|\.spec\.(ts|tsx|js|jsx)|\.test\.(ts|tsx|js|jsx))$",
    ],
    "fixtures": [
        r"(^|/)fixtures?(/|$)",
        r"(^|/)golden(/|$)",
        r"(^|/)snapshots?(/|$)",
        r"(^|/)testdata(/|$)",
        r"(^|/)examples?(/|$)",
    ],
    "arch_fitness": [
        r"ArchUnit",
        r"dependency-cruiser",
        r"import-linter",
        r"layeredArchitecture",
        r"no-restricted-imports",
        r"module-boundar(y|ies)",
        r"forbidden.*import",
    ],
    "security": [
        r"secret",
        r"gitleaks",
        r"trufflehog",
        r"semgrep",
        r"spotbugs",
        r"bandit",
        r"npm audit",
        r"cargo audit",
        r"pip-audit",
        r"Dependabot",
        r"Renovate",
        r"PII",
        r"token",
    ],
    "sandbox": [
        r"(^|/)\.devcontainer(/|$)",
        r"(^|/)devcontainer\.json$",
        r"(^|/)Dockerfile$",
        r"(^|/)docker-compose\.ya?ml$",
        r"(^|/)compose\.ya?ml$",
    ],
    "entropy": [
        r"freshness",
        r"staleness",
        r"doc-sync",
        r"dependabot",
        r"renovate",
        r"scheduled",
        r"cron",
        r"harness",
        r"cost",
        r"flaky",
    ],
}

COMMAND_HINTS = {
    "test": [r"\btest\b", r"pytest", r"go test", r"cargo test", r"mvn test", r"gradle test"],
    "lint": [r"\blint\b", r"ruff check", r"eslint", r"checkstyle", r"clippy", r"golangci-lint"],
    "typecheck": [r"typecheck", r"tsc", r"mypy", r"pyright", r"vue-tsc"],
    "build": [r"\bbuild\b", r"mvn package", r"gradle build", r"go build", r"cargo build"],
    "format": [r"\bformat\b", r"\bfmt\b", r"prettier", r"gofmt", r"rustfmt", r"ruff format"],
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            path = base / name
            try:
                if path.stat().st_size <= 500_000:
                    paths.append(path)
            except OSError:
                continue
    return paths


def read_text(path: Path) -> str:
    if path.suffix not in TEXT_SUFFIXES and path.name not in {"Makefile", "justfile", "Jenkinsfile"}:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def add_match(matches: dict[str, list[str]], key: str, value: str, limit: int = 25) -> None:
    bucket = matches.setdefault(key, [])
    if value not in bucket and len(bucket) < limit:
        bucket.append(value)


def collect(root: Path) -> dict[str, Any]:
    paths = iter_paths(root)
    rel_paths = [rel(path, root) for path in paths]
    matches: dict[str, list[str]] = {key: [] for key in PATTERNS}
    command_hits: dict[str, list[str]] = {key: [] for key in COMMAND_HINTS}
    package_scripts: dict[str, Any] = {}

    for path, rel_path in zip(paths, rel_paths):
        normalized = rel_path
        for key, patterns in PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized, re.IGNORECASE):
                    add_match(matches, key, normalized)

        text = read_text(path)
        if not text:
            continue

        for key in ("arch_fitness", "security", "entropy"):
            for pattern in PATTERNS[key]:
                if re.search(pattern, text, re.IGNORECASE):
                    add_match(matches, key, normalized)
                    break

        for command, patterns in COMMAND_HINTS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    add_match(command_hits, command, normalized)
                    break

        if path.name == "package.json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {}
            scripts = data.get("scripts")
            if isinstance(scripts, dict):
                package_scripts[normalized] = {
                    name: value for name, value in scripts.items() if isinstance(value, str)
                }

    markers = {
        "package_json": [p for p in rel_paths if p.endswith("package.json")][:10],
        "pyproject": [p for p in rel_paths if p.endswith("pyproject.toml")][:10],
        "go_mod": [p for p in rel_paths if p.endswith("go.mod")][:10],
        "cargo": [p for p in rel_paths if p.endswith("Cargo.toml")][:10],
        "maven": [p for p in rel_paths if p.endswith("pom.xml")][:10],
        "gradle": [p for p in rel_paths if p.endswith("build.gradle") or p.endswith("build.gradle.kts")][:10],
    }

    return {
        "root": str(root),
        "file_count_scanned": len(paths),
        "matches": matches,
        "command_hits": command_hits,
        "package_scripts": package_scripts,
        "project_markers": markers,
        "heuristic_summary": summarize(matches, command_hits),
    }


def summarize(matches: dict[str, list[str]], command_hits: dict[str, list[str]]) -> dict[str, str]:
    def yes(items: list[str]) -> bool:
        return bool(items)

    return {
        "feedforward": "present" if yes(matches["agent_guides"]) else "missing",
        "knowledge_docs": "present" if yes(matches["knowledge_docs"]) else "missing",
        "verification_commands": "present" if any(command_hits.values()) else "missing",
        "verification_entrypoint": "present" if yes(matches["verification_entrypoints"]) else "missing",
        "ci": "present" if yes(matches["ci"]) else "missing",
        "hooks": "present" if yes(matches["hooks"]) else "missing",
        "architecture_fitness": "present" if yes(matches["arch_fitness"]) else "missing",
        "behavior_fixtures": "present" if yes(matches["fixtures"]) else "missing",
        "tests": "present" if yes(matches["tests"]) else "missing",
        "security": "present" if yes(matches["security"]) else "missing",
        "sandbox": "present" if yes(matches["sandbox"]) else "missing",
        "entropy_management": "present" if yes(matches["entropy"]) else "missing",
    }


def to_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# Harness Evidence Scan: {data['root']}",
        "",
        f"Files scanned: {data['file_count_scanned']}",
        "",
        "## Heuristic Summary",
        "",
        "| Signal | Status |",
        "| --- | --- |",
    ]
    for key, value in data["heuristic_summary"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Evidence Matches", ""])
    for key, values in data["matches"].items():
        lines.append(f"### {key}")
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- none found")
        lines.append("")

    lines.extend(["## Command Hints", ""])
    for key, values in data["command_hits"].items():
        lines.append(f"### {key}")
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- none found")
        lines.append("")

    if data["package_scripts"]:
        lines.extend(["## package.json Scripts", ""])
        for path, scripts in data["package_scripts"].items():
            lines.append(f"### {path}")
            for name, value in scripts.items():
                lines.append(f"- `{name}`: `{value}`")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect harness audit evidence.")
    parser.add_argument("project_root", help="Path to the project root to scan")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Project root is not a readable directory: {root}")

    data = collect(root)
    if args.format == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(to_markdown(data), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
