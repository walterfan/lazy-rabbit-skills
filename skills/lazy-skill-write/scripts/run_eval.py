#!/usr/bin/env python3
"""
Run evaluation cases against a skill to test trigger behavior and output quality.

Reads evals.json from the skill directory and tests each case by running
the skill description through a simulated trigger check.

Usage:
    python run_eval.py <path-to-skill-directory>
    python run_eval.py <path-to-skill-directory> --verbose
"""

import json
import re
import sys
from pathlib import Path


def parse_skill_description(skill_dir: Path) -> tuple[str, str]:
    """Extract name and description from SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError("SKILL.md missing frontmatter")

    end = content.find("---", 3)
    frontmatter = content[3:end]

    name = ""
    description_lines = []
    in_description = False

    for line in frontmatter.split("\n"):
        name_match = re.match(r"^name:\s*(.+)", line)
        if name_match:
            name = name_match.group(1).strip()
            continue

        desc_match = re.match(r"^description:\s*(.*)", line)
        if desc_match:
            in_description = True
            val = desc_match.group(1).strip()
            if val and val not in (">-", ">", "|", "|-"):
                description_lines.append(val)
            continue

        if in_description and (line.startswith("  ") or line.startswith("\t")):
            description_lines.append(line.strip())
        elif in_description:
            in_description = False

    description = " ".join(description_lines).strip()
    return name, description


def load_evals(skill_dir: Path) -> dict:
    """Load evals.json from skill directory."""
    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.exists():
        raise FileNotFoundError(
            f"evals/evals.json not found in {skill_dir}. "
            "Copy templates/evals_template.json to <skill>/evals/evals.json and fill it in."
        )
    return json.loads(evals_path.read_text(encoding="utf-8"))


def check_trigger(description: str, prompt: str) -> bool:
    """
    Heuristic check: would this skill description trigger for the given prompt?

    This is a keyword-overlap heuristic, not a full LLM simulation.
    For real trigger testing, use `claude -p` with the skill loaded.
    """
    desc_lower = description.lower()
    prompt_lower = prompt.lower()

    # Extract significant words (3+ chars, not stopwords)
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "are", "was",
        "been", "have", "has", "had", "will", "would", "could", "should",
        "can", "may", "use", "when", "how", "what", "who", "which", "not",
        "but", "also", "into", "about", "than", "then", "just", "even",
        "more", "most", "some", "any", "all", "each", "every", "your",
        "their", "our", "its", "does", "did", "don", "isn", "doesn",
    }

    def extract_words(text):
        words = re.findall(r"[a-z][a-z0-9_-]{2,}", text)
        return {w for w in words if w not in stopwords}

    desc_words = extract_words(desc_lower)
    prompt_words = extract_words(prompt_lower)

    overlap = desc_words & prompt_words
    overlap_ratio = len(overlap) / max(len(prompt_words), 1)

    # Trigger if there's meaningful keyword overlap
    return overlap_ratio >= 0.15 or len(overlap) >= 2


def run_eval(skill_dir: Path, verbose: bool = False) -> dict:
    """Run all eval cases and return results."""
    name, description = parse_skill_description(skill_dir)
    evals_data = load_evals(skill_dir)
    results = []

    for case in evals_data.get("evals", []):
        case_id = case["id"]
        case_type = case.get("type", "should_trigger")
        prompt = case["prompt"]

        triggered = check_trigger(description, prompt)

        if case_type == "should_trigger":
            passed = triggered
        elif case_type == "should_not_trigger":
            passed = not triggered
        else:
            # boundary and verification cases — just check if trigger is reasonable
            passed = triggered

        result = {
            "id": case_id,
            "type": case_type,
            "prompt": prompt,
            "triggered": triggered,
            "passed": passed,
        }
        results.append(result)

        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {case_id}: triggered={triggered} (type={case_type})")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    pass_rate = passed / total if total > 0 else 0

    return {
        "skill": name,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(pass_rate, 3),
        "results": results,
    }


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-skill-directory> [--verbose]")
        sys.exit(1)

    skill_dir = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv

    if not skill_dir.is_dir():
        print(f"Error: {skill_dir} is not a directory")
        sys.exit(1)

    try:
        results = run_eval(skill_dir, verbose=verbose)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"\n--- Eval Results for '{results['skill']}' ---")
    print(f"Total: {results['total']}  Passed: {results['passed']}  Failed: {results['failed']}  Rate: {results['pass_rate']:.1%}")

    if results["failed"] > 0:
        print("\nFailed cases:")
        for r in results["results"]:
            if not r["passed"]:
                print(f"  - {r['id']} ({r['type']}): \"{r['prompt'][:80]}...\"")

    # Write results to JSON
    output_path = skill_dir / "evals" / "eval_results.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults written to {output_path}")

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
