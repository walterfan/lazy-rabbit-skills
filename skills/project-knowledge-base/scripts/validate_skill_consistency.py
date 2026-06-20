#!/usr/bin/env python3
"""
Cross-check SKILL.md declarations against the actual file system.

Catches:
  1. Scripts listed in the toolkit table that don't exist on disk
  2. Additional Resources links pointing to missing files
  3. Scripts on disk not listed in the init_pkb.sh copy loop
  4. Commands in SKILL.md missing from commands.md, and vice versa
  5. Template docs listed in init_pkb.sh that don't exist in templates/docs/
  6. Poetry scaffold files and Makefiles are aligned with the Poetry-first workflow
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from typing import List

SKILL_MD = "SKILL.md"
COMMANDS_MD = os.path.join("references", "commands.md")
INIT_SCRIPT = os.path.join("scripts", "init_pkb.sh")
ROOT_MAKEFILE = "Makefile"
ROOT_PYPROJECT = "pyproject.toml"
TEMPLATE_SPHINX_MAKEFILE = os.path.join("templates", "sphinx", "Makefile")
TEMPLATE_SPHINX_PYPROJECT = os.path.join("templates", "sphinx", "pyproject.toml")
TEMPLATE_SPHINX_CONF = os.path.join("templates", "sphinx", "conf.py")
TEMPLATE_SPHINX_LAYOUT = os.path.join("templates", "sphinx", "_templates", "layout.html")
SCRIPTS_DIR = "scripts"

TOOLKIT_TABLE_RE = re.compile(
    r"\|\s*`scripts/([^`]+)`\s*\|"
)
ADDITIONAL_RES_LINK_RE = re.compile(
    r"\[.+?\]\(([^)]+)\)"
)
COMMAND_TABLE_RE = re.compile(
    r"\|\s*`(/PKB-\S+?)(?:\s|`)"
)
COMMANDS_MD_HEADING_RE = re.compile(
    r"^##\s+(/PKB-\S+)"
)
INIT_COPY_SCRIPT_RE = re.compile(
    r"(\S+\.(?:py|sh))"
)
INIT_COPY_DOC_RE = re.compile(
    r"(\S+\.md)"
)

INTERNAL_HELPERS = {"generated_output.py", "generated_output.sh"}


@dataclass
class Issue:
    category: str
    detail: str


def find_skill_root() -> str:
    """Walk up from this script to find the directory containing SKILL.md."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, SKILL_MD)):
            return d
        d = os.path.dirname(d)
    raise SystemExit("Cannot locate SKILL.md from script directory")


