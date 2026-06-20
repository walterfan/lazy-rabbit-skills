#!/usr/bin/env python3
"""Render a GitLab Merge Request into a review-ready markdown prompt."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from gitlab_api import (
    ChangeItem,
    GitLabAPIError,
    MergeRequestInfo,
    change_items_to_markdown,
    convert_to_mr_summary,
    get_merge_request_info,
    mr_summary_to_markdown_table,
    parse_merge_request_reference,
    parse_diff_stats,
)


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROMPT_FILE = SCRIPT_DIR.parent / "assets" / "prompts" / "comprehensive-review.md"
PROMPTS_DIR = SCRIPT_DIR.parent / "assets" / "prompts"
TECH_PROMPTS_DIR = PROMPTS_DIR / "technology"

BUILTIN_PROMPT_FILES = {
    "comprehensive": PROMPTS_DIR / "comprehensive-review.md",
    "bug-detection": PROMPTS_DIR / "bug-detection-review.md",
}

TECHNOLOGY_PROMPT_FILES = {
    "Go": TECH_PROMPTS_DIR / "go.md",
    "Python": TECH_PROMPTS_DIR / "python.md",
    "Java": TECH_PROMPTS_DIR / "java.md",
    "TypeScript": TECH_PROMPTS_DIR / "typescript.md",
    "JavaScript": TECH_PROMPTS_DIR / "javascript.md",
    "Vue": TECH_PROMPTS_DIR / "vue.md",
    "React": TECH_PROMPTS_DIR / "react.md",
    "Spring Boot": TECH_PROMPTS_DIR / "spring-boot.md",
    "Gin": TECH_PROMPTS_DIR / "gin.md",
    "GORM": TECH_PROMPTS_DIR / "gorm.md",
    "MySQL": TECH_PROMPTS_DIR / "mysql.md",
    "Redis": TECH_PROMPTS_DIR / "redis.md",
    "Kafka": TECH_PROMPTS_DIR / "kafka.md",
    "Elasticsearch": TECH_PROMPTS_DIR / "elasticsearch.md",
}

TECHNOLOGY_CHANGE_HINTS = {
    "Gin": ["github.com/gin-gonic/gin", "gin.context", "gin.h", "routergroup", "ctx.shouldbind"],
    "GORM": ["gorm.io/gorm", ".where(", ".preload(", ".transaction(", ".model(", ".updates("],
    "Spring Boot": ["@springbootapplication", "@restcontroller", "@service", "@transactional"],
    "Vue": ["<template", "<script setup", "defineprops(", "defineemits(", "v-model", "ref(", "reactive("],
    "React": ["useeffect(", "usestate(", "useref(", "jsx", "tsx", "react."],
    "MySQL": ["mysql", "select ", "insert ", "update ", "delete ", "join ", "gorm.io/driver/mysql"],
    "Redis": ["redis", "ioredis", "go-redis", "spring-data-redis", "setex", "expire", "ttl"],
    "Kafka": ["kafka", "sarama", "kafkajs", "kafka-go", "confluent-kafka", "spring-kafka", "consumergroup"],
    "Elasticsearch": ["elasticsearch", "@elastic/elasticsearch", "go-elasticsearch", "_search", "_bulk", "match_query"],
}

TECHNOLOGY_PATH_HINTS = {
    "React": [".tsx", ".jsx"],
    "Vue": [".vue"],
    "Spring Boot": ["/controller/", "/service/", "/repository/", "/config/", "application.yml", "application.properties"],
    "Gin": ["/handler/", "/handlers/", "/router/", "/routes/", "/middleware/"],
    "GORM": ["/repository/", "/repositories/", "/dao/", "/model/", "/models/", "/entity/", "/entities/"],
}

LANGUAGE_TECHNOLOGIES = {
    "Go",
    "Python",
    "Java",
    "TypeScript",
    "JavaScript",
}

MANIFEST_LANGUAGE_HINTS = {
    "go.mod": "Go",
    "package.json": "JavaScript/TypeScript",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "pom.xml": "Java",
    "build.gradle": "Java",
    "build.gradle.kts": "Kotlin",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
}

FRAMEWORK_PATTERNS = {
    "go.mod": {
        "github.com/gin-gonic/gin": "Gin",
        "github.com/spf13/cobra": "Cobra CLI",
        "gorm.io/gorm": "GORM",
        "github.com/swaggo/swag": "Swagger/OpenAPI",
        "github.com/swaggo/gin-swagger": "Swagger/OpenAPI",
        "github.com/casbin/casbin": "Casbin",
        "github.com/go-sql-driver/mysql": "MySQL",
        "github.com/redis/go-redis": "Redis",
        "github.com/go-redis/redis": "Redis",
        "github.com/segmentio/kafka-go": "Kafka",
        "github.com/ibm/sarama": "Kafka",
        "github.com/confluentinc/confluent-kafka-go": "Kafka",
        "github.com/elastic/go-elasticsearch": "Elasticsearch",
    },
    "pyproject.toml": {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "pytest": "Pytest",
        "streamlit": "Streamlit",
        "redis": "Redis",
        "kafka-python": "Kafka",
        "confluent-kafka": "Kafka",
        "elasticsearch": "Elasticsearch",
        "pymysql": "MySQL",
        "mysqlclient": "MySQL",
    },
    "requirements.txt": {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "pytest": "Pytest",
        "redis": "Redis",
        "kafka-python": "Kafka",
        "confluent-kafka": "Kafka",
        "elasticsearch": "Elasticsearch",
        "pymysql": "MySQL",
        "mysqlclient": "MySQL",
    },
    "package.json": {
        "\"vue\"": "Vue",
        "\"pinia\"": "Pinia",
        "\"vite\"": "Vite",
        "\"react\"": "React",
        "\"next\"": "Next.js",
        "\"nuxt\"": "Nuxt",
        "\"express\"": "Express",
        "\"mysql2\"": "MySQL",
        "\"ioredis\"": "Redis",
        "\"redis\"": "Redis",
        "\"kafkajs\"": "Kafka",
        "\"kafka-node\"": "Kafka",
        "\"@elastic/elasticsearch\"": "Elasticsearch",
    },
    "pom.xml": {
        "spring-boot": "Spring Boot",
        "mybatis": "MyBatis",
        "junit": "JUnit",
        "spring-kafka": "Kafka",
        "spring-data-redis": "Redis",
        "mysql-connector": "MySQL",
        "elasticsearch": "Elasticsearch",
    },
    "build.gradle": {
        "spring-boot": "Spring Boot",
        "spring-kafka": "Kafka",
        "spring-data-redis": "Redis",
        "mysql-connector": "MySQL",
        "elasticsearch": "Elasticsearch",
    },
    "build.gradle.kts": {
        "spring-boot": "Spring Boot",
        "spring-kafka": "Kafka",
        "spring-data-redis": "Redis",
        "mysql-connector": "MySQL",
        "elasticsearch": "Elasticsearch",
    },
    "Cargo.toml": {
        "axum": "Axum",
        "actix-web": "Actix Web",
        "tokio": "Tokio",
    },
}

EXTENSION_TO_LANGUAGE = {
    ".go": "Go",
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".vue": "Vue",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".rs": "Rust",
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sql": "SQL",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
}

DEFAULT_MAX_FILES = 20
DEFAULT_MAX_CHANGED_LINES = 1200
DEFAULT_MAX_DIFF_CHARS = 50000
DEFAULT_LOCAL_CONTEXT_FILES = 4
DEFAULT_LOCAL_CONTEXT_CHARS = 12000
LOCAL_CONTEXT_RADIUS = 20

LOCKFILE_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.sum",
    "cargo.lock",
    "poetry.lock",
    "pipfile.lock",
}

LOW_SIGNAL_SUFFIXES = {
    ".md",
    ".rst",
    ".txt",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a GitLab Merge Request and render a markdown review prompt."
    )
    parser.add_argument(
        "mr_reference",
        nargs="?",
        help="Merge Request URL, namespace/project!iid, or plain IID when project context is available.",
    )
    parser.add_argument(
        "--local-diff",
        action="store_true",
        help="Review local tracked changes from `git diff HEAD` in --project-root before creating an MR.",
    )
    parser.add_argument(
        "--gitlab-url",
        default=os.getenv("GITLAB_URL") or os.getenv("GITLAB_BASE_URL") or "https://gitlab.example.com",
        help="GitLab base URL. Ignored when a full MR URL is provided.",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GITLAB_PROJECT") or os.getenv("GITLAB_PROJECT_ID"),
        help="Project path or ID for plain MR IIDs.",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITLAB_TOKEN") or os.getenv("GITLAB_PRIVATE_TOKEN"),
        help="GitLab private token. Prefer GITLAB_TOKEN in the environment.",
    )
    parser.add_argument(
        "--review-focus",
        default=os.getenv("MR_REVIEW_FOCUS") or "comprehensive",
        help=(
            "Built-in review focus. Supported values include "
            "comprehensive and bug-detection. Ignored when --prompt-file is provided."
        ),
    )
    parser.add_argument(
        "--project-root",
        default=os.getenv("MR_REVIEW_PROJECT_ROOT") or os.getcwd(),
        help="Project root used to collect repository context such as language, framework, and background.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=int(os.getenv("MR_REVIEW_MAX_FILES", str(DEFAULT_MAX_FILES))),
        help="Maximum number of changed files to include in the rendered review payload.",
    )
    parser.add_argument(
        "--max-changed-lines",
        type=int,
        default=int(os.getenv("MR_REVIEW_MAX_CHANGED_LINES", str(DEFAULT_MAX_CHANGED_LINES))),
        help="Maximum changed-line budget across selected files in the rendered review payload.",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=int,
        default=int(os.getenv("MR_REVIEW_MAX_DIFF_CHARS", str(DEFAULT_MAX_DIFF_CHARS))),
        help="Maximum total diff characters included in the rendered review payload.",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Include files marked as generated by GitLab in the review payload.",
    )
    parser.add_argument(
        "--skip-project-match-check",
        action="store_true",
        help="Skip local checkout versus GitLab project validation.",
    )
    parser.add_argument(
        "--prompt-file",
        default=os.getenv("MR_REVIEW_PROMPT_FILE") or str(DEFAULT_PROMPT_FILE),
        help="Markdown prompt template file.",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Override detected language. Defaults to auto.",
    )
    parser.add_argument(
        "--format",
        choices=("prompt", "bundle", "summary", "diff"),
        default="prompt",
        help="Output format. 'prompt' renders the template, other values print raw sections.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional file path for writing the result instead of stdout.",
    )
    return parser.parse_args()


def detect_language(paths: Iterable[str]) -> str:
    languages: List[str] = []
    for path in paths:
        suffix = Path(path).suffix.lower()
        language = EXTENSION_TO_LANGUAGE.get(suffix)
        if language:
            languages.append(language)

    if not languages:
        return "diff"

    counts = Counter(languages)
    ordered = [name for name, _ in counts.most_common()]
    if len(ordered) == 1:
        return ordered[0]

    return "mixed ({languages})".format(languages=", ".join(ordered[:5]))


def _sorted_unique(items: Iterable[str]) -> List[str]:
    return sorted({item for item in items if item})


def _read_text_if_exists(path: Path, max_chars: int = 20000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def run_git_command(project_root: Path, args: List[str]) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not available in the current environment") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise ValueError("git command failed: {error}".format(error=stderr)) from exc
    return result.stdout


def normalize_project_identifier(project: str) -> str:
    normalized = project.strip().strip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized


def is_numeric_project_identifier(project: str) -> bool:
    return normalize_project_identifier(project).isdigit()


def detect_repo_root(project_root: str) -> Path:
    root = Path(project_root).resolve()
    try:
        resolved = run_git_command(root, ["rev-parse", "--show-toplevel"]).strip()
        if resolved:
            return Path(resolved)
    except ValueError:
        pass
    return root


def collect_languages(project_root: Path, changed_paths: Iterable[str]) -> List[str]:
    languages: List[str] = []
    for path in changed_paths:
        suffix = Path(path).suffix.lower()
        language = EXTENSION_TO_LANGUAGE.get(suffix)
        if language:
            languages.append(language)

    for manifest_name, language in MANIFEST_LANGUAGE_HINTS.items():
        if (project_root / manifest_name).exists():
            languages.append(language)

    if (project_root / "frontend" / "package.json").exists():
        languages.append("JavaScript/TypeScript")

    return _sorted_unique(languages)


def _collect_frameworks_from_manifest(manifest_path: Path) -> List[str]:
    manifest_name = manifest_path.name
    patterns = FRAMEWORK_PATTERNS.get(manifest_name, {})
    if not patterns:
        return []

    if manifest_name == "package.json":
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            content = _read_text_if_exists(manifest_path)
        else:
            merged = {}
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                merged.update(data.get(section, {}))
            frameworks = [
                framework
                for dependency, framework in {
                    "vue": "Vue",
                    "pinia": "Pinia",
                    "vite": "Vite",
                    "react": "React",
                    "next": "Next.js",
                    "nuxt": "Nuxt",
                    "express": "Express",
                }.items()
                if dependency in merged
            ]
            return _sorted_unique(frameworks)
    else:
        content = _read_text_if_exists(manifest_path)

    lowered = content.lower()
    return _sorted_unique(
        framework for needle, framework in patterns.items() if needle.lower() in lowered
    )


def collect_frameworks(project_root: Path) -> List[str]:
    manifests = [
        project_root / "go.mod",
        project_root / "package.json",
        project_root / "pyproject.toml",
        project_root / "requirements.txt",
        project_root / "pom.xml",
        project_root / "build.gradle",
        project_root / "build.gradle.kts",
        project_root / "Cargo.toml",
        project_root / "frontend" / "package.json",
    ]
    frameworks: List[str] = []
    for manifest_path in manifests:
        frameworks.extend(_collect_frameworks_from_manifest(manifest_path))
    return _sorted_unique(frameworks)


def extract_background_knowledge(project_root: Path) -> str:
    candidates = [
        project_root / "README.md",
        project_root / "README.MD",
        project_root / "readme.md",
    ]
    for readme_path in candidates:
        content = _read_text_if_exists(readme_path, max_chars=12000)
        if not content:
            continue

        lines = [line.strip() for line in content.splitlines()]
        useful_lines: List[str] = []
        for line in lines:
            if not line:
                if useful_lines and useful_lines[-1] != "":
                    useful_lines.append("")
                continue
            if line.startswith("## ") and useful_lines:
                break
            if line.startswith("#"):
                continue
            if line.startswith("- [") or line.startswith("* ["):
                continue
            if line.startswith("!["):
                continue
            if line.startswith("```"):
                break
            useful_lines.append(line)
            if len(" ".join(useful_lines)) > 900:
                break

        background = "\n".join(useful_lines).strip()
        if background:
            return background[:900]
    return "No README-based project background was detected."


def build_project_context(
    project_root: Path,
    changed_paths: Iterable[str],
    project_label: str,
    relevant_technologies: Iterable[str],
) -> Dict[str, str]:
    languages = collect_languages(project_root, changed_paths)
    repo_stack = collect_frameworks(project_root)
    relevant_stack = [
        technology for technology in _sorted_unique(relevant_technologies) if technology not in LANGUAGE_TECHNOLOGIES
    ]
    background = extract_background_knowledge(project_root)

    context_lines = [
        "## Project Context",
        "",
        "- Project: `{project}`".format(project=project_label),
        "- Languages: {languages}".format(
            languages=", ".join(languages) if languages else "Unknown"
        ),
        "- Change-Relevant Frameworks/Stack: {frameworks}".format(
            frameworks=", ".join(relevant_stack) if relevant_stack else "No change-specific framework markers detected"
        ),
        "",
        "### Background Knowledge",
        background,
    ]

    return {
        "project_root": project_root.name,
        "project_name": project_label,
        "project_languages": ", ".join(languages) if languages else "Unknown",
        "project_frameworks": ", ".join(relevant_stack)
        if relevant_stack
        else "No change-specific framework markers detected",
        "project_stack": ", ".join(repo_stack) if repo_stack else "No repo-wide framework markers detected",
        "project_background": background,
        "project_context": "\n".join(context_lines).strip(),
    }


def _safe_repo_relative_path(repo_root: Path, relative_path: str) -> Optional[Path]:
    if not relative_path:
        return None
    candidate = (repo_root / relative_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return candidate


def _path_fence_language(path: str) -> str:
    suffix = Path(path).suffix.lower()
    language_map = {
        ".go": "go",
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".vue": "vue",
        ".sql": "sql",
        ".sh": "bash",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
    }
    return language_map.get(suffix, "text")


def _parse_new_hunk_ranges(diff: str) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []
    pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for line in diff.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        if count <= 0:
            continue
        ranges.append((start, start + count - 1))
    return ranges


def _merge_line_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def build_local_code_context(
    repo_root: Path,
    changes: Iterable[ChangeItem],
    project_label: str,
    max_files: int = DEFAULT_LOCAL_CONTEXT_FILES,
    max_chars: int = DEFAULT_LOCAL_CONTEXT_CHARS,
) -> Dict[str, str]:
    sections: List[str] = []
    used_files = 0
    consumed_chars = 0

    intro = [
        "## Local Code Context",
        "",
        (
            "The review target matches the local checkout for `{project}`. "
            "Use the following nearby file context to understand surrounding code that may not "
            "appear in the diff payload."
        ).format(project=project_label),
        "",
    ]

    for change in changes:
        if used_files >= max_files or consumed_chars >= max_chars:
            break

        relative_path = change.new_path or change.old_path
        file_path = _safe_repo_relative_path(repo_root, relative_path)
        if not file_path or not file_path.exists() or not file_path.is_file():
            continue
        if is_low_signal_path(relative_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not content.strip():
            continue

        lines = content.splitlines()
        if not lines:
            continue

        hunk_ranges = _parse_new_hunk_ranges(change.diff)
        if hunk_ranges:
            expanded = [
                (max(1, start - LOCAL_CONTEXT_RADIUS), min(len(lines), end + LOCAL_CONTEXT_RADIUS))
                for start, end in hunk_ranges
            ]
            selected_ranges = _merge_line_ranges(expanded)
        else:
            selected_ranges = [(1, min(len(lines), LOCAL_CONTEXT_RADIUS * 2))]

        snippets: List[str] = []
        for start, end in selected_ranges:
            excerpt = "\n".join(lines[start - 1 : end]).rstrip()
            if not excerpt:
                continue
            snippet = "\n".join(
                [
                    "Context from lines {start}-{end}:".format(start=start, end=end),
                    "```{language}".format(language=_path_fence_language(relative_path)),
                    excerpt,
                    "```",
                ]
            )
            projected = consumed_chars + len(snippet)
            if projected > max_chars and snippets:
                break
            if projected > max_chars:
                remaining = max_chars - consumed_chars
                if remaining < 200:
                    break
                truncated_excerpt = excerpt[: max(remaining - 80, 0)].rstrip()
                if not truncated_excerpt:
                    break
                snippet = "\n".join(
                    [
                        "Context from lines {start}-{end} (truncated):".format(start=start, end=end),
                        "```{language}".format(language=_path_fence_language(relative_path)),
                        truncated_excerpt,
                        "```",
                    ]
                )
            snippets.append(snippet)
            consumed_chars += len(snippet)
            if consumed_chars >= max_chars:
                break

        if not snippets:
            continue

        sections.extend(
            [
                "### `{path}`".format(path=relative_path),
                "",
                *snippets,
                "",
            ]
        )
        used_files += 1

    if not sections:
        return {
            "local_code_context": "",
            "local_code_context_status": "No additional local code context was collected.",
        }

    return {
        "local_code_context": "\n".join(intro + sections).strip(),
        "local_code_context_status": "Included nearby local code context from the current checkout.",
    }


def _change_mentions_technology(change: ChangeItem, technology: str) -> bool:
    keywords = TECHNOLOGY_CHANGE_HINTS.get(technology, [])
    haystacks = [
        (change.new_path or "").lower(),
        (change.old_path or "").lower(),
        change.diff.lower(),
    ]
    return any(keyword.lower() in haystack for keyword in keywords for haystack in haystacks)


def _change_path_matches_technology(change: ChangeItem, technology: str) -> bool:
    hints = TECHNOLOGY_PATH_HINTS.get(technology, [])
    paths = [
        (change.new_path or "").lower(),
        (change.old_path or "").lower(),
    ]
    return any(hint.lower() in path for hint in hints for path in paths)


def detect_technologies(project_root: Path, changes: Iterable[ChangeItem]) -> List[str]:
    detected: List[str] = []

    suffix_to_technology = {
        ".go": "Go",
        ".py": "Python",
        ".java": "Java",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".vue": "Vue",
    }
    materialized_changes = list(changes)
    changed_languages: List[str] = []
    for change in materialized_changes:
        path = change.new_path or change.old_path
        technology = suffix_to_technology.get(Path(path).suffix.lower())
        if technology:
            detected.append(technology)
            changed_languages.append(technology)

    for technology in TECHNOLOGY_PROMPT_FILES:
        if technology in detected:
            continue
        if any(_change_mentions_technology(change, technology) for change in materialized_changes):
            detected.append(technology)

    repo_stack = collect_frameworks(project_root)
    for framework in ("React", "Vue"):
        if any(_change_path_matches_technology(change, framework) for change in materialized_changes):
            detected.append(framework)

    if "Java" in changed_languages and "Spring Boot" in repo_stack:
        if any(_change_path_matches_technology(change, "Spring Boot") for change in materialized_changes):
            detected.append("Spring Boot")
    if "Go" in changed_languages:
        for framework in ("Gin", "GORM"):
            if framework in repo_stack and any(
                _change_path_matches_technology(change, framework) for change in materialized_changes
            ):
                detected.append(framework)
    if any(language in changed_languages for language in ("TypeScript", "JavaScript")):
        for framework in ("React", "Vue"):
            if framework in repo_stack and any(
                _change_path_matches_technology(change, framework) for change in materialized_changes
            ):
                detected.append(framework)

    return _sorted_unique(detected)


def build_technology_focus(project_root: Path, changes: Iterable[ChangeItem]) -> Dict[str, str]:
    technologies = detect_technologies(project_root, changes)
    sections: List[str] = []
    loaded: List[str] = []

    for technology in technologies:
        prompt_path = TECHNOLOGY_PROMPT_FILES.get(technology)
        if not prompt_path:
            continue
        content = _read_text_if_exists(prompt_path, max_chars=4000).strip()
        if not content:
            continue
        loaded.append(technology)
        sections.append("### {technology}\n{content}".format(technology=technology, content=content))

    technology_focus = ""
    if sections:
        technology_focus = "## Technology-Specific Review Focus\n\n" + "\n\n".join(sections)

    return {
        "detected_technologies": ", ".join(loaded) if loaded else "None",
        "technology_focus": technology_focus,
    }


def load_prompt_template(prompt_file: str) -> str:
    return Path(prompt_file).read_text(encoding="utf-8")


def normalize_review_focus(review_focus: str) -> str:
    normalized = review_focus.strip().lower()
    aliases = {
        "default": "comprehensive",
        "full": "comprehensive",
        "general": "comprehensive",
        "overall": "comprehensive",
        "bugs": "bug-detection",
        "bug": "bug-detection",
        "bug_detection": "bug-detection",
        "bug detection": "bug-detection",
        "bug-focused": "bug-detection",
        "bug focused": "bug-detection",
        "defect": "bug-detection",
        "defects": "bug-detection",
    }
    return aliases.get(normalized, normalized)


def resolve_prompt_file(review_focus: str, explicit_prompt_file: Optional[str]) -> str:
    if explicit_prompt_file and explicit_prompt_file != str(DEFAULT_PROMPT_FILE):
        return explicit_prompt_file

    normalized_focus = normalize_review_focus(review_focus)
    prompt_file = BUILTIN_PROMPT_FILES.get(normalized_focus)
    if prompt_file:
        return str(prompt_file)

    available = ", ".join(sorted(BUILTIN_PROMPT_FILES))
    raise ValueError(
        "unsupported review focus '{focus}'. Supported built-in focuses: {available}".format(
            focus=review_focus,
            available=available,
        )
    )


def render_template(template: str, context: Dict[str, str]) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def render_review_prompt(template: str, context: Dict[str, str]) -> str:
    rendered = render_template(template, context)
    technology_focus = context.get("technology_focus", "").strip()
    if technology_focus and "{{technology_focus}}" not in template:
        return rendered.rstrip() + "\n\n" + technology_focus + "\n"
    return rendered


def parse_project_from_remote_url(remote_url: str) -> Optional[str]:
    patterns = [
        r"^[^@]+@[^:]+:(?P<project>.+?)(?:\.git)?$",
        r"^(?:ssh|https?)://[^/]+/(?P<project>.+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, remote_url.strip())
        if match:
            project = match.group("project").strip("/")
            if project:
                return project
    return None


def detect_project_from_git_remote(project_root: Path) -> Optional[str]:
    try:
        output = run_git_command(project_root, ["remote", "-v"])
    except ValueError:
        return None

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    preferred_lines = [
        line for line in lines if line.startswith("origin\t") and line.endswith("(fetch)")
    ]
    for line in preferred_lines + lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        project = parse_project_from_remote_url(parts[1])
        if project:
            return project
    return None


def validate_project_match(
    repo_root: Path,
    resolved_project: str,
    skip_project_match_check: bool,
) -> None:
    if skip_project_match_check or is_numeric_project_identifier(resolved_project):
        return

    detected_project = detect_project_from_git_remote(repo_root)
    if not detected_project:
        return

    detected = normalize_project_identifier(detected_project)
    expected = normalize_project_identifier(resolved_project)
    if detected == expected:
        return

    raise ValueError(
        "local project mismatch: --project-root points to '{detected}', but the MR belongs to "
        "'{expected}'. Pass the correct --project-root or use --skip-project-match-check if you "
        "intentionally want to reuse another checkout for context.".format(
            detected=detected,
            expected=expected,
        )
    )


def can_use_local_checkout_context(repo_root: Path, resolved_project: str) -> bool:
    if is_numeric_project_identifier(resolved_project):
        return False
    detected_project = detect_project_from_git_remote(repo_root)
    if not detected_project:
        return False
    return normalize_project_identifier(detected_project) == normalize_project_identifier(
        resolved_project
    )


def parse_name_status_output(output: str) -> Dict[str, Dict[str, object]]:
    statuses: Dict[str, Dict[str, object]] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status_code = parts[0]
        kind = status_code[:1]

        if kind == "R" and len(parts) >= 3:
            old_path, new_path = parts[1], parts[2]
            statuses[new_path] = {
                "old_path": old_path,
                "new_path": new_path,
                "new_file": False,
                "deleted_file": False,
                "renamed_file": True,
            }
        elif kind == "A":
            path = parts[1]
            statuses[path] = {
                "old_path": path,
                "new_path": path,
                "new_file": True,
                "deleted_file": False,
                "renamed_file": False,
            }
        elif kind == "D":
            path = parts[1]
            statuses[path] = {
                "old_path": path,
                "new_path": path,
                "new_file": False,
                "deleted_file": True,
                "renamed_file": False,
            }
        else:
            path = parts[1]
            statuses[path] = {
                "old_path": path,
                "new_path": path,
                "new_file": False,
                "deleted_file": False,
                "renamed_file": False,
            }
    return statuses


def parse_unified_diff_blocks(diff_text: str) -> List[Dict[str, str]]:
    blocks: List[Dict[str, str]] = []
    current: List[str] = []
    old_path = ""
    new_path = ""

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current:
                blocks.append(
                    {
                        "old_path": old_path,
                        "new_path": new_path,
                        "diff": "\n".join(current).strip(),
                    }
                )
            current = [line]
            match = re.match(r"diff --git a/(.+) b/(.+)", line)
            if match:
                old_path, new_path = match.group(1), match.group(2)
            else:
                old_path, new_path = "", ""
            continue
        if current:
            current.append(line)

    if current:
        blocks.append(
            {
                "old_path": old_path,
                "new_path": new_path,
                "diff": "\n".join(current).strip(),
            }
        )

    return blocks


def get_local_change_info(project_root: Path) -> MergeRequestInfo:
    try:
        diff_text = run_git_command(project_root, ["diff", "--find-renames", "HEAD", "--"])
        name_status = run_git_command(project_root, ["diff", "--find-renames", "--name-status", "HEAD", "--"])
    except ValueError as exc:
        message = str(exc).lower()
        if "bad revision 'head'" in message or "ambiguous argument 'head'" in message:
            raise ValueError(
                "the target repository does not have a valid HEAD commit yet. "
                "Create the first commit before using `--local-diff`, or compare changes manually."
            ) from exc
        raise
    statuses = parse_name_status_output(name_status)
    blocks = parse_unified_diff_blocks(diff_text)

    changes: List[ChangeItem] = []
    for block in blocks:
        key = block["new_path"] or block["old_path"]
        status = statuses.get(key, {})
        changes.append(
            ChangeItem(
                diff=block["diff"],
                new_path=str(status.get("new_path") or block["new_path"]),
                old_path=str(status.get("old_path") or block["old_path"]),
                new_file=bool(status.get("new_file", False)),
                deleted_file=bool(status.get("deleted_file", False)),
                renamed_file=bool(status.get("renamed_file", False)),
            )
        )

    return MergeRequestInfo(
        title="Local Changes vs HEAD",
        description=(
            "Tracked staged and unstaged changes from `git diff HEAD` in the target repository. "
            "Untracked files are not included."
        ),
        changes=changes,
    )


def resolve_project(
    mr_reference: str,
    explicit_project: Optional[str],
    project_root: Path,
) -> Optional[str]:
    if explicit_project:
        return explicit_project
    if mr_reference.strip().isdigit():
        return detect_project_from_git_remote(project_root)
    return explicit_project


def looks_like_source_file(path: str) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in EXTENSION_TO_LANGUAGE and suffix not in {".md", ".json", ".yaml", ".yml"}


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    return (
        "/test" in lowered
        or "/tests" in lowered
        or lowered.endswith("_test.go")
        or lowered.endswith(".spec.ts")
        or lowered.endswith(".spec.tsx")
        or lowered.endswith(".test.ts")
        or lowered.endswith(".test.tsx")
        or lowered.endswith(".test.js")
        or lowered.endswith(".spec.js")
        or lowered.startswith("tests/")
    )


def is_low_signal_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    suffix = Path(normalized).suffix.lower()
    name = Path(normalized).name.lower()
    if name in LOCKFILE_NAMES:
        return True
    if suffix in LOW_SIGNAL_SUFFIXES:
        return True
    lowered = normalized.lower()
    return any(
        marker in lowered
        for marker in (
            "/dist/",
            "/build/",
            "/coverage/",
            "/node_modules/",
            "/vendor/",
            "/docs/",
            "/doc/",
        )
    )


def score_change_for_review(change: ChangeItem) -> int:
    path = change.new_path or change.old_path
    stats = parse_diff_stats(change.diff)
    score = 0

    if looks_like_source_file(path):
        score += 120
    elif is_test_path(path):
        score += 80
    elif not is_low_signal_path(path):
        score += 60
    else:
        score += 15

    if change.new_file or change.deleted_file or change.renamed_file:
        score += 10
    if is_test_path(path):
        score -= 15

    score += min(stats.changed_lines, 150)
    return score


def truncate_diff(diff: str, max_chars: int) -> str:
    if max_chars <= 0 or len(diff) <= max_chars:
        return diff
    truncated = diff[:max_chars].rstrip()
    return (
        truncated
        + "\n\n... diff truncated to fit review budget. Inspect the original MR for full context."
    )


def build_review_subset(
    mr_info: MergeRequestInfo,
    max_files: int,
    max_changed_lines: int,
    max_diff_chars: int,
    include_generated: bool,
) -> Dict[str, object]:
    candidates: List[Dict[str, object]] = []
    skipped_generated = 0

    for change in mr_info.changes:
        if change.generated_file and not include_generated:
            skipped_generated += 1
            continue
        stats = parse_diff_stats(change.diff)
        path = change.new_path or change.old_path
        candidates.append(
            {
                "change": change,
                "path": path,
                "stats": stats,
                "score": score_change_for_review(change),
                "low_signal": is_low_signal_path(path),
            }
        )

    ordered = sorted(
        candidates,
        key=lambda item: (
            item["low_signal"],
            -int(item["score"]),
            -int(item["stats"].changed_lines),
            str(item["path"]),
        ),
    )

    selected_changes: List[ChangeItem] = []
    selected_changed_lines = 0
    selected_diff_chars = 0
    omitted_paths: List[str] = []

    for item in ordered:
        if max_files > 0 and len(selected_changes) >= max_files:
            omitted_paths.append(str(item["path"]))
            continue

        change = item["change"]
        stats = item["stats"]
        remaining_chars = max_diff_chars - selected_diff_chars if max_diff_chars > 0 else len(change.diff)
        if max_diff_chars > 0 and remaining_chars <= 0:
            omitted_paths.append(str(item["path"]))
            continue

        if selected_changes and max_changed_lines > 0 and (
            selected_changed_lines + stats.changed_lines > max_changed_lines
        ):
            omitted_paths.append(str(item["path"]))
            continue

        truncated_diff = truncate_diff(change.diff, remaining_chars)
        selected_changes.append(
            ChangeItem(
                diff=truncated_diff,
                new_path=change.new_path,
                old_path=change.old_path,
                a_mode=change.a_mode,
                b_mode=change.b_mode,
                new_file=change.new_file,
                renamed_file=change.renamed_file,
                deleted_file=change.deleted_file,
                generated_file=change.generated_file,
            )
        )
        selected_changed_lines += stats.changed_lines
        selected_diff_chars += len(truncated_diff)

    if not selected_changes and ordered:
        first = ordered[0]["change"]
        selected_changes.append(
            ChangeItem(
                diff=truncate_diff(first.diff, max_diff_chars),
                new_path=first.new_path,
                old_path=first.old_path,
                a_mode=first.a_mode,
                b_mode=first.b_mode,
                new_file=first.new_file,
                renamed_file=first.renamed_file,
                deleted_file=first.deleted_file,
                generated_file=first.generated_file,
            )
        )
        selected_changed_lines = parse_diff_stats(first.diff).changed_lines
        selected_diff_chars = len(selected_changes[0].diff)

    selected_info = MergeRequestInfo(
        title=mr_info.title,
        description=mr_info.description,
        changes=selected_changes,
    )

    scope_lines = [
        "## Review Scope",
        "",
        "- Total changed files in MR: {total}".format(total=len(mr_info.changes)),
        "- Files included in prompt: {count}".format(count=len(selected_changes)),
        "- Files omitted from prompt: {count}".format(
            count=max(len(mr_info.changes) - len(selected_changes), 0)
        ),
        "- Generated files skipped: {count}".format(count=skipped_generated),
        "- Selected changed-line budget used: {value}".format(value=selected_changed_lines),
        "- Selected diff characters used: {value}".format(value=selected_diff_chars),
    ]

    if omitted_paths:
        preview = ", ".join(omitted_paths[:8])
        if len(omitted_paths) > 8:
            preview += ", ..."
        scope_lines.extend(
            [
                "",
                "Omitted files include: {preview}".format(preview=preview),
            ]
        )

    return {
        "selected_info": selected_info,
        "review_scope": "\n".join(scope_lines).strip(),
    }


def build_sections(
    mr_reference: str,
    gitlab_url: str,
    project: Optional[str],
    token: str,
    project_root: str,
    max_files: int,
    max_changed_lines: int,
    max_diff_chars: int,
    include_generated: bool,
    skip_project_match_check: bool,
) -> Dict[str, str]:
    repo_root = detect_repo_root(project_root)
    resolved_project_hint = resolve_project(mr_reference, project, repo_root)
    resolved_url, resolved_project, mr_iid = parse_merge_request_reference(
        mr_reference,
        gitlab_url=gitlab_url,
        default_project=resolved_project_hint,
    )
    validate_project_match(repo_root, resolved_project, skip_project_match_check)
    mr_info = get_merge_request_info(resolved_url, resolved_project, mr_iid, token)
    review_subset = build_review_subset(
        mr_info,
        max_files=max_files,
        max_changed_lines=max_changed_lines,
        max_diff_chars=max_diff_chars,
        include_generated=include_generated,
    )
    selected_info = review_subset["selected_info"]
    mr_summary = mr_summary_to_markdown_table(convert_to_mr_summary(selected_info))
    mr_diff = change_items_to_markdown(selected_info)
    changed_paths = [change.new_path or change.old_path for change in selected_info.changes]
    technology_focus = build_technology_focus(repo_root, selected_info.changes)
    project_context = build_project_context(
        repo_root,
        changed_paths,
        resolved_project,
        technology_focus["detected_technologies"].split(", ") if technology_focus["detected_technologies"] != "None" else [],
    )
    local_code_context = (
        build_local_code_context(repo_root, selected_info.changes, resolved_project)
        if can_use_local_checkout_context(repo_root, resolved_project)
        else {
            "local_code_context": "",
            "local_code_context_status": "No matching local checkout was confirmed for this MR.",
        }
    )
    language = detect_language(changed_paths)
    code_parts = [
        review_subset["review_scope"],
        "",
        mr_summary,
        "",
        mr_diff,
    ]
    bundle_parts = [
        project_context["project_context"],
        "",
        local_code_context["local_code_context"],
        "",
        review_subset["review_scope"],
        "",
        mr_summary,
        "",
        mr_diff,
    ]
    sections = {
        "gitlab_url": resolved_url,
        "project": resolved_project,
        "merge_request_iid": mr_iid,
        "review_focus": "",
        "mr_title": mr_info.title,
        "mr_description": mr_info.description or "",
        "review_scope": review_subset["review_scope"],
        "mr_summary": mr_summary,
        "mr_diff": mr_diff,
        "language": language,
        "code": "\n".join(code_parts).strip(),
        "bundle": "\n".join(bundle_parts).strip(),
    }
    sections.update(project_context)
    sections.update(technology_focus)
    sections.update(local_code_context)
    return sections


def build_local_sections(
    project_root: str,
    max_files: int,
    max_changed_lines: int,
    max_diff_chars: int,
    include_generated: bool,
) -> Dict[str, str]:
    repo_root = detect_repo_root(project_root)
    detected_project = detect_project_from_git_remote(repo_root) or repo_root.name
    local_info = get_local_change_info(repo_root)
    if not local_info.changes:
        raise ValueError(
            "no tracked local changes found in the target repository. `--local-diff` reviews "
            "`git diff HEAD`, so untracked files are not included."
        )
    review_subset = build_review_subset(
        local_info,
        max_files=max_files,
        max_changed_lines=max_changed_lines,
        max_diff_chars=max_diff_chars,
        include_generated=include_generated,
    )
    selected_info = review_subset["selected_info"]
    mr_summary = mr_summary_to_markdown_table(convert_to_mr_summary(selected_info))
    mr_diff = change_items_to_markdown(selected_info)
    changed_paths = [change.new_path or change.old_path for change in selected_info.changes]
    technology_focus = build_technology_focus(repo_root, selected_info.changes)
    project_context = build_project_context(
        repo_root,
        changed_paths,
        detected_project,
        technology_focus["detected_technologies"].split(", ") if technology_focus["detected_technologies"] != "None" else [],
    )
    local_code_context = build_local_code_context(repo_root, selected_info.changes, detected_project)
    language = detect_language(changed_paths)
    code_parts = [
        review_subset["review_scope"],
        "",
        mr_summary,
        "",
        mr_diff,
    ]
    bundle_parts = [
        project_context["project_context"],
        "",
        local_code_context["local_code_context"],
        "",
        review_subset["review_scope"],
        "",
        mr_summary,
        "",
        mr_diff,
    ]
    sections = {
        "gitlab_url": "",
        "project": detected_project,
        "merge_request_iid": "",
        "review_focus": "",
        "mr_title": local_info.title,
        "mr_description": local_info.description,
        "review_scope": review_subset["review_scope"],
        "mr_summary": mr_summary,
        "mr_diff": mr_diff,
        "language": language,
        "code": "\n".join(code_parts).strip(),
        "bundle": "\n".join(bundle_parts).strip(),
    }
    sections.update(project_context)
    sections.update(technology_focus)
    sections.update(local_code_context)
    return sections


def write_output(content: str, output_file: str) -> None:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()

    if not args.local_diff and not args.mr_reference:
        print(
            "Provide a Merge Request reference or pass --local-diff to review local changes.",
            file=sys.stderr,
        )
        return 2

    if not args.local_diff and not args.token:
        print(
            "Missing GitLab token. Set GITLAB_TOKEN or pass --token. "
            "See skills/gitlab-mr-review/references/token-setup.md for setup steps.",
            file=sys.stderr,
        )
        return 2

    try:
        if args.local_diff:
            sections = build_local_sections(
                args.project_root,
                args.max_files,
                args.max_changed_lines,
                args.max_diff_chars,
                args.include_generated,
            )
        else:
            sections = build_sections(
                args.mr_reference or "",
                args.gitlab_url,
                args.project,
                args.token,
                args.project_root,
                args.max_files,
                args.max_changed_lines,
                args.max_diff_chars,
                args.include_generated,
                args.skip_project_match_check,
            )
        prompt_file = resolve_prompt_file(args.review_focus, args.prompt_file)
    except (GitLabAPIError, OSError, ValueError) as exc:
        print("Failed to build MR review prompt: {error}".format(error=exc), file=sys.stderr)
        return 1
    if args.language != "auto":
        sections["language"] = args.language
    sections["review_focus"] = normalize_review_focus(args.review_focus)

    if args.format == "prompt":
        template = load_prompt_template(prompt_file)
        output = render_review_prompt(template, sections)
    elif args.format == "bundle":
        output = sections["bundle"]
    elif args.format == "summary":
        output = sections["mr_summary"]
    else:
        output = sections["mr_diff"]

    if args.output_file:
        write_output(output, args.output_file)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
