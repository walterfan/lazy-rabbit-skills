#!/usr/bin/env python3
"""
Package a skill directory into a distributable .skill archive (ZIP format).

Validates the skill structure, excludes non-essential files, and creates
a ZIP archive ready for sharing or publishing.

Usage:
    python package_skill.py <skill-directory> [output-directory]
"""

import sys
import zipfile
from pathlib import Path

EXCLUDE_PATTERNS = {
    "__pycache__",
    "node_modules",
    ".git",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "evals",
    ".env",
}


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from the package."""
    for part in path.parts:
        if part in EXCLUDE_PATTERNS:
            return True
        for pattern in EXCLUDE_PATTERNS:
            if pattern.startswith("*") and part.endswith(pattern[1:]):
                return True
    return False


def validate_skill_dir(skill_dir: Path) -> str:
    """Validate skill directory and return the skill name."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError("SKILL.md missing frontmatter")

    # Extract name
    import re
    match = re.search(r"^name:\s*(.+)", content, re.MULTILINE)
    if not match:
        raise ValueError("SKILL.md frontmatter missing 'name' field")

    return match.group(1).strip()


def package_skill(skill_dir: Path, output_dir: Path) -> Path:
    """Create a .skill archive from the skill directory."""
    name = validate_skill_dir(skill_dir)
    output_path = output_dir / f"{name}.skill"

    file_count = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(skill_dir.rglob("*")):
            if file_path.is_dir():
                continue
            relative = file_path.relative_to(skill_dir)
            if should_exclude(relative):
                continue
            zf.write(file_path, arcname=str(relative))
            file_count += 1

    print(f"Packaged {file_count} files into {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <skill-directory> [output-directory]")
        sys.exit(1)

    skill_dir = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()

    if not skill_dir.is_dir():
        print(f"Error: {skill_dir} is not a directory")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        output_path = package_skill(skill_dir, output_dir)
        print(f"Success: {output_path}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