def read_lines(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def check_toolkit_table(skill_lines: List[str], skill_root: str) -> List[Issue]:
    """Every script in the toolkit table must exist on disk."""
    issues: List[Issue] = []
    for line in skill_lines:
        m = TOOLKIT_TABLE_RE.search(line)
        if m:
            script = m.group(1)
            if not os.path.isfile(os.path.join(skill_root, "scripts", script)):
                issues.append(Issue("toolkit_table", f"scripts/{script} listed in toolkit table but not found on disk"))
    return issues


def check_additional_resources(skill_lines: List[str], skill_root: str) -> List[Issue]:
    """Every local link in Additional Resources must resolve."""
    issues: List[Issue] = []
    in_section = False
    for line in skill_lines:
        stripped = line.strip()
        if stripped.startswith("## Additional Resources"):
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section:
            continue
        for target in ADDITIONAL_RES_LINK_RE.findall(line):
            if target.startswith(("http://", "https://", "#")):
                continue
            clean = target.split("#")[0].split("?")[0]
            if not os.path.exists(os.path.join(skill_root, clean)):
                issues.append(Issue("additional_resources", f"link target '{clean}' not found on disk"))
    return issues


def check_command_sync(skill_lines: List[str], commands_lines: List[str]) -> List[Issue]:
    """Commands in SKILL.md table should match commands.md headings."""
    issues: List[Issue] = []

    skill_cmds: set[str] = set()
    for line in skill_lines:
        m = COMMAND_TABLE_RE.search(line)
        if m:
            skill_cmds.add(normalize_cmd(m.group(1)))

    ref_cmds: set[str] = set()
    for line in commands_lines:
        m = COMMANDS_MD_HEADING_RE.match(line.strip())
        if m:
            ref_cmds.add(normalize_cmd(m.group(1)))

    for cmd in sorted(ref_cmds - skill_cmds):
        issues.append(Issue("command_sync", f"{cmd} is in commands.md but missing from SKILL.md command table"))
    for cmd in sorted(skill_cmds - ref_cmds):
        issues.append(Issue("command_sync", f"{cmd} is in SKILL.md command table but missing from commands.md"))

    return issues


def normalize_cmd(raw: str) -> str:
    return raw.split("[")[0].split("<")[0].rstrip()


def check_init_script_coverage(init_lines: List[str], skill_root: str) -> List[Issue]:
    """Scripts on disk should be listed in init_pkb.sh copy loop."""
    issues: List[Issue] = []

    scripts_on_disk = {
        f for f in os.listdir(os.path.join(skill_root, SCRIPTS_DIR))
        if f.endswith((".py", ".sh")) and not f.startswith("__")
    }
    init_text = "".join(init_lines)
    copied_scripts: set[str] = set()
    for name in INIT_COPY_SCRIPT_RE.findall(init_text):
        candidate = os.path.basename(name.strip().strip('"').strip("'").rstrip(";"))
        if candidate in scripts_on_disk:
            copied_scripts.add(candidate)

    skip = INTERNAL_HELPERS | {"validate_skill_consistency.py", "init_pkb.sh"}
    for s in sorted(scripts_on_disk - copied_scripts - skip):
        issues.append(Issue("init_coverage", f"scripts/{s} exists on disk but is not copied by init_pkb.sh"))
    for s in sorted(copied_scripts - scripts_on_disk):
        issues.append(Issue("init_coverage", f"init_pkb.sh copies scripts/{s} but it does not exist on disk"))

    return issues


def check_init_template_docs(init_lines: List[str], skill_root: str) -> List[Issue]:
    """Template docs listed in init_pkb.sh must exist in templates/docs/."""
    issues: List[Issue] = []
    templates_dir = os.path.join(skill_root, "templates", "docs")

    in_doc_loop = False
    for line in init_lines:
        stripped = line.strip()
        if "00-overview.md" in stripped:
            in_doc_loop = True
        if in_doc_loop:
            for m in INIT_COPY_DOC_RE.finditer(stripped):
                doc = m.group(1).rstrip(";")
                if doc.startswith("$") or "/" in doc:
                    continue
                if not os.path.isfile(os.path.join(templates_dir, doc)):
                    issues.append(Issue("init_template_docs", f"init_pkb.sh copies templates/docs/{doc} but it does not exist"))
            if stripped.startswith("done") or (stripped.endswith("; do") and "00-overview" not in stripped):
                break

    return issues


def check_poetry_scaffold(init_lines: List[str], skill_root: str) -> List[Issue]:
    """Poetry-first files and Makefile hooks should exist."""
    issues: List[Issue] = []

    root_pyproject = os.path.join(skill_root, ROOT_PYPROJECT)
    root_makefile = os.path.join(skill_root, ROOT_MAKEFILE)
    template_pyproject = os.path.join(skill_root, TEMPLATE_SPHINX_PYPROJECT)
    template_makefile = os.path.join(skill_root, TEMPLATE_SPHINX_MAKEFILE)
    template_conf = os.path.join(skill_root, TEMPLATE_SPHINX_CONF)
    template_layout = os.path.join(skill_root, TEMPLATE_SPHINX_LAYOUT)

    if not os.path.isfile(root_pyproject):
        issues.append(Issue("poetry_scaffold", f"{ROOT_PYPROJECT} not found"))
    if not os.path.isfile(template_pyproject):
        issues.append(Issue("poetry_scaffold", f"{TEMPLATE_SPHINX_PYPROJECT} not found"))

    if os.path.isfile(root_makefile):
        root_make_lines = "".join(read_lines(root_makefile))
        if "poetry install" not in root_make_lines and "$(POETRY) install" not in root_make_lines:
            issues.append(Issue("poetry_scaffold", "skill Makefile does not expose a Poetry install workflow"))
    else:
        issues.append(Issue("poetry_scaffold", f"{ROOT_MAKEFILE} not found"))

    if os.path.isfile(template_makefile):
        template_make_lines = "".join(read_lines(template_makefile))
        if "poetry install" not in template_make_lines and "$(POETRY) install" not in template_make_lines:
            issues.append(Issue("poetry_scaffold", "templates/sphinx/Makefile does not install via Poetry"))
        for target in ("html-en:", "html-zh:", "html-all:", "gettext:", "intl-update:", "strip-confidential:"):
            if target not in template_make_lines:
                issues.append(Issue("poetry_scaffold", f"templates/sphinx/Makefile is missing target {target.rstrip(':')}"))
    else:
        issues.append(Issue("poetry_scaffold", f"{TEMPLATE_SPHINX_MAKEFILE} not found"))

    if os.path.isfile(template_conf):
        conf_text = "".join(read_lines(template_conf))
        for required in (
            'language = os.environ.get("SPHINX_LANGUAGE", "en")',
            "locale_dirs = ['locale/']",
            "gettext_compact = False",
            "available_languages",
        ):
            if required not in conf_text:
                issues.append(Issue("poetry_scaffold", f"templates/sphinx/conf.py is missing {required!r}"))
    else:
        issues.append(Issue("poetry_scaffold", f"{TEMPLATE_SPHINX_CONF} not found"))

    if not os.path.isfile(template_layout):
        issues.append(Issue("poetry_scaffold", f"{TEMPLATE_SPHINX_LAYOUT} not found"))

    init_text = "".join(init_lines)
    if "pyproject.toml" not in init_text:
        issues.append(Issue("poetry_scaffold", "init_pkb.sh does not mention copying pyproject.toml"))
    if "--bilingual=" not in init_text:
        issues.append(Issue("poetry_scaffold", "init_pkb.sh does not expose --bilingual=<locale>"))

    return issues


def main() -> None:
    skill_root = find_skill_root()
    skill_path = os.path.join(skill_root, SKILL_MD)
    commands_path = os.path.join(skill_root, COMMANDS_MD)
    init_path = os.path.join(skill_root, INIT_SCRIPT)

    skill_lines = read_lines(skill_path)

    all_issues: List[Issue] = []
    all_issues.extend(check_toolkit_table(skill_lines, skill_root))
    all_issues.extend(check_additional_resources(skill_lines, skill_root))

    if os.path.isfile(commands_path):
        all_issues.extend(check_command_sync(skill_lines, read_lines(commands_path)))
    else:
        all_issues.append(Issue("missing_file", f"{COMMANDS_MD} not found"))

    if os.path.isfile(init_path):
        init_lines = read_lines(init_path)
        all_issues.extend(check_init_script_coverage(init_lines, skill_root))
        all_issues.extend(check_init_template_docs(init_lines, skill_root))
        all_issues.extend(check_poetry_scaffold(init_lines, skill_root))
    else:
        all_issues.append(Issue("missing_file", f"{INIT_SCRIPT} not found"))

    if not all_issues:
        print("All consistency checks passed.")
        sys.exit(0)

    print(f"\nSkill Consistency Report — {len(all_issues)} issue(s)\n")
    print(f"{'Category':<24} Detail")
    print("-" * 80)
    for issue in all_issues:
        print(f"{issue.category:<24} {issue.detail}")

    sys.exit(1)


if __name__ == "__main__":
    main()
