#!/usr/bin/env python3
"""
L1: AI Skill structure lint.

Usage:
    python3 lint.py <skill_dir> [--json]

Checks:
  - SKILL.md / skill.md exists
  - YAML frontmatter parses and contains required fields
  - name is kebab-case lowercase (warn)
  - description length in [50, 1024]
  - referenced files under references/, scripts/, assets/ exist
  - no TODO / FIXME / XXX / TBD residues in body (warn)
  - UTF-8 + LF line endings (warn)

Exits 0 on pass (errors == 0), 1 on fail.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML not installed. Run: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# (subdir_name, regex capturing the relative path after the subdir)
REFERENCE_RULES = [
    ("references", re.compile(r"references/([\w\-./]+\.md)")),
    ("scripts", re.compile(r"scripts/([\w\-./]+\.(?:py|sh|js|ts|mjs))")),
    ("assets", re.compile(r"assets/([\w\-./]+)")),
]

BAD_TOKENS = ("TODO", "FIXME", "XXX", "TBD")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*$")


def find_skill_md(skill_dir: Path) -> Path | None:
    for name in ("SKILL.md", "skill.md", "Skill.md"):
        p = skill_dir / name
        if p.exists():
            return p
    return None


def lint(skill_dir: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not skill_dir.is_dir():
        return {
            "passed": False,
            "errors": [f"not a directory: {skill_dir}"],
            "warnings": [],
        }

    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return {
            "passed": False,
            "errors": [f"missing SKILL.md in {skill_dir}"],
            "warnings": [],
        }

    try:
        raw = skill_md.read_bytes()
    except OSError as exc:
        return {
            "passed": False,
            "errors": [f"cannot read {skill_md}: {exc}"],
            "warnings": [],
        }

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return {
            "passed": False,
            "errors": [f"{skill_md.name} is not valid UTF-8: {exc}"],
            "warnings": [],
        }

    if b"\r\n" in raw:
        warnings.append(f"{skill_md.name} uses CRLF line endings (prefer LF)")

    m = FRONTMATTER_RE.match(text)
    fm: dict = {}
    body = text
    if not m:
        errors.append("missing YAML frontmatter (--- ... ---) at top")
    else:
        try:
            parsed = yaml.safe_load(m.group(1))
            if isinstance(parsed, dict):
                fm = parsed
            else:
                errors.append("YAML frontmatter must be a mapping")
        except yaml.YAMLError as exc:
            errors.append(f"YAML frontmatter does not parse: {exc}")
        body = text[m.end():]

    name = str(fm.get("name") or "")
    desc = str(fm.get("description") or "")

    if not name:
        errors.append("frontmatter.name is missing or empty")
    elif not NAME_RE.match(name):
        warnings.append(f"frontmatter.name '{name}' is not kebab-case lowercase")

    if not desc:
        errors.append("frontmatter.description is missing or empty")
    else:
        dlen = len(desc)
        if dlen < 50:
            warnings.append(
                f"description too short ({dlen} chars); agents need context to trigger reliably"
            )
        if dlen > 1024:
            errors.append(
                f"description too long ({dlen} chars); many agents truncate after 1024"
            )

    for subdir, pattern in REFERENCE_RULES:
        seen: set[str] = set()
        for rel in pattern.findall(body):
            if rel in seen:
                continue
            seen.add(rel)
            target = skill_dir / subdir / rel
            if not target.exists():
                errors.append(f"broken reference: {subdir}/{rel} not found")

    stripped_body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    stripped_body = re.sub(r"`[^`\n]+`", "", stripped_body)
    for token in BAD_TOKENS:
        if re.search(rf"(?<![A-Za-z_`]){token}(?![A-Za-z_`])", stripped_body):
            warnings.append(f"body contains '{token}' marker; resolve before release")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "meta": {
            "skill_md": str(skill_md),
            "name": name,
            "description_length": len(desc),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L1 structure lint for an AI skill")
    parser.add_argument("skill_dir", help="path to the skill directory")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    result = lint(Path(args.skill_dir).resolve())

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[L1 lint] {status} ({args.skill_dir})")
        for e in result["errors"]:
            print(f"  ERROR  {e}")
        for w in result["warnings"]:
            print(f"  WARN   {w}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
