#!/usr/bin/env python3
"""
Validate a SKILL.md file against the CEVF framework.

Checks:
- Frontmatter structure and required fields
- CEVF layer presence (Contract, Execution, Verification, Feedback)
- Description quality heuristics
- Line count limit

Usage:
    python validate_skill.py <path-to-SKILL.md>
    python validate_skill.py <path-to-skill-directory>
"""

import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and body from SKILL.md content."""
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    frontmatter_text = content[3:end].strip()
    body = content[end + 3:].strip()

    # Simple key-value extraction (not full YAML parsing)
    frontmatter = {}
    current_key = None
    current_value_lines = []

    for line in frontmatter_text.split("\n"):
        match = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if match:
            if current_key:
                frontmatter[current_key] = "\n".join(current_value_lines).strip()
            current_key = match.group(1)
            current_value_lines = [match.group(2)]
        elif current_key and (line.startswith("  ") or line.startswith("\t")):
            current_value_lines.append(line.strip())

    if current_key:
        frontmatter[current_key] = "\n".join(current_value_lines).strip()

    return frontmatter, body


def validate_frontmatter(frontmatter: dict[str, str]) -> list[str]:
    """Check required frontmatter fields."""
    errors = []
    required = ["name", "description", "version", "author"]
    recommended = ["tags", "category", "platforms", "visibility"]

    for field in required:
        if field not in frontmatter:
            errors.append(f"FAIL: Missing required frontmatter field: {field}")

    for field in recommended:
        if field not in frontmatter:
            errors.append(f"WARN: Missing recommended frontmatter field: {field}")

    # Name format check
    name = frontmatter.get("name", "")
    if name and not re.match(r"^[a-z][a-z0-9-]*$", name):
        errors.append(f"FAIL: Skill name '{name}' should be kebab-case (lowercase, hyphens only)")
    if name and len(name) > 64:
        errors.append(f"FAIL: Skill name exceeds 64 characters ({len(name)})")

    # Description length
    desc = frontmatter.get("description", "")
    if desc and len(desc) > 1024:
        errors.append(f"WARN: Description exceeds 1024 characters ({len(desc)})")

    return errors


def validate_description_quality(frontmatter: dict[str, str]) -> list[str]:
    """Heuristic checks on description trigger quality."""
    errors = []
    desc = frontmatter.get("description", "").lower()

    if not desc:
        errors.append("FAIL: Description is empty")
        return errors

    # Third person check (rough heuristic)
    first_person = ["i can", "i will", "i help", "i'll"]
    for phrase in first_person:
        if phrase in desc:
            errors.append(f"WARN: Description uses first person ('{phrase}'). Use third person instead")
            break

    # WHAT + WHEN check
    when_keywords = ["use when", "use this", "trigger", "whenever", "even if", "even when", "make sure"]
    has_when = any(kw in desc for kw in when_keywords)
    if not has_when:
        errors.append("WARN: Description may lack WHEN trigger guidance. Consider adding 'Use when...' or 'Make sure to use this when...'")

    # Assertiveness check
    passive_phrases = ["can be used", "may help", "might be useful", "use if relevant", "use when relevant"]
    for phrase in passive_phrases:
        if phrase in desc:
            errors.append(f"WARN: Description is too passive ('{phrase}'). Be more assertive about when to trigger")
            break

    return errors


def validate_cevf_layers(body: str) -> list[str]:
    """Check for CEVF layer presence in the body."""
    errors = []
    headings = re.findall(r"^#{1,3}\s+(.+)", body, re.MULTILINE)
    headings_lower = [h.lower().strip() for h in headings]
    all_text_lower = body.lower()

    # Contract layer
    contract_keywords = ["contract", "scope_in", "scope_out", "precondition", "postcondition"]
    has_contract = any(kw in all_text_lower for kw in contract_keywords)
    if not has_contract:
        errors.append("FAIL [Contract]: No contract layer found. Define scope_in, scope_out, preconditions, postconditions")

    # Check specific contract elements
    if has_contract:
        if "scope_in" not in all_text_lower:
            errors.append("WARN [Contract]: scope_in not explicitly defined")
        if "scope_out" not in all_text_lower:
            errors.append("WARN [Contract]: scope_out not explicitly defined")
        if "precondition" not in all_text_lower:
            errors.append("WARN [Contract]: Preconditions not explicitly defined")
        if "postcondition" not in all_text_lower:
            errors.append("WARN [Contract]: Postconditions not explicitly defined")

    # Execution layer
    execution_keywords = ["execution", "phase", "step", "workflow"]
    has_execution = any(kw in all_text_lower for kw in execution_keywords)
    if not has_execution:
        errors.append("FAIL [Execution]: No execution layer found. Define phases with entry/exit criteria")

    # Check for failure handling in execution
    failure_keywords = ["on fail", "rollback", "degrad", "fall back", "fallback", "if fail"]
    has_failure_path = any(kw in all_text_lower for kw in failure_keywords)
    if has_execution and not has_failure_path:
        errors.append("WARN [Execution]: No failure/rollback path found in execution phases")

    # Verification layer
    verification_keywords = ["verification", "hard gate", "soft gate", "quality gate", "assert", "check"]
    has_verification = any(kw in all_text_lower for kw in verification_keywords)
    if not has_verification:
        errors.append("FAIL [Verification]: No verification layer found. Define hard gates with pass/fail thresholds")

    # Feedback layer
    feedback_keywords = ["feedback", "failure mode", "boundary example", "improvement trigger"]
    has_feedback = any(kw in all_text_lower for kw in feedback_keywords)
    if not has_feedback:
        errors.append("FAIL [Feedback]: No feedback layer found. Document failure modes and improvement triggers")

    return errors


def validate_line_count(content: str) -> list[str]:
    """Check SKILL.md stays under 500 lines."""
    errors = []
    line_count = content.count("\n") + 1
    if line_count > 500:
        errors.append(f"WARN: SKILL.md is {line_count} lines (recommended max: 500). Consider using progressive disclosure")
    return errors


def validate_skill(path: Path) -> list[str]:
    """Run all validations on a SKILL.md file."""
    if path.is_dir():
        path = path / "SKILL.md"

    if not path.exists():
        return [f"FAIL: File not found: {path}"]

    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    errors = []
    errors.extend(validate_frontmatter(frontmatter))
    errors.extend(validate_description_quality(frontmatter))
    errors.extend(validate_cevf_layers(body))
    errors.extend(validate_line_count(content))

    return errors


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-SKILL.md-or-directory>")
        sys.exit(1)

    path = Path(sys.argv[1])
    errors = validate_skill(path)

    if not errors:
        print("PASS: All CEVF checks passed")
        sys.exit(0)

    fails = [e for e in errors if e.startswith("FAIL")]
    warns = [e for e in errors if e.startswith("WARN")]

    for error in errors:
        print(error)

    print(f"\n--- Summary: {len(fails)} error(s), {len(warns)} warning(s) ---")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
