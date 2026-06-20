#!/usr/bin/env python3
"""Plan small harness improvements for a software project."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".next",
    "coverage",
}


def walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        base = Path(dirpath)
        for filename in filenames:
            path = base / filename
            try:
                if path.stat().st_size <= 400_000:
                    files.append(path)
            except OSError:
                continue
    return files


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def exists_any(root: Path, names: list[str]) -> list[str]:
    found: list[str] = []
    for name in names:
        for path in root.glob(name):
            if path.exists():
                found.append(rel(path, root))
    return found


def detect(root: Path) -> dict[str, Any]:
    files = walk_files(root)
    rels = [rel(path, root) for path in files]
    rel_set = set(rels)

    stacks: list[str] = []
    commands: dict[str, list[str]] = {
        "setup": [],
        "lint": [],
        "typecheck": [],
        "test": [],
        "build": [],
    }

    package_paths = [path for path in files if path.name == "package.json"]
    for path in package_paths:
        data = read_json(path)
        scripts = data.get("scripts", {})
        if isinstance(scripts, dict):
            prefix = "npm run"
            if (path.parent / "pnpm-lock.yaml").exists():
                prefix = "pnpm"
            elif (path.parent / "yarn.lock").exists():
                prefix = "yarn"
            for name in scripts:
                lower = name.lower()
                command = f"cd {rel(path.parent, root)} && {prefix} {name}" if path.parent != root else f"{prefix} {name}"
                if "lint" in lower:
                    commands["lint"].append(command)
                if "typecheck" in lower or "type-check" in lower or lower == "tsc":
                    commands["typecheck"].append(command)
                if "test" in lower:
                    commands["test"].append(command)
                if "build" in lower:
                    commands["build"].append(command)
            stacks.append("node")

    if "go.mod" in rel_set:
        stacks.append("go")
        commands["test"].append("go test ./...")
        commands["build"].append("go build ./...")

    if "Cargo.toml" in rel_set:
        stacks.append("rust")
        commands["lint"].append("cargo fmt --check")
        commands["lint"].append("cargo clippy -- -D warnings")
        commands["test"].append("cargo test")
        commands["build"].append("cargo build")

    if "pyproject.toml" in rel_set or any(path.endswith("requirements.txt") for path in rels):
        stacks.append("python")
        if "pyproject.toml" in rel_set and "uv.lock" in rel_set:
            commands["test"].append("uv run pytest")
            commands["lint"].append("uv run ruff check .")
        else:
            commands["test"].append("pytest")
            commands["lint"].append("ruff check .")

    if "pom.xml" in rel_set:
        stacks.append("java-maven")
        commands["test"].append("./mvnw test" if "mvnw" in rel_set else "mvn test")
        commands["build"].append("./mvnw package" if "mvnw" in rel_set else "mvn package")

    if "build.gradle" in rel_set or "build.gradle.kts" in rel_set:
        stacks.append("java-gradle")
        commands["test"].append("./gradlew test" if "gradlew" in rel_set else "gradle test")
        commands["build"].append("./gradlew build" if "gradlew" in rel_set else "gradle build")

    signals = {
        "agent_guides": exists_any(root, [
            "AGENTS.md",
            "CLAUDE.md",
            ".cursor/rules/*",
            ".codex/commands/*",
            ".codex/skills/*",
            ".codex/agents/*",
            ".claude/commands/*",
            ".claude/skills/*",
            ".claude/agents/*",
            ".claude/CLAUDE.md",
        ]),
        "verification_entrypoint": exists_any(root, ["Makefile", "Taskfile.yml", "justfile", "package.json", "pom.xml", "build.gradle", "build.gradle.kts", "scripts/agent-check.sh", "scripts/check.sh", "ci/build.sh"]),
        "ci": exists_any(root, [".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml", "Jenkinsfile"]),
        "precommit": exists_any(root, [".pre-commit-config.yaml", "lefthook.yml", ".husky/*", "husky/*"]),
        "tests": [path for path in rels if "/test" in f"/{path}" or path.endswith(("_test.go", ".spec.ts", ".spec.tsx", ".test.ts", ".test.tsx", "Test.java"))][:20],
        "fixtures": [path for path in rels if any(part in path.lower() for part in ("fixture", "golden", "snapshot", "testdata"))][:20],
        "docs": [path for path in rels if path == "README.md" or path.startswith(("docs/", "doc/", "man/", "adr/"))][:20],
    }

    gaps = recommend(signals, commands)
    return {
        "root": str(root),
        "stacks": sorted(set(stacks)),
        "commands": {key: values for key, values in commands.items() if values},
        "signals": signals,
        "recommendations": gaps,
    }


def recommend(signals: dict[str, Any], commands: dict[str, list[str]]) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    if not signals["agent_guides"]:
        recs.append({
            "priority": "P0",
            "area": "Feedforward context",
            "action": "Create a concise AGENTS.md with project map, real commands, boundaries, safety rules, and done criteria.",
        })
    if not signals["verification_entrypoint"]:
        recs.append({
            "priority": "P0",
            "area": "Feedback and verification",
            "action": "Add a reusable verification entrypoint on an existing build surface (a `check` target in Makefile / Taskfile / justfile, an `npm run check` script, `mvn verify`, `gradle check`, or `./ci/build.sh`). Only fall back to a bespoke `scripts/agent-check.sh` if no existing build surface fits.",
        })
    if not signals["ci"]:
        recs.append({
            "priority": "P1",
            "area": "Feedback and verification",
            "action": "Add or extend CI to run the same fast verification path used locally.",
        })
    if not signals["fixtures"]:
        recs.append({
            "priority": "P1",
            "area": "Behavior correctness",
            "action": "Add one approved fixture or golden example for a critical user-visible path.",
        })
    if not signals["precommit"]:
        recs.append({
            "priority": "P2",
            "area": "Hooks",
            "action": "Add lightweight pre-commit or tool hooks only for cheap checks such as format/lint.",
        })
    if not commands.get("test"):
        recs.append({
            "priority": "P0",
            "area": "Feedback and verification",
            "action": "Identify or create a real test command; document missing tests honestly if none exist.",
        })
    return recs


def to_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# Harness Improvement Plan: {data['root']}",
        "",
        f"Detected stacks: {', '.join(data['stacks']) if data['stacks'] else 'unknown'}",
        "",
        "## Existing Signals",
        "",
        "| Signal | Evidence |",
        "| --- | --- |",
    ]
    for key, value in data["signals"].items():
        if isinstance(value, list):
            evidence = ", ".join(f"`{item}`" for item in value[:8]) if value else "none"
        else:
            evidence = str(value)
        lines.append(f"| {key} | {evidence} |")

    lines.extend(["", "## Discovered Commands", ""])
    if data["commands"]:
        for kind, commands in data["commands"].items():
            lines.append(f"### {kind}")
            lines.extend(f"- `{command}`" for command in commands)
            lines.append("")
    else:
        lines.append("No obvious verification commands found.")
        lines.append("")

    lines.extend(["## Recommended Next Moves", ""])
    for rec in data["recommendations"]:
        lines.append(f"- **{rec['priority']} {rec['area']}**: {rec['action']}")
    if not data["recommendations"]:
        lines.append("- No obvious P0/P1 gaps detected. Run a full harness audit for score-specific improvements.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan harness score improvements.")
    parser.add_argument("project_root", help="Path to the project root")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Project root is not a readable directory: {root}")

    data = detect(root)
    if args.format == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(to_markdown(data), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
